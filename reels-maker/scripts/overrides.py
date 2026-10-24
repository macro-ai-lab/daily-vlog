"""Reviewable personal skill patches: propose locally, save only after approval."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile

from locking import exclusive_lock
from text_layout import validate_overlays


def default_store_path():
    from installation_context import installation_context
    return Path(installation_context()['profile'])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode('utf-8')


def merge(base, patch, delete_null=True):
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if value is None and delete_null:
            result.pop(key, None)
        elif isinstance(value, dict):
            result[key] = merge(result.get(key, {}), value, delete_null)
        else:
            result[key] = copy.deepcopy(value)
    return result


def validate_defaults(defaults):
    if not isinstance(defaults, dict) or set(defaults) - {'text_overlays'}:
        raise ValueError('Reusable render defaults support text_overlays only; other preferences belong in instructions')
    if 'text_overlays' in defaults:
        validate_overlays(defaults['text_overlays'])


def validate_profile(profile):
    if not isinstance(profile, dict) or profile.get('version') != 1:
        raise ValueError('Unsupported user override profile')
    if not isinstance(profile.get('revision'), int) or isinstance(profile['revision'], bool) or profile['revision'] < 0:
        raise ValueError('Invalid profile revision')
    instructions = profile.get('instructions')
    if not isinstance(instructions, dict) or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v.strip() for k, v in instructions.items()):
        raise ValueError('Instructions must map stable names to nonempty user preference text')
    validate_defaults(profile.get('defaults', {}))
    if not isinstance(profile.get('history'), list):
        raise ValueError('Invalid profile history')
    return profile


def load_profile(store=None):
    path = Path(store) if store is not None else default_store_path()
    if not path.exists():
        return {'version': 1, 'revision': 0, 'instructions': {}, 'defaults': {}, 'history': []}
    return validate_profile(json.loads(path.read_text(encoding='utf-8')))


def apply_user_overrides(plan, store=None):
    profile = load_profile(store)
    # Explicit settings in this particular video always win over personal defaults.
    return merge(profile['defaults'], plan, delete_null=False)


def propose(patch_path, request, output, store=None):
    path = Path(store).expanduser().resolve() if store is not None else default_store_path().resolve()
    patch = json.loads(Path(patch_path).read_text(encoding='utf-8'))
    if not isinstance(patch, dict) or not patch or set(patch) - {'instructions', 'defaults'}:
        raise ValueError('Personal patch accepts instructions and defaults only')
    if not isinstance(request, str) or not request.strip():
        raise ValueError('A short actual user request is required')
    before = load_profile(path)
    after = merge(before, patch)
    validate_profile(after)
    if after['instructions'] == before['instructions'] and after['defaults'] == before['defaults']:
        return {'status': 'already_current', 'store': str(path), 'revision': before['revision']}
    proposal = {'version': 1, 'store': str(path), 'request': request,
                'base_sha256': digest(path.read_bytes()) if path.exists() else None,
                'before': {'instructions': before['instructions'], 'defaults': before['defaults']},
                'after': {'instructions': after['instructions'], 'defaults': after['defaults']},
                'question': '이 변경을 브이로그 스킬의 개인 기본 지침에 반영할까요?'}
    proposal['proposal_id'] = digest(encoded(proposal))
    target = Path(output).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as stream:
        json.dump(proposal, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return {'status': 'awaiting_user_approval', 'proposal': str(target), **proposal}


def save(proposal_path, proposal_id, approval):
    # These strings record the calling agent's evidence; they are not authentication
    # and never replace an actual human reply in the conversation.
    if not isinstance(approval, str) or not approval.strip():
        raise ValueError('Explicit human approval evidence is required')
    proposal = json.loads(Path(proposal_path).read_text(encoding='utf-8'))
    expected = proposal.pop('proposal_id', None)
    if expected != proposal_id or digest(encoded(proposal)) != proposal_id:
        raise ValueError('Proposal changed; show a new proposal and obtain approval again')
    path = Path(proposal['store'])
    if not path.is_absolute():
        raise ValueError('Proposal store must be absolute')
    validate_profile({'version': 1, 'revision': 0, **proposal['after'], 'history': []})
    # Successful save is idempotent for the same proposal. A later profile edit
    # cannot be silently overwritten by an approval for an older revision.
    current = load_profile(path)
    if any(item.get('proposal_id') == proposal_id for item in current['history']):
        return {'status': 'already_applied', 'store': str(path), 'revision': current['revision']}
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix('.lock')
    lock.touch(exist_ok=True)
    with exclusive_lock(lock):
        raw = path.read_bytes() if path.exists() else None
        actual_hash = digest(raw) if raw is not None else None
        if actual_hash != proposal['base_sha256']:
            raise ValueError('Profile changed after proposal; rebase the patch and ask again')
        current = load_profile(path)
        updated = {**current, **proposal['after'], 'revision': current['revision'] + 1}
        updated['history'] = (current['history'] + [{'proposal_id': proposal_id,
                              'request': proposal['request'], 'user_approval': approval}])[-20:]
        validate_profile(updated)
        if raw is not None:
            backup = path.with_name(f'{path.stem}.rev-{current["revision"]}.json')
            with backup.open('xb') as stream:
                stream.write(raw)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.override-', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded(updated) + b'\n')
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return {'status': 'saved', 'store': str(path), 'revision': updated['revision'],
            'instructions': updated['instructions'], 'defaults': updated['defaults']}
