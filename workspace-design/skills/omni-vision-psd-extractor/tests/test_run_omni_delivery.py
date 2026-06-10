import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_omni_delivery.py"
spec = importlib.util.spec_from_file_location("run_omni_delivery", MODULE_PATH)
run_omni_delivery = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(run_omni_delivery)


class RunOmniDeliveryTests(unittest.TestCase):
    def test_split_package_lists_every_required_file_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            psd_path = out_dir / "layered-output.psd"
            psd_path.write_bytes(os.urandom(30 * 1024 * 1024))

            info = run_omni_delivery.make_delivery_package(out_dir, split_mb=20)

            self.assertTrue(info["split"])
            self.assertGreater(len(info["parts"]), 1)
            self.assertEqual(info["deliveryFiles"], info["parts"])
            self.assertTrue(info["validation"]["ok"])
            self.assertIn(str(out_dir / "layered-output-delivery.zip"), info["deliveryFiles"])
            self.assertTrue(any(path.endswith(".z01") for path in info["deliveryFiles"]))

    def test_resolves_feishu_target_from_source_session_key(self):
        direct = run_omni_delivery.resolve_delivery_target(
            feishu_target="",
            feishu_user_id="",
            feishu_chat_id="",
            feishu_account_id="design",
            source_session_key="agent:design:feishu:direct:ou_user123",
        )
        self.assertEqual(direct["target"], "user:ou_user123")
        self.assertEqual(direct["user_id"], "ou_user123")

        group = run_omni_delivery.resolve_delivery_target(
            feishu_target="",
            feishu_user_id="",
            feishu_chat_id="",
            feishu_account_id="design",
            source_session_key="agent:design-shared:feishu:group:oc_chat123",
        )
        self.assertEqual(group["target"], "chat:oc_chat123")
        self.assertEqual(group["chat_id"], "oc_chat123")


if __name__ == "__main__":
    unittest.main()
