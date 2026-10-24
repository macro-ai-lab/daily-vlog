"""Use wheels for both encoding and probing: no Homebrew or ffprobe prerequisite."""
from pathlib import Path
import subprocess
import av
import imageio_ffmpeg


def ffmpeg_path():
    # Use only the wheel binary, without a PATH or environment override.
    import platform
    from imageio_ffmpeg._definitions import FNAME_PER_PLATFORM
    system, machine = platform.system(), platform.machine().lower()
    if system == 'Darwin':
        key = 'macos-aarch64' if machine in ('arm64', 'aarch64') else 'macos-x86_64'
    elif system == 'Windows' and machine in ('amd64', 'x86_64'):
        key = 'windows-x86_64'
    else:
        raise RuntimeError('현재 지원 대상은 macOS와 Windows x64입니다. Windows ARM은 아직 지원하지 않습니다.')
    name = FNAME_PER_PLATFORM.get(key)
    path = Path(imageio_ffmpeg.__file__).parent / 'binaries' / str(name)
    if not name or not path.is_file():
        raise RuntimeError('전용 FFmpeg를 찾을 수 없습니다. 설치를 다시 확인하세요.')
    return str(path)


def default_font():
    font = Path(__file__).resolve().parents[1] / 'assets/fonts/NotoSansKR-Regular.otf'
    if not font.is_file():
        raise RuntimeError('기본 Noto Sans KR 번들 폰트가 없습니다. 스킬 배포 파일을 확인하세요.')
    return font


def probe(path):
    with av.open(str(path)) as container:
        streams = []
        for stream in container.streams:
            codec = stream.codec_context
            item = {'codec_type': stream.type, 'codec_name': codec.name if codec is not None else None,
                    'index': stream.index, 'metadata': dict(stream.metadata)}
            if stream.duration is not None and stream.time_base is not None:
                item['duration'] = str(float(stream.duration * stream.time_base))
            if stream.type == 'video':
                item.update(width=codec.width, height=codec.height, nb_frames=stream.frames,
                            pix_fmt=codec.format.name if codec.format else None,
                            avg_frame_rate=str(stream.average_rate or '0/1'),
                            color_trc=int(codec.color_trc), color_primaries=int(codec.color_primaries),
                            colorspace=int(codec.colorspace))
                # Rotation lives on decoded VideoFrame, not VideoStream.
                with av.open(str(path)) as rotation_source:
                    frame = next(rotation_source.decode(rotation_source.streams[stream.index]), None)
                    if frame is None:
                        raise ValueError('디코딩 가능한 영상 프레임이 없습니다.')
                    item['rotation'] = frame.rotation
                    item['display_matrix'] = any('DISPLAYMATRIX' in str(sd) for sd in frame.side_data)
            elif stream.type == 'audio':
                item.update(sample_rate=codec.sample_rate, channels=codec.channels)
            streams.append(item)
        duration = container.duration / av.time_base if container.duration is not None else max(
            (float(s.get('duration', 0)) for s in streams), default=0)
        return {'format': {'duration': str(duration), 'format_name': container.format.name,
                           'metadata': dict(container.metadata)}, 'streams': streams}
