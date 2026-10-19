"""Portable defaults for the compact two-line timelog requested by the user."""
import copy
import json
from pathlib import Path


def apply_timelog_defaults(plan):
    result = copy.deepcopy(plan)
    enabled = result.get('timeline_mode', any('time_label' in s for s in result.get('shots', [])))
    if enabled is not True or result.get('timeline_layout') == 'split':
        return result
    skill = Path(__file__).resolve().parents[1]
    defaults = json.loads((skill / 'references/timelog-style.json').read_text(encoding='utf-8'))
    for key in ('timeline_layout', 'timeline_time_font_size'):
        result.setdefault(key, defaults[key])
    result.setdefault('font', str(skill / 'assets/fonts/Pretendard-SemiBold.otf'))
    result['caption_style'] = {**defaults['caption_style'], **(result.get('caption_style') or {})}
    return result
