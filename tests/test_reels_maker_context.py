"""The renamed skill keeps each client's existing private profile and install scope."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(os.environ.get('DAILY_VLOG_TEST_SKILL', ROOT / 'reels-maker'))
sys.path.insert(0, str(SKILL / 'scripts'))
from installation_context import installation_context


class RenamedContextTests(unittest.TestCase):
    def test_both_names_clients_and_scopes_reuse_private_profile(self):
        with tempfile.TemporaryDirectory(prefix='릴스 이름 변경 ') as td:
            root = Path(td)
            for client, container_name in (('codex', '.agents'), ('claude-code', '.claude')):
                config = root / client / '개인 설정'
                profile = config / 'daily-vlog/user-overrides.json'
                profile.parent.mkdir(parents=True)
                profile.write_bytes(b'{"preserve": "existing preferences"}')
                for name in ('daily-vlog', 'reels-maker'):
                    for scope in ('project', 'user'):
                        with self.subTest(client=client, name=name, scope=scope):
                            base = config if scope == 'user' else root / client / '작품' / container_name
                            skill = base / 'skills' / name
                            skill.mkdir(parents=True, exist_ok=True)
                            (skill.parent / f'.{name}-install').write_text(
                                f'skill-install-v1\n{client}\n{scope}\n', encoding='utf-8')
                            with patch.dict(os.environ, {'CODEX_HOME':str(config), 'CLAUDE_CONFIG_DIR':str(config)}, clear=True):
                                result = installation_context(skill)
                            self.assertEqual(result['client'], client)
                            self.assertEqual(result['scope'], scope)
                            self.assertEqual(Path(result['profile']), profile.resolve())
                            self.assertEqual(profile.read_bytes(), b'{"preserve": "existing preferences"}')

    def test_bad_new_name_marker_is_rejected_without_profile_writes(self):
        with tempfile.TemporaryDirectory() as td:
            skill = Path(td)/'.agents/skills/reels-maker'; skill.mkdir(parents=True)
            (skill.parent/'.reels-maker-install').write_text('wrong-record\n', encoding='utf-8')
            with self.assertRaises(ValueError): installation_context(skill)


if __name__ == '__main__': unittest.main()
