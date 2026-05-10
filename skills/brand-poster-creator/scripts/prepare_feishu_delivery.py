#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image

FEISHU_LIMIT_BYTES = 10 * 1024 * 1024
PREVIEW_MAX_EDGE = 1600
PREVIEW_JPEG_QUALITY = 88
DELIVERY_DIR = Path('/Users/a123/.openclaw/workspace/feishu-deliver')


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def ensure_delivery_dir() -> None:
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f'{stem}-v{counter}{suffix}')
        if not candidate.exists():
            return candidate
        counter += 1


def make_preview(source_path: Path, project_id: str) -> tuple[Path, int]:
    preview_path = unique_path(DELIVERY_DIR / f'{project_id}-final_poster-preview.jpg')
    with Image.open(source_path) as img:
        preview = img.convert('RGB')
        preview.thumbnail((PREVIEW_MAX_EDGE, PREVIEW_MAX_EDGE))
        preview.save(preview_path, format='JPEG', quality=PREVIEW_JPEG_QUALITY, optimize=True)
    return preview_path, preview_path.stat().st_size


def copy_original(source_path: Path, project_id: str) -> tuple[Path, int]:
    target_path = unique_path(DELIVERY_DIR / f'{project_id}-final_poster{source_path.suffix.lower()}')
    shutil.copy2(source_path, target_path)
    return target_path, target_path.stat().st_size


def make_zip(source_path: Path, project_id: str) -> tuple[Path, int]:
    zip_path = unique_path(DELIVERY_DIR / f'{project_id}-final_poster-original.zip')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(source_path, arcname=source_path.name)
    return zip_path, zip_path.stat().st_size


def build_manifest(project_dir: Path, image_path: Path, original_size: int, original_copy_path: Path | None, original_copy_size: int | None, preview_path: Path | None, preview_size: int | None, zip_path: Path | None, zip_size: int | None) -> dict:
    needs_preview = original_size > FEISHU_LIMIT_BYTES
    return {
        'project_dir': str(project_dir),
        'project_id': project_dir.name,
        'original_image': str(image_path),
        'original_size_bytes': original_size,
        'feishu_limit_bytes': FEISHU_LIMIT_BYTES,
        'needs_preview': needs_preview,
        'delivery_mode': 'preview_and_zip' if needs_preview else 'direct_image',
        'deliverables': {
            'preview_image': {
                'path': str(preview_path) if preview_path else '',
                'size_bytes': preview_size or 0,
            },
            'original_copy': {
                'path': str(original_copy_path) if original_copy_path else '',
                'size_bytes': original_copy_size or 0,
            },
            'original_zip': {
                'path': str(zip_path) if zip_path else '',
                'size_bytes': zip_size or 0,
            },
        },
        'edit_source_image': str(image_path),
        'notes': {
            'preview_for_feishu_only': True,
            'edit_from_original_only': True,
            'zip_for_final_delivery_after_confirmation': needs_preview,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Prepare Feishu delivery assets for brand poster output')
    parser.add_argument('--project-dir', required=True, help='Brand poster project directory')
    parser.add_argument('--image', default='', help='Original image path, defaults to project images/final_poster.png')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    image_path = Path(args.image).resolve() if args.image else project_dir / 'images' / 'final_poster.png'
    if not image_path.exists():
        raise FileNotFoundError(f'原图不存在: {image_path}')

    ensure_delivery_dir()

    project_id = project_dir.name
    original_size = image_path.stat().st_size
    preview_path = None
    preview_size = None
    original_copy_path = None
    original_copy_size = None
    zip_path = None
    zip_size = None

    if original_size > FEISHU_LIMIT_BYTES:
        preview_path, preview_size = make_preview(image_path, project_id)
        original_copy_path, original_copy_size = copy_original(image_path, project_id)
        zip_path, zip_size = make_zip(image_path, project_id)
    else:
        original_copy_path, original_copy_size = copy_original(image_path, project_id)

    manifest = build_manifest(
        project_dir=project_dir,
        image_path=image_path,
        original_size=original_size,
        original_copy_path=original_copy_path,
        original_copy_size=original_copy_size,
        preview_path=preview_path,
        preview_size=preview_size,
        zip_path=zip_path,
        zip_size=zip_size,
    )
    manifest_path = project_dir / 'delivery_manifest.json'
    write_json(manifest_path, manifest)
    print(str(manifest_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
