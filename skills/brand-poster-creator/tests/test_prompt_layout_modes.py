import importlib.util
import unittest
from pathlib import Path


ROOT = Path('/Users/a123/.openclaw/skills/brand-poster-creator')
ASSEMBLE_SCRIPT = ROOT / 'scripts' / 'assemble_prompt.py'


def load_assemble_module():
    spec = importlib.util.spec_from_file_location('assemble_prompt_layout_modes_test', ASSEMBLE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PromptLayoutModeTests(unittest.TestCase):
    def test_free_layout_uses_relative_regions_without_placeholder_positions(self):
        assemble = load_assemble_module()
        brief = {
            'brand_name': '测试品牌',
            'product_name': '云朵软吐司',
            'ratio': '9:16',
            'type': '产品上新',
            'hero_priority': {
                'hero_1': '云朵软吐司',
                'hero_2': '蓝天白云氛围',
            },
        }
        copywriting = {
            'headline': {'文案': '云朵软吐司'},
            'subline': {'文案': '一口咬到云般软'},
            'selling_point': {'文案': '水牛奶和面'},
        }

        prompt, _, _ = assemble.assemble_prompt(
            brief,
            distill=None,
            copywriting=copywriting,
            refs={},
        )

        self.assertIn('== 画面布局（自由构图与阅读动线） ==', prompt)
        self.assertIn('顶部信息区', prompt)
        self.assertIn('中部主视觉区', prompt)
        self.assertIn('底部信息区', prompt)
        self.assertNotIn('放置在画面适当位置', prompt)
        self.assertNotIn('不要只给静态站姿', prompt)
        self.assertNotIn('x:', prompt)
        self.assertIn('云朵软吐司', prompt)
        self.assertIn('一口咬到云般软', prompt)
        self.assertIn('水牛奶和面', prompt)

    def test_fixed_layout_uses_distill_coordinates_and_not_free_layout(self):
        assemble = load_assemble_module()
        brief = {
            'brand_name': '测试品牌',
            'product_name': '云朵软吐司',
            'ratio': '9:16',
            'type': '产品上新',
            'hero_priority': {'hero_1': '云朵软吐司'},
        }
        distill = {
            'layout_analysis': {
                'elements': [
                    {
                        'id': 'title-main',
                        'type': 'title',
                        'name_zh': '主标题区',
                        'x': 12,
                        'y': 8,
                        'width': 76,
                        'height': 12,
                        'z_index': 3,
                        '排版方向': '横排',
                    },
                    {
                        'id': 'product-hero',
                        'type': 'product_photo',
                        'name_zh': '产品主图区',
                        'x': 16,
                        'y': 32,
                        'width': 68,
                        'height': 42,
                        'z_index': 4,
                    },
                ],
                'negative_constraints': [],
            },
        }
        copywriting = {
            'title-main': {'文案': '云朵软吐司', '字体风格': '圆润醒目'},
        }

        prompt, _, _ = assemble.assemble_prompt(
            brief,
            distill=distill,
            copywriting=copywriting,
            refs={},
        )
        blocking_errors, _ = assemble.validate_prompt(
            prompt,
            distill=distill,
            copywriting=copywriting,
        )

        self.assertEqual(blocking_errors, [])
        self.assertIn('== 画面布局（固定版式坐标） ==', prompt)
        self.assertIn('【固定区域 title-main - 主标题区】x:12% y:8% 宽:76% 高:12% z:3', prompt)
        self.assertIn('【固定区域 product-hero - 产品主图区】x:16% y:32% 宽:68% 高:42% z:4', prompt)
        self.assertNotIn('== 画面布局（自由构图与阅读动线） ==', prompt)
        self.assertNotIn('无固定版式', prompt)

    def test_fixed_layout_without_product_region_adds_coordinate_product_guard(self):
        assemble = load_assemble_module()
        brief = {
            'brand_name': '测试品牌',
            'product_name': '云朵软吐司',
            'ratio': '9:16',
            'type': '产品上新',
            'hero_priority': {'hero_1': '产品主视觉'},
        }
        distill = {
            'layout_analysis': {
                'elements': [
                    {
                        'id': 'title-main',
                        'type': 'title',
                        'name_zh': '主标题区',
                        'x': 12,
                        'y': 8,
                        'width': 76,
                        'height': 12,
                        'z_index': 3,
                    },
                ],
                'negative_constraints': [],
            },
        }
        refs = {
            '产品图': {
                '路径': '/tmp/product.png',
                '产品名': '云朵软吐司',
            }
        }

        prompt, _, _ = assemble.assemble_prompt(
            brief,
            distill=distill,
            copywriting={'title-main': {'文案': '云朵软吐司'}},
            refs=refs,
        )

        self.assertIn('== 画面布局（固定版式坐标） ==', prompt)
        self.assertIn('== 产品主视觉区域 ==', prompt)
        self.assertIn('固定版式中缺少独立产品主图区', prompt)
        self.assertIn('x:14% y:31% 宽:72% 高:46% z:3', prompt)
        self.assertNotIn('== 画面布局（自由构图与阅读动线） ==', prompt)

    def test_free_layout_product_guard_uses_relative_region_not_coordinates(self):
        assemble = load_assemble_module()
        brief = {
            'brand_name': '测试品牌',
            'product_name': '云朵软吐司',
            'ratio': '9:16',
            'type': '产品上新',
            'hero_priority': {'hero_1': '产品主视觉'},
        }
        refs = {
            '产品图': {
                '路径': '/tmp/product.png',
                '产品名': '云朵软吐司',
            }
        }

        prompt, _, _ = assemble.assemble_prompt(
            brief,
            distill=None,
            copywriting={'headline': {'文案': '云朵软吐司'}},
            refs=refs,
        )

        self.assertIn('== 产品主视觉区域 ==', prompt)
        self.assertIn('中部主视觉区', prompt)
        self.assertNotIn('x:', prompt)
        self.assertNotIn('宽:', prompt)
        self.assertNotIn('高:', prompt)

    def test_distill_without_elements_still_uses_free_product_guard(self):
        assemble = load_assemble_module()
        brief = {
            'brand_name': '测试品牌',
            'product_name': '云朵软吐司',
            'ratio': '9:16',
            'type': '产品上新',
            'hero_priority': {'hero_1': '产品主视觉'},
        }
        distill = {
            'layout_analysis': {
                'elements': [],
                'negative_constraints': ['不要空白占位框'],
            },
        }
        refs = {
            '产品图': {
                '路径': '/tmp/product.png',
                '产品名': '云朵软吐司',
            }
        }

        prompt, _, _ = assemble.assemble_prompt(
            brief,
            distill=distill,
            copywriting={'headline': {'文案': '云朵软吐司'}},
            refs=refs,
        )

        self.assertIn('== 画面布局（自由构图与阅读动线） ==', prompt)
        self.assertIn('== 产品主视觉区域 ==', prompt)
        self.assertIn('中部主视觉区', prompt)
        self.assertIn('不要空白占位框', prompt)
        self.assertNotIn('== 画面布局（固定版式坐标） ==', prompt)
        self.assertNotIn('x:', prompt)
        self.assertNotIn('宽:', prompt)
        self.assertNotIn('高:', prompt)


if __name__ == '__main__':
    unittest.main()
