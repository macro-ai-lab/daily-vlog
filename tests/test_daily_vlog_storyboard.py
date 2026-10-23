"""Check the optional actual-frame style preview, layout edits and MP4 agreement."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(os.environ['DAILY_VLOG_TEST_SKILL']) if os.environ.get('DAILY_VLOG_TEST_SKILL') else (ROOT / 'share/daily-vlog' if (ROOT / 'share/daily-vlog').is_dir() else ROOT / 'daily-vlog')
sys.path.insert(0, str(SKILL / 'scripts'))
from PIL import Image, ImageChops, ImageStat
from media_runtime import ffmpeg_path
from fonts import fetch_font
from storyboard import storyboard
from customize import customize


class StoryboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix='storyboard-한글 ')
        cls.root = Path(cls.workspace.name)
        cls.source = cls.root / '원본 sample.mp4'
        subprocess.run([ffmpeg_path(), '-hide_banner', '-nostdin', '-v', 'error', '-f', 'lavfi',
                        '-i', 'testsrc2=size=640x360:rate=24:duration=4', '-an', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', str(cls.source)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.isolated = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.isolated.cleanup)
        self.work = Path(self.isolated.name)
        isolated = patch('overrides.default_store_path', return_value=self.work / 'no-profile.json')
        isolated.start(); self.addCleanup(isolated.stop)
        self.plan = {'source_kind': 'personal', 'timeline_mode': True,
                     'time_label_policy': 'editorial', 'disclosure_label': '예시 시각 · 기능 검증',
                     'text_overlays': {'time': {'position': 'center', 'position_mode': 'fixed'},
                                       'caption': {'position': 'bottom', 'y': 1300},
                                       'title': {'text': '배치 확인', 'position': 'top', 'y': 320, 'enabled': False}},
                     'shots': [{'source': str(self.source), 'start': 0, 'duration': 2.5,
                                'crop_x': .1 + i * .2, 'crop_end_x': .2 + i * .2,
                                'caption': '장면 확인', 'time_label': '10:30',
                                'timeline_offset_y': i * 80} for i in range(4)]}
        self.plan['shots'][0]['text_overlays'] = {'title': {'enabled': True}}
        self.path = self.work / 'plan.json'
        self.path.write_text(json.dumps(self.plan, ensure_ascii=False), encoding='utf-8')

    def test_real_stills_fixed_clock_guides_and_no_overwrite(self):
        original = self.path.read_bytes()
        env = dict(os.environ, DAILY_VLOG_PROFILE=str(self.work/'no-profile.json'), PYTHONUTF8='1')
        run = subprocess.run([sys.executable, str(SKILL/'scripts/vlog.py'), 'style-preview', str(self.path),
                              '--root', str(self.work), '--output-dir', str(self.work/'board')],
                             env=env, check=True, capture_output=True, text=True, encoding='utf-8', timeout=60)
        result = json.loads(run.stdout)
        report = json.loads(Path(result['manifest']).read_text(encoding='utf-8'))
        self.assertEqual(len(report['shots']), 4)
        self.assertFalse(result['video_rendered'])
        self.assertEqual(report['agent_image_view'], 'not_checked')
        self.assertEqual(self.path.read_bytes(), original)
        for shot in report['shots']:
            time = shot['text_bounds']['time']
            self.assertAlmostEqual((time[1] + time[3]) / 2, 960)
            self.assertEqual(shot['source_time_seconds'], 1.25)
            with Image.open(self.work/'board'/shot['image']) as clean, Image.open(self.work/'board'/shot['guide_image']) as guide:
                self.assertEqual(clean.size, (1080, 1920))
                self.assertIsNotNone(ImageChops.difference(clean.convert('RGB'), guide.convert('RGB')).getbbox())
        self.assertIn('title', report['shots'][0]['text_bounds'])
        self.assertNotIn('title', report['shots'][1]['text_bounds'])
        self.assertEqual(len(report['sheets']), 2)
        with self.assertRaises(FileExistsError): storyboard(self.path, self.work/'board', self.work)

    def test_patch_changes_only_selected_caption_and_keeps_clock(self):
        a = storyboard(self.path, self.work/'first', self.work)
        font = fetch_font('SUIT', self.work/'unused')['font']
        change = {'shots': {'2': {'text_overlays': {'caption': {'font': font, 'position': 'top', 'position_mode': 'fixed', 'y': 500}}}}}
        patch_file = self.work/'patch.json'; patch_file.write_text(json.dumps(change), encoding='utf-8')
        customize(self.path, patch_file, self.work/'next.json', self.work)
        b = storyboard(self.work/'next.json', self.work/'next', self.work)
        first = json.loads(Path(a['manifest']).read_text(encoding='utf-8'))
        next_ = json.loads(Path(b['manifest']).read_text(encoding='utf-8'))
        self.assertNotEqual(first['effective_plan_sha256'], next_['effective_plan_sha256'])
        self.assertEqual(first['shots'][0]['sha256'], next_['shots'][0]['sha256'])
        self.assertNotEqual(first['shots'][1]['sha256'], next_['shots'][1]['sha256'])
        self.assertEqual(first['shots'][1]['text_bounds']['time'], next_['shots'][1]['text_bounds']['time'])
        self.assertLess(next_['shots'][1]['text_bounds']['caption'][3], 600)
        self.assertEqual(json.loads((self.work/'next.json').read_text())['shots'][1]['source'], str(self.source))

    def test_fabricated_clock_fails_before_creating_outputs(self):
        self.plan['time_label_policy'] = 'capture_verified'
        self.path.write_text(json.dumps(self.plan), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'evidence'):
            storyboard(self.path, self.work/'invalid', self.work)
        self.assertFalse((self.work/'invalid').exists())

    def test_bundled_choices_use_verified_files_without_system_install(self):
        for name in ['Pretendard', 'SUIT', '마루부리', '고운바탕', '검은고딕']:
            choice = fetch_font(name, self.work/'fonts')
            self.assertTrue(choice['bundled'])
            self.assertTrue(Path(choice['font']).is_file())
            self.assertTrue(Path(choice['license']).is_file())
            self.assertNotIn('font_weight', choice)
        self.assertFalse((self.work/'fonts').exists())

    def test_still_matches_frame_from_final_mp4(self):
        result = storyboard(self.path, self.work/'board', self.work)
        lock = self.work/'render.lock'; lock.touch()
        command = [sys.executable, str(SKILL/'scripts/render.py'), str(self.path), '--root', str(self.work),
                   '--output', 'preview.mp4', '--poster', 'poster.jpg', '--shared-lock', str(lock)]
        env = dict(os.environ)
        # A child render must not read the developer's real personal defaults.
        env['CODEX_HOME'] = str(self.work/'client-config')
        subprocess.run(command, check=True, capture_output=True, text=True, env=env, timeout=180)
        extracted = self.work/'from-mp4.png'
        subprocess.run([ffmpeg_path(), '-hide_banner', '-nostdin', '-v', 'error', '-i', str(self.work/'preview.mp4'),
                        '-vf', r'select=eq(n\,30)', '-frames:v', '1', str(extracted)], check=True, capture_output=True)
        with Image.open(self.work/'board/shot-01.png') as still, Image.open(extracted) as movie:
            diff = ImageStat.Stat(ImageChops.difference(still.convert('RGB'), movie.convert('RGB')))
            self.assertLess(sum(diff.mean)/3, 4.0)  # H.264 quantization is expected.


if __name__ == '__main__':
    unittest.main()
