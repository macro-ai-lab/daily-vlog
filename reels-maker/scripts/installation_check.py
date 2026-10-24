"""Check local video I/O without touching user footage or requiring an AI model."""
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

from media_runtime import default_font, ffmpeg_path, probe


def check(output_dir):
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'running', 'stage': 'encode', 'output_dir': str(output),
              'agent_image_view': 'not_checked', 'user_footage_used': False}
    try:
        source = output / '설치 확인 sample.mp4'
        subprocess.run([ffmpeg_path(), '-hide_banner', '-nostdin', '-v', 'error',
                        '-f', 'lavfi', '-i', 'color=c=0x32526c:s=160x284:r=24:d=1',
                        '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)],
                       check=True, capture_output=True, text=True, timeout=60)
        report['stage'] = 'decode'
        report['probe'] = probe(source)
        report['stage'] = 'extract_frames'
        frames = subprocess.run([sys.executable, str(Path(__file__).with_name('vlog.py')),
                                 'frames', str(source), '--output-dir', str(output / 'frames')],
                                check=True, capture_output=True, text=True, timeout=60)
        report['frames'] = json.loads(frames.stdout)
        if len(report['frames']) != 3:
            raise ValueError('테스트 프레임 3장을 확인하지 못했습니다.')
        report['stage'] = 'image_and_font'
        for path in report['frames']:
            with Image.open(path) as image:
                image.load()
                if image.size != (160, 284):
                    raise ValueError('테스트 이미지 크기가 예상과 다릅니다.')
        preview = output / '설치 확인.png'
        image = Image.new('RGB', (480, 160), '#32526c')
        font = ImageFont.truetype(str(default_font()), 40)
        ImageDraw.Draw(image).text((24, 40), '영상 읽기 확인', font=font, fill='white')
        image.save(preview)
        report.update(status='passed', stage='complete', preview=str(preview))
        return report
    except Exception as exc:
        report.update(status='failed', error=str(exc))
        if isinstance(exc, subprocess.CalledProcessError):
            report['exit_code'] = exc.returncode
            report['stderr'] = (exc.stderr or '')[-8000:]
        raise
    finally:
        (output / 'installation-check.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
