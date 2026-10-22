"""Portable defaults for the compact two-line timelog requested by the user."""
import json
from pathlib import Path
from overrides import apply_user_overrides
from media_runtime import default_font


def apply_timelog_defaults(plan):
    result = apply_user_overrides(plan)
    enabled = result.get('timeline_mode', any('time_label' in s for s in result.get('shots', [])))
    if enabled is not True or result.get('timeline_layout') == 'split':
        return result
    skill = Path(__file__).resolve().parents[1]
    defaults = json.loads((skill / 'references/timelog-style.json').read_text(encoding='utf-8'))
    for key in ('timeline_layout', 'timeline_time_font_size'):
        result.setdefault(key, defaults[key])
    result.setdefault('font', str(default_font()))
    result['caption_style'] = {**defaults['caption_style'], **(result.get('caption_style') or {})}
    return result
