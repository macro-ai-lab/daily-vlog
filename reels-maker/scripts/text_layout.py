"""Optional per-element text layout; old plans keep the legacy pixel layout."""
import copy
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

ELEMENTS = {'title', 'time', 'caption'}
FIELDS = {'text', 'enabled', 'font', 'font_index', 'font_weight', 'font_size',
          'color', 'stroke_color', 'stroke_width', 'shadow_opacity',
          'position', 'position_mode', 'x', 'y', 'align'}
POSITION_FIELDS = {'position', 'position_mode', 'x', 'y', 'align'}


def validate_overlays(value):
    if not isinstance(value, dict) or set(value) - ELEMENTS:
        raise ValueError('text_overlays supports only title, time, caption')
    for name, config in value.items():
        if not isinstance(config, dict) or set(config) - FIELDS:
            raise ValueError(f'Unknown {name} text setting')
        for key, low, high in [('font_size', 24, 140), ('font_index', 0, 30),
                               ('font_weight', 100, 900), ('stroke_width', 0, 6),
                               ('shadow_opacity', 0, 255), ('x', 40, 1040), ('y', 80, 1800)]:
            if key in config:
                v = config[key]
                if isinstance(v, bool) or not isinstance(v, int) or not low <= v <= high:
                    raise ValueError(f'{name}.{key} must be an integer in {low}..{high}')
        if 'enabled' in config and not isinstance(config['enabled'], bool):
            raise ValueError('enabled must be boolean')
        if 'text' in config and (not isinstance(config['text'], str) or '\n' in config['text']):
            raise ValueError('Text must be one short line')
        # A visual edit must never replace the source-backed capture label.
        if name == 'time' and 'text' in config:
            raise ValueError('Set capture labels on shots with time_label and capture_time_evidence')
        for key in ('color', 'stroke_color'):
            if key in config:
                c = config[key]
                if not isinstance(c, str) or len(c) != 7 or not c.startswith('#'):
                    raise ValueError(f'{key} must be #RRGGBB')
                ImageColor.getrgb(c)
        if config.get('position', 'center') not in ('top', 'center', 'bottom'):
            raise ValueError('position must be top, center, bottom')
        if config.get('position_mode', 'follow_shot') not in ('fixed', 'follow_shot'):
            raise ValueError('position_mode must be fixed or follow_shot')
        if config.get('align', 'center') not in ('left', 'center', 'right'):
            raise ValueError('align must be left, center, right')
        if 'font' in config and (not isinstance(config['font'], str) or not config['font']):
            raise ValueError('font must be a real local font path')
    return value


def prepare_overlays(plan, shot, resolve):
    if 'text_overlays' not in plan and 'text_overlays' not in shot:
        return None
    global_config = validate_overlays(plan.get('text_overlays', {}))
    local_config = validate_overlays(shot.get('text_overlays', {}))
    result = copy.deepcopy(global_config)
    for name, local in local_config.items():
        global_element = global_config.get(name, {})
        if global_element.get('position_mode') == 'fixed':
            for key in POSITION_FIELDS & local.keys():
                if key not in global_element or local[key] != global_element[key]:
                    raise ValueError(f'{name} position is fixed globally; remove the shot position override')
        result[name] = {**result.get(name, {}), **local}
    for config in result.values():
        if 'font' in config:
            config['font'] = str(resolve(config['font']))
    return result


def font_paths(overlays):
    return {Path(c['font']) for c in (overlays or {}).values() if 'font' in c}


def load_font(config):
    path = Path(config['font'])
    if not path.is_file():
        raise FileNotFoundError(f'Requested font is unavailable: {path}')
    index = config.get('font_index', 0) if path.suffix.lower() in ('.ttc', '.otc') else 0
    font = ImageFont.truetype(str(path), config['font_size'], index=index)
    if 'font_weight' in config:
        try:
            axes = font.get_variation_axes()
        except OSError as exc:
            raise ValueError('font_weight requires a variable font; select a static weight file instead') from exc
        weights = []
        found = False
        for axis in axes:
            if axis['name'].decode().lower() == 'weight':
                weight = config['font_weight']
                if not axis['minimum'] <= weight <= axis['maximum']:
                    raise ValueError('Requested weight is outside font axes')
                weights.append(weight)
                found = True
            else:
                weights.append(axis['default'])
        if not found:
            raise ValueError('Font has no weight axis')
        font.set_variation_by_axes(weights)
    return font


