"""Bounded, timestamped visual sampling; editorial choices remain with the agent."""
import json
import math
from fractions import Fraction
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps
from media_runtime import ffmpeg_path, probe


def sample_times(duration, start=0, end=None, interval=30, max_frames=60, tail_margin=.1):
    values = [duration, start, interval, tail_margin] + ([] if end is None else [end])
    if not all(math.isfinite(x) for x in values):
        raise ValueError('영상 길이와 구간·간격은 유한한 숫자여야 합니다.')
    end = duration if end is None else end
    if not 0 <= start < end <= duration or interval <= 0 or not 2 <= max_frames <= 120:
        raise ValueError('구간은 영상 범위 안에, 간격은 0보다 크게, 프레임 수는 2~120으로 지정하세요.')
    # Reserve at least one frame: duration can extend past the final frame.
    last = max(start, end - min(tail_margin, (end - start) / 2))
    count = min(max_frames, max(2, math.ceil((last - start) / interval) + 1))
    return [start + (last - start) * i / (count - 1) for i in range(count)]


def timestamp(seconds):
    total_ms = round(seconds * 1000)
    minutes, ms = divmod(total_ms, 60000)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:02}:{minutes:02}:{ms / 1000:06.3f}'


def survey(file, output_dir, start=0, end=None, interval=30, max_frames=60):
    source = Path(file).expanduser().resolve()
    info = probe(source)
    video = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
    if video is None:
        raise ValueError('영상 스트림이 없습니다.')
    duration = float(video.get('duration', info['format']['duration']))
    fps = float(Fraction(video.get('avg_frame_rate', '0/1')))
    margin = max(.1, 1.1 / fps) if fps > 0 else 1
    times = sample_times(duration, start, end, interval, max_frames, margin)
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    stat = source.stat()
    result = {
        'source': str(source), 'source_size_bytes': stat.st_size,
        'duration_seconds': duration, 'range_seconds': [start, duration if end is None else end],
        'requested_interval_seconds': interval,
        'actual_interval_seconds': times[1] - times[0],
        'frames': [], 'contact_sheets': [],
        'note': '시각은 원본 내 위치이며 촬영시각이 아닙니다. 간격 샘플이라 짧은 행동은 빠질 수 있습니다. 후보 구간은 더 촘촘하게 확인하세요. 오디오·전체 움직임은 검수하지 않았습니다.',
    }
    # Each sheet contains 20 tiles. Keep both per-frame images and original offsets.
    font = ImageFont.load_default(size=18)
    try:
        for index, seconds in enumerate(times):
            frame_path = output / f'frame-{index + 1:03}.jpg'
            subprocess.run([
                ffmpeg_path(), '-hide_banner', '-nostdin', '-v', 'error',
                '-threads', '1', '-ss', str(seconds), '-i', str(source),
                '-map', '0:v:0', '-an', '-frames:v', '1', '-vf',
                'scale=640:640:force_original_aspect_ratio=decrease',
                '-threads', '1', str(frame_path),
            ], check=True, timeout=120, capture_output=True)
            if not frame_path.is_file():
                raise ValueError(f'{timestamp(seconds)}에서 프레임을 읽지 못했습니다.')
            result['frames'].append({'seconds': seconds, 'position': timestamp(seconds), 'path': str(frame_path)})
        for offset in range(0, len(times), 20):
            frames = result['frames'][offset:offset + 20]
            sheet = Image.new('RGB', (4 * 320, math.ceil(len(frames) / 4) * 212), '#202020')
            draw = ImageDraw.Draw(sheet)
            for tile, frame in enumerate(frames):
                x, y = (tile % 4) * 320, (tile // 4) * 212
                with Image.open(frame['path']) as image:
                    thumb = ImageOps.contain(image.convert('RGB'), (320, 180))
                    sheet.paste(thumb, (x + (320 - thumb.width) // 2, y + (180 - thumb.height) // 2))
                draw.text((x + 8, y + 186), frame['position'], font=font, fill='white')
            sheet_path = output / f'contact-{offset // 20 + 1:02}.jpg'
            sheet.save(sheet_path, quality=88)
            result['contact_sheets'].append(str(sheet_path))
        if source.stat().st_size != stat.st_size or source.stat().st_mtime_ns != stat.st_mtime_ns:
            raise ValueError('분석 중 원본이 바뀌었습니다. 안정된 로컬 사본으로 다시 확인하세요.')
        result['status'] = 'sampled_not_editorially_selected'
    except Exception as exc:
        result['status'] = 'incomplete'
        result['error'] = str(exc)
        raise
    finally:
        (output / 'survey.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result
