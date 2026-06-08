#!/usr/bin/env python3
import os
import json
import base64
import argparse
from pathlib import Path
import requests

# Disable proxy to avoid requests going through local proxy
for p in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY']:
    os.environ.pop(p, None)


def normalize_size(raw: str) -> str:
    """Ensure width and height are divisible by 16, rounding up if needed."""
    if 'x' in raw:
        try:
            w_str, h_str = raw.split('x')
            w, h = int(w_str), int(h_str)
            adjusted = False
            if w % 16 != 0:
                w = ((w + 15) // 16) * 16
                adjusted = True
            if h % 16 != 0:
                h = ((h + 15) // 16) * 16
                adjusted = True
            if adjusted:
                print(f'[warn] size {w_str}x{h_str} not divisible by 16; adjusting to {w}x{h}')
            return f'{w}x{h}'
        except (ValueError, TypeError):
            pass
    return raw


def resolve_key(base_url: str) -> str:
    host = (base_url or '').lower()
    if 'aixor.org' in host:
        return os.getenv('BANANA_API_KEY_AIXOR') or os.getenv('BANANA_API_KEY_BACKUP') or os.getenv('BANANA_API_KEY', '')
    return os.getenv('BANANA_API_KEY', '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', required=True)
    ap.add_argument('--mask', required=True)
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--size', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--model', default='gpt-image-2')
    ap.add_argument('--base-url', default='https://n.lconai.com')
    args = ap.parse_args()

    base_url = args.base_url.rstrip('/')
    api_key = resolve_key(base_url)
    if not api_key:
        raise SystemExit(f'No API key found for {base_url}')

    image = Path(args.image)
    mask = Path(args.mask)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    size = normalize_size(args.size)

    headers = {'Authorization': f'Bearer {api_key}'}
    url = f'{base_url}/v1/images/edits'

    files = [
        ('image', (image.name, open(image, 'rb'), 'image/png' if image.suffix.lower()=='.png' else 'image/jpeg')),
        ('mask', (mask.name, open(mask, 'rb'), 'image/png')),
    ]
    data = {
        'model': args.model,
        'prompt': args.prompt,
        'n': '1',
        'size': size,
        'response_format': 'b64_json',
    }

    session = requests.Session()
    session.trust_env = False

    try:
        resp = session.post(url, headers=headers, data=data, files=files, timeout=600)
        print(json.dumps({'status_code': resp.status_code, 'preview': resp.text[:1200]}, ensure_ascii=False, indent=2))
        resp.raise_for_status()
        payload = resp.json()
        item = None
        if isinstance(payload.get('data'), list) and payload['data']:
            item = payload['data'][0]
        elif payload.get('b64_json'):
            item = payload
        elif isinstance(payload.get('data'), dict) and isinstance(payload['data'].get('content'), list) and payload['data']['content']:
            item = payload['data']['content'][0]
        if not item or not item.get('b64_json'):
            raise SystemExit('No b64_json found in response')
        b64 = item['b64_json']
        missing = 4 - len(b64) % 4
        if missing != 4:
            b64 += '=' * missing
        output.write_bytes(base64.b64decode(b64))
        print(str(output))
    finally:
        for _, (_name, fh, _mime) in files:
            try:
                fh.close()
            except Exception:
                pass

if __name__ == '__main__':
    main()
