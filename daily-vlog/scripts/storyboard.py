"""Optional actual-frame style preview; illustrated storyboards use the session image tool."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont
from media_runtime import default_font, ffmpeg_path, probe
from render import prepare_plan, overlay_png, shot_base_filter


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def guide_image(clean):
    """Illustrative UI margins, never an official Instagram specification."""
    image = clean.convert('RGBA')
    guide = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(guide)
    # Conservative review hints. Do not move user-fixed overlays to fit these.
    for box in ((0, 0, 1080, 240), (0, 1520, 1080, 1920), (900, 240, 1080, 1520)):
        draw.rectangle(box, fill=(215, 71, 78, 42))
    draw.rectangle((80, 240, 900, 1520), outline=(255, 215, 105, 210), width=3)
    draw.line((540, 240, 540, 1520), fill=(255, 215, 105, 170), width=2)
    label_font = ImageFont.truetype(str(default_font()), 26)
    draw.text((28, 28), '배치 검토용 · UI 영역은 예시', font=label_font,
              fill='white', stroke_width=1, stroke_fill='black')
    return Image.alpha_composite(image, guide).convert('RGB')


def contact_sheet(directory, shots, page, total_pages, guided=False):
    width, height = 1140, 1640
    sheet = Image.new('RGB', (width, height), '#F2F0EB')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(default_font()), 28)
    small = ImageFont.truetype(str(default_font()), 21)
    label = '배치 검토용 · 색 영역은 UI 회피 참고' if guided else '이미지 콘티 · 실제 원본 프레임'
    draw.text((20, 18), f'{label}   {page}/{total_pages}', font=font, fill='#222B32')
    draw.text((20, 62), '정지 시안입니다. 동작·전환·음악은 영상 미리보기에서 확인합니다.', font=small, fill='#56616B')
    for i, shot in enumerate(shots):
        x, y = 20 + (i % 3) * 375, 112 + (i // 3) * 740
        filename = shot['guide_image'] if guided else shot['image']
        with Image.open(directory / filename) as frame:
            sheet.paste(frame.resize((360, 640), Image.Resampling.LANCZOS), (x, y))
        draw.text((x, y + 648), f"{shot['shot']:02d}  ·  {shot['duration']:g}초", font=font, fill='#222B32')
        draw.text((x, y + 689), f"원본 {shot['source_time_seconds']:.3f}초", font=small, fill='#56616B')
    return sheet


def storyboard(plan_file, output_dir, root='.'):
    root = Path(root).expanduser().resolve()
    plan_path = (root / Path(plan_file).expanduser()).resolve()
    output = (root / Path(output_dir).expanduser()).resolve()
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite: {output}')
    prepared = prepare_plan(plan_path, root)
    plan, shots = prepared['plan'], prepared['shots']
    resolve = lambda v: (root / v).resolve()
    for path in prepared['inputs']:
        if not path.is_file():
            raise FileNotFoundError(path)
    plan_hash = sha256(plan_path)
    effective_hash = hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    fonts = [{'path': str(p), 'sha256': sha256(p)} for p in sorted(prepared['fonts'])]
    source_info = {}
    for shot in shots:
        source = resolve(shot['source'])
        if str(source) not in source_info:
            info = probe(source)
            video = [s for s in info['streams'] if s['codec_type'] == 'video']
            if (not video or any(s['codec_name'] != 'h264' or s.get('color_trc') in (16, 18)
                                or s.get('display_matrix') or s.get('rotation') not in (None, 0)
                                or s.get('metadata', {}).get('rotate', '0') != '0' for s in video)):
                raise ValueError('Unsupported codec/HDR/rotation; inspect the source first')
            if any(s['codec_type'] == 'audio' for s in info['streams']):
                raise ValueError('원음이 있는 영상은 현재 편집 지원 범위 밖입니다. 원음 처리 방식을 먼저 정하세요.')
            stat = source.stat()
            source_info[str(source)] = {'duration': float(info['format']['duration']),
                                        'size': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
        if shot['start'] + shot['duration'] > source_info[str(source)]['duration'] + 1e-6:
            raise ValueError('Shot trim exceeds source duration')
    music = prepared['music']
    if music is not None:
        duration = float(probe(resolve(music['source']))['format']['duration'])
        if music.get('start', 0) + prepared['total'] > duration:
            raise ValueError('Music shorter than requested range')
    # Generate inside our own new directory. Existing results are never replaced.
    output.mkdir(parents=True, exist_ok=False)
    records = []
    ffmpeg = ffmpeg_path()
    with tempfile.TemporaryDirectory(prefix='stills-', dir=output) as temporary:
        temp = Path(temporary)
        for i, shot in enumerate(shots, 1):
            overlay = temp / 'overlay.png'
            bounds = overlay_png(overlay, shot['caption'], prepared['font'], prepared['style'],
                                 shot.get('time_label'), prepared['timeline_mode'],
                                 prepared['timeline_layout'], shot.get('timeline_offset_y', 0),
                                 plan.get('timeline_time_font_size'), prepared['disclosure'],
                                 prepared['overlays'][i - 1])
            # Select a frame after the same fps/crop/composition graph as MP4.
            frame_index = round(shot['duration'] * 24) // 2
            graph = (f'[0:v]{shot_base_filter(shot)}[base];'
                     '[base][1:v]overlay=0:0:format=auto,format=yuv420p,'
                     f'select=eq(n\\,{frame_index})[v]')
            clean_name, guide_name = f'shot-{i:02d}.png', f'shot-{i:02d}-guide.png'
            subprocess.run([ffmpeg, '-hide_banner', '-nostdin', '-v', 'error', '-ss', str(shot['start']),
                            '-i', str(resolve(shot['source'])), '-loop', '1', '-i', str(overlay),
                            '-filter_complex', graph, '-map', '[v]', '-an', '-frames:v', '1',
                            '-n', str(output / clean_name)], check=True, capture_output=True)
            with Image.open(output / clean_name) as clean:
                if clean.size != (1080, 1920):
                    raise ValueError('Unexpected storyboard raster size')
                guide_image(clean).save(output / guide_name)
            records.append({'shot': i, 'source': str(resolve(shot['source'])),
                            'source_time_seconds': shot['start'] + frame_index / 24,
                            'frame_index_in_shot': frame_index, 'duration': shot['duration'],
                            'caption': shot['caption'], 'image': clean_name, 'guide_image': guide_name,
                            'text_bounds': bounds, 'sha256': sha256(output / clean_name)})
    sheets = []
    total_pages = (len(records) + 5) // 6
    for page in range(1, total_pages + 1):
        subset = records[(page - 1) * 6:page * 6]
        for guided, suffix in ((False, ''), (True, '-guide')):
            name = f'storyboard-{page:02d}{suffix}.png'
            contact_sheet(output, subset, page, total_pages, guided).save(output / name)
            sheets.append(name)
    for path, info in source_info.items():
        stat = Path(path).stat()
        if stat.st_size != info['size'] or stat.st_mtime_ns != info['mtime_ns']:
            raise ValueError('Source changed while creating storyboard')
    if sha256(plan_path) != plan_hash or any(sha256(f['path']) != f['sha256'] for f in fonts):
        raise ValueError('Plan/font changed while creating storyboard')
    report = {'status': 'storyboard_generated_not_user_approved', 'plan': str(plan_path),
              'plan_sha256': plan_hash, 'effective_plan_sha256': effective_hash,
              'duration_seconds': prepared['total'], 'shots': records, 'fonts': fonts,
              'sources': source_info, 'sheets': sheets,
              'ui_guides': 'illustrative_not_official_safe_zones',
              'motion_review': 'not_checked', 'agent_image_view': 'not_checked',
              'video_rendered': False}
    with (output / 'storyboard.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return {'output_dir': str(output), 'manifest': str(output / 'storyboard.json'),
            'sheets': [str(output / n) for n in sheets], 'shots': len(records),
            'status': report['status'], 'video_rendered': False}
