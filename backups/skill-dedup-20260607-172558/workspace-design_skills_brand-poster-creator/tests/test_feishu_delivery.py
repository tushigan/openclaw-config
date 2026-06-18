from __future__ import annotations

import importlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

from PIL import Image

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import prepare_feishu_delivery
from project_manager import load_json


class FeishuDeliveryManifestTest(unittest.TestCase):
    def make_project(self, tmp_path: Path) -> Path:
        project_dir = tmp_path / 'BP-test-delivery'
        image_dir = project_dir / 'images'
        image_dir.mkdir(parents=True)
        Image.new('RGB', (64, 96), (240, 220, 180)).save(image_dir / 'final_poster.png')
        return project_dir

    def prepare_manifest(self, tmp_path: Path) -> tuple[Path, dict]:
        project_dir = self.make_project(tmp_path)
        delivery_dir = tmp_path / 'feishu-deliver'
        argv = [
            'prepare_feishu_delivery.py',
            '--project-dir',
            str(project_dir),
        ]
        with patch.object(prepare_feishu_delivery, 'DELIVERY_DIR', delivery_dir):
            with patch.object(sys, 'argv', argv):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(prepare_feishu_delivery.main(), 0)
        return project_dir, load_json(project_dir / 'delivery_manifest.json')

    def test_manifest_requires_real_feishu_media_tool_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir, manifest = self.prepare_manifest(Path(tmp))

            self.assertEqual(manifest['delivery_status'], 'not_attempted')
            self.assertEqual(manifest['user_report'], 'IMAGE READY BUT NOT DELIVERED TO USER')

            contract = manifest['agent_delivery_contract']
            self.assertTrue(contract['completion_requires_tool_success'])
            self.assertIn('MEDIA:', contract['forbidden_text_delivery_prefixes'])
            self.assertIn('/Users/', contract['forbidden_text_delivery_prefixes'])

            send_plan = contract['send_plan']
            self.assertEqual(send_plan['tool'], 'message')
            self.assertEqual(send_plan['path'], manifest['deliverables']['original_copy']['path'])
            self.assertTrue(Path(send_plan['path']).exists())

            args = send_plan['message_tool_arguments']
            self.assertEqual(args['action'], 'send')
            self.assertEqual(args['channel'], 'feishu')
            self.assertEqual(args['media'], send_plan['path'])
            self.assertIn(args['mimeType'], {'image/png', 'image/jpeg'})

            record_command = contract['after_success_record_command']
            self.assertIn(str(project_dir), record_command)
            self.assertIn('--message-id', record_command)
            self.assertIn('--chat-id', record_command)

    def test_record_delivery_marks_manifest_and_project_state_done(self):
        record_feishu_delivery = importlib.import_module('record_feishu_delivery')

        with tempfile.TemporaryDirectory() as tmp:
            project_dir, manifest = self.prepare_manifest(Path(tmp))
            sent_path = manifest['agent_delivery_contract']['send_plan']['path']

            manifest_path = record_feishu_delivery.record_delivery(
                project_dir=project_dir,
                sent_path=sent_path,
                message_id='om_test_message',
                chat_id='oc_test_chat',
                method='message(media)',
            )

            updated = load_json(manifest_path)
            state = load_json(project_dir / 'project_state.json')

        self.assertTrue(updated['delivery_attempted'])
        self.assertEqual(updated['delivery_status'], 'sent')
        self.assertEqual(updated['delivery_evidence']['message_id'], 'om_test_message')
        self.assertEqual(updated['delivery_evidence']['chat_id'], 'oc_test_chat')
        self.assertIn(str(Path(sent_path).resolve()), updated['delivery_evidence']['sent_paths'])
        self.assertEqual(updated['user_report'], '')
        self.assertEqual(state['stage_status']['delivery'], 'done')
        self.assertTrue(state['workflow_flags']['delivery_ready'])


if __name__ == '__main__':
    unittest.main()
