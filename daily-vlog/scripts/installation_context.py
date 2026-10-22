"""Resolve the installed client's private profile without editing client settings."""
import os
from pathlib import Path


def installation_context(skill_dir=None):
    skill = Path(skill_dir or Path(__file__).resolve().parents[1]).resolve()
    skills = skill.parent
    container = skills.parent
    marker = skills / '.daily-vlog-install'
    if marker.is_symlink():
        raise ValueError('Invalid skill installation record')
    if marker.exists():
        if marker.is_symlink() or not marker.is_file():
            raise ValueError('Invalid skill installation record')
        lines = marker.read_text(encoding='utf-8').splitlines()
        if len(lines) != 3 or lines[0] != 'skill-install-v1' or lines[1] not in ('codex', 'claude-code') or lines[2] not in ('project', 'user'):
            raise ValueError('Invalid skill installation record')
        client, scope = lines[1:]
    else:
        client = 'claude-code' if container.name == '.claude' else ('codex' if container.name in ('.agents', '.codex') else os.environ.get('AI_SKILL_CLIENT', 'codex'))
        if client not in ('codex', 'claude-code'):
            raise ValueError('Unknown skill client')
        base = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude') if client == 'claude-code' else Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
        if skills.name == 'skills' and container == base.expanduser().resolve():
            scope = 'user'
        elif skills.name == 'skills' and container.name in ('.agents', '.claude'):
            scope = 'project'
        else:
            scope = 'source'
    if scope == 'user':
        base = container
    elif client == 'claude-code':
        base = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')
    else:
        base = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    base = base.expanduser()
    if not base.is_absolute():
        raise ValueError('Client configuration path must be absolute')
    profile = Path(os.environ['DAILY_VLOG_PROFILE']).expanduser() if os.environ.get('DAILY_VLOG_PROFILE') else base / 'daily-vlog/user-overrides.json'
    if not profile.is_absolute():
        raise ValueError('Personal profile path must be absolute')
    return {'client': client, 'scope': scope, 'config_dir': str(base.resolve()),
            'profile': str(profile.resolve()),
            'project_root': str(container.parent) if scope == 'project' else None}
