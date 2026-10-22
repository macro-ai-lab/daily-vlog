"""Agent-facing CLI; novice users give a folder and a natural-language request."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from PIL import ImageFont
from media_runtime import default_font, ffmpeg_path, probe


def doctor():
    font = default_font()
    ImageFont.truetype(str(font), 53)
    ffmpeg = ffmpeg_path()
    result = subprocess.run([ffmpeg, '-hide_banner', '-version'], check=True, capture_output=True, text=True)
    enc = subprocess.run([ffmpeg, '-hide_banner', '-encoders'], check=True, capture_output=True, text=True)
    if 'libx264' not in enc.stdout or ' aac ' not in enc.stdout:
        raise RuntimeError('필수 H.264/AAC 인코더를 찾지 못했습니다.')
    return {'status': 'ready', 'python': sys.version.split()[0],
            'packages': {n: importlib.metadata.version(n) for n in ['pillow', 'av', 'imageio-ffmpeg']},
            'ffmpeg': result.stdout.splitlines()[0], 'font': str(font),
            'media_upload': False, 'support': 'macOS / Windows x64 candidate; silent H.264 MP4; separate licensed BGM'}


def inspect(folder=None, files=None):
    if bool(folder) == bool(files):
        raise ValueError('영상 폴더 하나 또는 첨부 영상 파일 경로 목록 중 하나를 지정하세요.')
    if files:
        # Inspect only the supplied attachments, never their shared parent folder.
        paths = [Path(x).expanduser().resolve() for x in files]
        files = list(dict.fromkeys(paths))
        p = None
    else:
        p = Path(folder).expanduser().resolve()
        if not p.is_dir():
            raise ValueError('영상 폴더를 찾을 수 없습니다. 영상 파일을 직접 첨부하거나 폴더 위치를 알려주세요.')
        files = sorted(x for x in p.iterdir() if x.is_file() and x.suffix.lower() in {'.mp4', '.mov', '.m4v', '.mkv'})
    if len(files) > 200:
        raise ValueError('영상이 200개보다 많습니다. 이번에 쓸 영상 200개 이하를 선택해 첨부하거나 별도 폴더로 지정해 주세요.')
    items = []
    for f in files:
        try:
            if not f.is_file():
                raise ValueError('첨부 영상 파일에 접근할 수 없습니다. 해당 파일을 다시 첨부하거나 접근 가능한 위치를 알려주세요.')
            info = probe(f)
            vids = [s for s in info['streams'] if s['codec_type'] == 'video']
            audio = any(s['codec_type'] == 'audio' for s in info['streams'])
            reason = []
            if not vids or any(s['codec_name'] != 'h264' for s in vids):
                reason.append('현재 지원 범위는 H.264 영상입니다. 변환이 필요한 파일입니다.')
            if audio:
                reason.append('원음이 있어 자동 편집 대상에서 제외했습니다. 임의로 소리를 지우지 않습니다.')
            for s in vids:
                if s.get('color_trc') in (16, 18):
                    reason.append('HDR 영상입니다. SDR 변환 검증이 먼저 필요합니다.')
                if s.get('display_matrix') or s.get('rotation') not in (None, 0) or s.get('metadata', {}).get('rotate', '0') != '0':
                    reason.append('회전 정보가 있습니다. 방향 확인·정규화가 먼저 필요합니다.')
            items.append({'file': str(f), 'eligible': not reason, 'reasons': reason, 'probe': info})
        except Exception as exc:
            items.append({'file': str(f), 'eligible': False, 'reasons': [str(exc)]})
    return {'folder': str(p) if p is not None else None, 'input_mode': 'folder' if p is not None else 'files', 'files': items, 'count': len(items),
            'note': '파일명·수정 시각은 실제 촬영 시각의 증거가 아닙니다. 이 검사는 장면 선택을 대신하지 않습니다.'}


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='command', required=True)
    sp.add_parser('doctor')
    smoke = sp.add_parser('smoke'); smoke.add_argument('--output-dir', required=True)
    i = sp.add_parser('inspect'); i.add_argument('folder', nargs='?'); i.add_argument('--files', nargs='+')
    f = sp.add_parser('frames'); f.add_argument('file'); f.add_argument('--output-dir', required=True)
    s = sp.add_parser('survey'); s.add_argument('file'); s.add_argument('--output-dir', required=True)
    s.add_argument('--start', type=float, default=0); s.add_argument('--end', type=float)
    s.add_argument('--interval', type=float, default=30); s.add_argument('--max-frames', type=int, default=60)
    c = sp.add_parser('customize'); c.add_argument('plan'); c.add_argument('--patch', required=True)
    c.add_argument('--output', required=True); c.add_argument('--root', default='.')
    fnt = sp.add_parser('font'); fnt.add_argument('--name', required=True); fnt.add_argument('--output-dir', required=True)
    ov = sp.add_parser('overrides'); ovsp = ov.add_subparsers(dest='action', required=True)
    show = ovsp.add_parser('show'); show.add_argument('--store')
    proposal = ovsp.add_parser('propose'); proposal.add_argument('--patch', required=True)
    proposal.add_argument('--request', required=True); proposal.add_argument('--output', required=True); proposal.add_argument('--store')
    approve = ovsp.add_parser('save'); approve.add_argument('proposal'); approve.add_argument('--proposal-id', required=True)
    approve.add_argument('--approval', required=True)
    r = sp.add_parser('render', add_help=False); r.add_argument('arguments', nargs=argparse.REMAINDER)
    if len(sys.argv) > 1 and sys.argv[1] == 'render':
        args = sys.argv[2:]
        if '--shared-lock' not in args:
            lock = Path(os.environ['DAILY_VLOG_RUNTIME']) / 'render.lock'
            if not lock.exists():
                lock.touch(exist_ok=False)
            args += ['--shared-lock', str(lock)]
        # Check source eligibility even if an agent skips inspect.
        rp = argparse.ArgumentParser(add_help=False)
        rp.add_argument('plan'); rp.add_argument('--root', default='.')
        known, _ = rp.parse_known_args(args)
        root = Path(known.root).expanduser().resolve()
        plan = json.loads((root / known.plan).read_text())
        sources = {str((root / s['source']).resolve()) for s in plan['shots']}
        for source in sources:
            info = probe(source)
            vids = [s for s in info['streams'] if s['codec_type'] == 'video']
            if not vids or any(s['codec_name'] != 'h264' or s.get('color_trc') in (16,18)
                               or s.get('display_matrix') or s.get('rotation') not in (None,0)
                               or s.get('metadata',{}).get('rotate','0') != '0' for s in vids):
                raise ValueError('지원 범위 밖의 코덱·HDR·회전 정보가 있습니다. inspect로 확인하세요.')
        sys.argv = ['render.py', *args]
        import render
        render.main()
        return
    a = p.parse_args()
    if a.command == 'doctor': result = doctor()
    elif a.command == 'smoke':
        from installation_check import check
        result = check(a.output_dir)
    elif a.command == 'inspect': result = inspect(a.folder, a.files)
    elif a.command == 'survey':
        from survey import survey
        result = survey(a.file, a.output_dir, a.start, a.end, a.interval, a.max_frames)
    elif a.command == 'customize':
        from customize import customize
        result = customize(a.plan, a.patch, a.output, a.root)
    elif a.command == 'font':
        from fonts import fetch_font
        result = fetch_font(a.name, a.output_dir)
    elif a.command == 'overrides':
        from overrides import default_store_path, load_profile, propose, save
        if a.action == 'show':
            result = {'store': str(Path(a.store) if a.store else default_store_path()),
                      'profile': load_profile(a.store)}
        elif a.action == 'propose':
            result = propose(a.patch, a.request, a.output, a.store)
        else:
            result = save(a.proposal, a.proposal_id, a.approval)
    elif a.command == 'frames':
        info = probe(a.file); duration = float(info['format']['duration'])
        output = Path(a.output_dir).expanduser(); output.mkdir(parents=True, exist_ok=False)
        result = []
        for n, ratio in enumerate([.1,.5,.9]):
            image = output / f'frame-{n+1}.jpg'
            subprocess.run([ffmpeg_path(),'-hide_banner','-nostdin','-v','error','-ss',str(duration*ratio),
                            '-i',str(Path(a.file).expanduser()),'-frames:v','1',str(image)],check=True)
            result.append(str(image.resolve()))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try: main()
    except BlockingIOError:
        print('다른 영상 작업이 실행 중입니다. 기존 작업을 중단하지 말고 완료 후 다시 실행하세요.',file=sys.stderr); sys.exit(3)
    except Exception as exc:
        print(f'브이로그 작업을 완료하지 못했습니다: {exc}',file=sys.stderr);sys.exit(1)
