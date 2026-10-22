"""Apply an agent-authored visual patch without replacing media or old results."""
import copy
import json
from pathlib import Path

from text_layout import FIELDS, prepare_overlays, validate_overlays


def merge_elements(current, changes):
    if not isinstance(changes, dict):
        raise ValueError('text_overlays patch must be an object')
    cleaned = {}
    for name, settings in changes.items():
        if not isinstance(settings, dict) or set(settings) - FIELDS:
            raise ValueError('Unknown text patch setting')
        cleaned[name] = {k: v for k, v in settings.items() if v is not None}
    validate_overlays(cleaned)
    for name, settings in changes.items():
        element = current.setdefault(name, {})
        for key, value in settings.items():
            if value is None:
                element.pop(key, None)
            else:
                element[key] = value


def customize(plan_path, patch_path, output, root='.'):
    root = Path(root).expanduser().resolve()
    resolve = lambda p: (root / p).resolve()
    source, patch_file, destination = map(resolve, (plan_path, patch_path, output))
    plan = json.loads(source.read_text(encoding='utf-8'))
    patch = json.loads(patch_file.read_text(encoding='utf-8'))
    if not isinstance(patch, dict) or set(patch) - {'text_overlays', 'shots'}:
        raise ValueError('Visual patch supports text_overlays and per-shot text_overlays only')
    updated = copy.deepcopy(plan)
    if 'text_overlays' in patch:
        current = updated.setdefault('text_overlays', {})
        merge_elements(current, patch['text_overlays'])
    # Shot keys are one-based string indices, never media paths or timing edits.
    if 'shots' in patch and not isinstance(patch['shots'], dict):
        raise ValueError('shots patch must map one-based indices to text_overlays')
    for index, changes in patch.get('shots', {}).items():
        if not index.isdecimal() or not 1 <= int(index) <= len(updated['shots']):
            raise ValueError('Shot index is outside the plan')
        if not isinstance(changes, dict) or set(changes) != {'text_overlays'}:
            raise ValueError('Per-shot visual patch accepts text_overlays only')
        current = updated['shots'][int(index) - 1].setdefault('text_overlays', {})
        merge_elements(current, changes['text_overlays'])
    for shot in updated['shots']:
        prepare_overlays(updated, shot, resolve)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(updated, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return {'plan': str(destination), 'previous_plan': str(source), 'changes': patch}
