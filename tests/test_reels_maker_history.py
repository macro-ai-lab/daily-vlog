"""Production memory stores real renders, separates types and preserves approved defaults."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(os.environ.get('DAILY_VLOG_TEST_SKILL', ROOT / 'reels-maker'))
sys.path.insert(0, str(SKILL / 'scripts'))
from production_history import show, record, feedback, store_path
from media_runtime import ffmpeg_path


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='제작 이력 ')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.store = self.root/'개인 이력'
        self.plan = self.root/'plan.json'
        self.output = self.root/'video.mp4'
        self.data = {'production_id': 'one-production', 'edit_format': 'story',
                     'text_overlays': {'caption': {'font_size': 64}},
                     'shots': [{'caption': '첫 장면', 'duration': 1}]}
        self.plan.write_text(json.dumps(self.data), encoding='utf-8')
        subprocess.run([ffmpeg_path(), '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=blue:s=160x284:r=24:d=1', '-an', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', str(self.output)], check=True, capture_output=True)

    def test_read_only_empty_and_client_profile_location(self):
        self.assertEqual(show(store=self.store)['by_format']['story']['production_count'], 0)
        self.assertFalse(self.store.exists())
        with patch.dict(os.environ, {'REELS_MAKER_HISTORY': str(self.store)}):
            self.assertEqual(store_path(), self.store.resolve())
        with patch.dict(os.environ, {}, clear=True), patch('overrides.default_store_path', return_value=self.root/'config/user-overrides.json'):
            self.assertEqual(store_path(), self.root/'config/production-history')

    def test_revisions_feedback_types_and_no_private_default_change(self):
        profile = self.root/'user-overrides.json'
        original = b'{"private":"keep untouched"}'
        profile.write_bytes(original)
        with patch.dict(os.environ, {'DAILY_VLOG_PROFILE': str(profile)}):
            first = record(self.output, self.plan, store=self.store)
            self.assertEqual(record(self.output, self.plan, store=self.store)['status'], 'already_recorded')
            feedback(first['id'], 'needs_changes', '자막을 더 짧게', ['자막 축소'], self.store)
            feedback(first['id'], 'accepted', '이 버전 좋아', store=self.store)
            self.assertEqual(feedback(first['id'], 'accepted', '이 버전 좋아', store=self.store)['status'], 'already_recorded')
            second = self.root/'video-v002.mp4'; second.write_bytes(self.output.read_bytes())
            revision = record(second, self.plan, store=self.store)
            state = show('story', self.store)['by_format']['story']
            self.assertEqual((state['render_count'], state['production_count']), (2, 1))
            self.assertEqual(state['accepted_production_count'], 0)  # Latest version has no feedback.
            feedback(revision['id'], 'accepted', '새 버전으로 완성', store=self.store)
            record(self.output, self.plan, 'timelog', self.root/'other-store', 'different-production')
            moment = self.root/'moments.mp4'; moment.write_bytes(self.output.read_bytes())
            record(moment, self.plan, 'moments', self.store, 'second-production')
            summary = show(store=self.store)['by_format']
            self.assertEqual(summary['moments']['production_count'], 1)
            self.assertEqual(summary['story']['accepted_production_count'], 1)
            self.assertEqual(summary['timelog']['render_count'], 0)
            self.assertEqual(profile.read_bytes(), original)
            cached = json.loads((self.store/'summary.json').read_text(encoding='utf-8'))
            self.assertEqual(cached['by_format'], summary)
            self.assertEqual(len(list((self.store/'records').glob('*.json'))), 3)

    def test_new_content_types_and_editing_methods_need_no_code_changes(self):
        self.data.update(edit_format='comparison', content_type='shopping_review', content_type_label='쇼핑 후기')
        self.plan.write_text(json.dumps(self.data), encoding='utf-8')
        entry = record(self.output, self.plan, store=self.store)
        summary = show(store=self.store)
        self.assertEqual(summary['by_type']['shopping_review']['label'], '쇼핑 후기')
        self.assertEqual(summary['by_format']['comparison']['production_count'], 1)
        feedback(entry['id'], 'accepted', '이 구매 후기 좋다', store=self.store)
        self.assertEqual(show(store=self.store, content_type='shopping_review')['by_type']['shopping_review']['accepted_production_count'], 1)
        second = self.root/'travel.mp4'; second.write_bytes(self.output.read_bytes())
        record(second, self.plan, 'timelog', self.store, 'trip', 'travel_review', '여행 후기')
        third = self.root/'ad.mp4'; third.write_bytes(self.output.read_bytes())
        record(third, self.plan, 'demonstration', self.store, 'ad', 'advertisement', '광고')
        self.assertEqual(set(show(store=self.store)['by_type']), {'shopping_review', 'travel_review', 'advertisement'})
        self.assertEqual(show(store=self.store, content_type='unknown_new_type')['by_type']['unknown_new_type']['production_count'], 0)
        self.assertEqual(len(list((self.store/'records').glob('*.json'))), 3)
        with self.assertRaises(ValueError): record(self.output, self.plan, '../unsafe', self.store)

    def test_legacy_records_keep_bytes_and_classification(self):
        entry = record(self.output, self.plan, store=self.store)
        path = self.store/'records'/(entry['id']+'.json')
        old = json.loads(path.read_text(encoding='utf-8'))
        old.pop('content_type'); old.pop('content_type_label')
        path.write_text(json.dumps(old), encoding='utf-8'); original = path.read_bytes()
        summary = show(store=self.store)
        self.assertEqual(summary['by_type']['story']['production_count'], 1)
        self.assertEqual(summary['by_format']['story']['production_count'], 1)
        self.assertEqual(path.read_bytes(), original)

    def test_invalid_render_and_auto_do_not_create_history(self):
        self.output.write_bytes(b'not a video')
        with self.assertRaises(Exception): record(self.output, self.plan, store=self.store)
        self.assertFalse(self.store.exists())
        with self.assertRaises(ValueError): record(self.output, self.plan, 'auto', self.store)
        with self.assertRaises(ValueError): feedback('../invalid', 'accepted', 'okay', store=self.store)

    def test_corruption_is_not_silently_replaced(self):
        (self.store/'records').mkdir(parents=True)
        corrupt = self.store/'records/bad.json'; corrupt.write_bytes(b'{broken')
        with self.assertRaises(ValueError): record(self.output, self.plan, store=self.store)
        self.assertEqual(corrupt.read_bytes(), b'{broken')
        self.assertEqual(len(list((self.store/'records').glob('*.json'))), 1)


if __name__ == '__main__': unittest.main()
