import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path('/Users/a123/.openclaw/skills/brand-poster-creator')
NORMALIZE_SCRIPT = ROOT / 'scripts' / 'normalize_product_reference.py'
ASSEMBLE_SCRIPT = ROOT / 'scripts' / 'assemble_prompt.py'


def load_assemble_module():
    spec = importlib.util.spec_from_file_location('assemble_prompt_for_test', ASSEMBLE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_low_res_toast(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', (407, 379), (242, 239, 230))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((85, 65, 330, 330), radius=90, fill=(154, 91, 47), outline=(126, 68, 36), width=6)
    draw.rectangle((112, 160, 306, 332), fill=(113, 74, 52))
    for x, y, r in [(145, 185, 5), (180, 220, 3), (210, 200, 6), (245, 248, 4), (270, 210, 5)]:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(54, 38, 30))
    img.save(path, quality=92)


class ProductReferenceNormalizationTests(unittest.TestCase):
    def test_normalization_generates_deterministic_soft_proxy(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            product_path = project_dir / 'images' / 'product.jpg'
            write_low_res_toast(product_path)
            (project_dir / 'brief.json').write_text(json.dumps({
                'type': '产品推广',
                'industry': '烘焙食品 / 可可吐司',
                'product_name': '纯脂可可吐司',
                'assets': {'product': 'images/product.jpg'},
            }, ensure_ascii=False), encoding='utf-8')

            proc = subprocess.run(
                [sys.executable, str(NORMALIZE_SCRIPT), '--project-dir', str(project_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            brief = json.loads((project_dir / 'brief.json').read_text(encoding='utf-8'))
            manifest = json.loads((project_dir / 'product_reference_manifest.json').read_text(encoding='utf-8'))
            output = project_dir / brief['assets']['product']

            self.assertEqual(brief['assets']['product_original'], 'images/product.jpg')
            self.assertEqual(brief['assets']['product_normalization']['method'], 'deterministic_soft_proxy')
            self.assertEqual(manifest['status'], 'generated')
            self.assertEqual(manifest['method'], 'deterministic_soft_proxy')
            self.assertTrue(output.exists())
            with Image.open(output) as img:
                self.assertEqual(img.size, (1024, 1024))

            assemble = load_assemble_module()
            self.assertEqual(assemble.validate_product_normalization_gate(brief, project_dir), '')

    def test_prompt_gate_rejects_manual_product_realized_without_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            write_low_res_toast(project_dir / 'images' / 'product.jpg')
            write_low_res_toast(project_dir / 'images' / 'product_realized.png')
            brief = {
                'type': '产品推广',
                'industry': '烘焙食品 / 可可吐司',
                'product_name': '纯脂可可吐司',
                'assets': {'product': 'images/product_realized.png'},
                'product_reference_realization': {'original_product': 'images/product.jpg'},
            }

            assemble = load_assemble_module()
            issue = assemble.validate_product_normalization_gate(brief, project_dir)

            self.assertIn('禁止绕过 Step 3.5', issue)
            self.assertIn('product_realized', issue)

    def test_texture_reference_skips_lowres_gate_and_gets_distinct_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            product_path = project_dir / 'images' / 'product.jpg'
            texture_path = project_dir / 'images' / 'crumb_texture.jpg'
            write_low_res_toast(product_path)
            write_low_res_toast(texture_path)
            brief = {
                'type': '产品推广',
                'industry': '烘焙食品 / 可可吐司',
                'product_name': '纯脂可可吐司',
                'assets': {
                    'product': 'images/product.jpg',
                    'product_texture_refs': ['images/crumb_texture.jpg'],
                },
            }
            refs = {
                '产品图': {'路径': str(product_path), '产品名': '纯脂可可吐司'},
                '产品质地参考图': [{'路径': str(texture_path), '来源': '用户上传'}],
            }

            assemble = load_assemble_module()
            self.assertEqual(assemble.validate_product_normalization_gate(brief, project_dir), '')
            block = assemble.build_product_reference_guard(brief, refs)
            ref_lines, image_paths, ref_roles = assemble.assemble_ref_image_refs(refs)

            self.assertIn('产品身份与质地参考分离', block)
            self.assertIn('不需要再生成中间 AI 产品 hero 参考', block)
            self.assertIn('产品质地参考', '\n'.join(ref_lines))
            self.assertEqual([role['role'] for role in ref_roles], ['product', 'product_texture'])
            self.assertEqual(image_paths, [str(product_path), str(texture_path)])


if __name__ == '__main__':
    unittest.main()
