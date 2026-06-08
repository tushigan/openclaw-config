import importlib.util
import unittest
from pathlib import Path


ROOT = Path('/Users/a123/.openclaw/skills/brand-poster-creator')
ASSEMBLE_SCRIPT = ROOT / 'scripts' / 'assemble_prompt.py'
CREATIVE_SCRIPT = ROOT / 'scripts' / 'generate_creative_direction.py'


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CreativeDirectionPromptTermTests(unittest.TestCase):
    def test_creative_direction_does_not_leak_workflow_terms_into_prompt(self):
        creative = load_module('generate_creative_direction_for_test', CREATIVE_SCRIPT)
        assemble = load_module('assemble_prompt_for_creative_test', ASSEMBLE_SCRIPT)

        brief = {
            'brand_name': '测试品牌',
            'product_name': '粉色礼盒',
            'ratio': '9:16',
            'type': '节日海报',
            'hero_priority': {'hero_1': '粉色礼盒'},
        }
        copywriting = {
            'headline': {'文案': '甜蜜心意'},
            'subline': {'文案': '把祝福装进礼盒'},
        }

        creative_direction = creative.build_creative_direction(
            brief,
            copywriting,
            distill=None,
            style_profile=None,
        )
        prompt, _, _ = assemble.assemble_prompt(
            brief,
            distill=None,
            copywriting=copywriting,
            refs={},
            creative_direction=creative_direction,
        )
        blocking_errors, _ = assemble.validate_prompt(
            prompt,
            distill=None,
            copywriting=copywriting,
            creative_direction=creative_direction,
        )

        self.assertEqual(blocking_errors, [])


if __name__ == '__main__':
    unittest.main()