def draw_overlay(path, caption, font_path, settings, time_label, timeline_mode,
                 timeline_layout, offset, time_size, disclosure, overlays):
    validate_overlays(overlays)
    image = Image.new('RGBA', (1080, 1920))
    draw = ImageDraw.Draw(image)
    common = dict(font=str(font_path), font_index=0, color='#FFFFFF',
                  stroke_color='#000000', stroke_width=2, shadow_opacity=200,
                  align='center', position_mode='follow_shot')
    defaults = {
        'title': {**common, 'text': '', 'font_size': 64, 'position': 'top', 'position_mode': 'fixed'},
        'time': {**common, 'text': time_label or '', 'font_size': time_size or 54,
                 'x': 540 if timeline_layout == 'center' else 80,
                 'y': 925 if timeline_layout == 'center' else 180,
                 'align': 'center' if timeline_layout == 'center' else 'left'},
        'caption': {**common, 'text': caption, 'font': settings['font'],
                    'font_index': settings['font_index'], 'font_size': settings['font_size'],
                    'color': settings['color'], 'stroke_color': settings['stroke_color'],
                    'stroke_width': settings['stroke_width'], 'shadow_opacity': settings['shadow_opacity'],
                    'x': 540 if settings['align'] == 'center' else settings['margin_x'],
                    'y': settings['y'], 'align': settings['align']},
    }
    bounds = {}
    for name in ('title', 'time', 'caption'):
        override = overlays.get(name, {})
        config = {**defaults[name], **override}
        if 'position' in override and 'align' not in override:
            config['align'] = 'center'
        if not config.get('enabled', True) or not config['text']:
            continue
        if name == 'time' and not timeline_mode:
            raise ValueError('Clock text requires timeline_mode and verified time labels')
        font = load_font(config)
        box = draw.textbbox((0, 0), config['text'], font=font)
        width, height = box[2] - box[0], box[3] - box[1]
        # Named positions use the visible ink center. Explicit y uses its top,
        # preserving legacy coordinates when only a title/font was requested.
        if 'position' in override or name == 'title':
            x = config.get('x', 540)
            y = override.get('y', {'top': 160, 'center': 960, 'bottom': 1700}[config.get('position', 'top')]) - height / 2
            if 'x' not in override:
                x = 540
        else:
            x, y = config['x'], config['y']
        if config['position_mode'] == 'follow_shot' and timeline_layout == 'center':
            y += offset
        if name == 'caption' and not {'y', 'position'} & override.keys() and 'time' in bounds:
            # Keep an explicitly fixed clock still; only the unspecified caption
            # position can give it breathing room after a center-anchor change.
            time_box = bounds['time']
            if y < time_box[3] + 12 and y + height > time_box[1]:
                y = time_box[3] + 12
        left = x if config['align'] == 'left' else x - width if config['align'] == 'right' else x - width / 2
        stroke = config['stroke_width']
        if left - stroke < 40 or left + width + stroke > 1040 or y - stroke < 80 or y + height + stroke + 2 > 1800:
            raise ValueError(f'{name} exceeds safe bounds; shorten text or explicitly adjust its layout')
        xy = (left - box[0], y - box[1])
        if config['shadow_opacity']:
            draw.text((xy[0] + 1, xy[1] + 2), config['text'], font=font,
                      fill=(0, 0, 0, config['shadow_opacity']), stroke_width=stroke)
        draw.text(xy, config['text'], font=font,
                  fill=(*ImageColor.getrgb(config['color']), 245), stroke_width=stroke,
                  stroke_fill=(*ImageColor.getrgb(config['stroke_color']), 245))
        bounds[name] = [left, y, left + width, y + height]
    # Stock/editorial disclosure cannot be switched off by custom title settings.
    if disclosure:
        font = ImageFont.truetype(str(font_path), 26)
        badge = draw.textbbox((80, 80), disclosure, font=font, stroke_width=1)
        for box in bounds.values():
            if max(box[0], badge[0]) < min(box[2], badge[2]) and max(box[1], badge[1]) < min(box[3], badge[3]):
                raise ValueError('Text overlaps required source disclosure; adjust the text position')
        draw.text((80, 80), disclosure, font=font, fill=(255, 255, 255, 245), stroke_width=1, stroke_fill='black')
    image.save(path)
    return bounds
