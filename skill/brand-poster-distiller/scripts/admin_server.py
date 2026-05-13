#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import json
import mimetypes
import secrets
import sys
import time
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'library-index.json'
HOST = '127.0.0.1'
PORT = 8766
DATA_ROOT = ROOT / 'data'
USERS = DATA_ROOT / 'users.json'
SESSIONS = DATA_ROOT / 'sessions.json'
SESSION_COOKIE = 'distill_session'
SESSION_TTL = 60 * 60 * 24 * 14

EDITABLE_STRING_FIELDS = {'title', 'subtitle', 'summary'}
EDITABLE_ARRAY_FIELDS = {'tags'}

# Directories allowed for static file serving (relative to ROOT)
ALLOWED_STATIC_PREFIXES = ('site/', 'data/', 'source_images/', 'cards/')


def ensure_store():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if not USERS.exists():
        write_json(USERS, {'users': []})
    if not SESSIONS.exists():
        write_json(SESSIONS, {'sessions': {}})


def read_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now_ts():
    return int(time.time())


def normalize_index(raw):
    if isinstance(raw, dict):
        cards = raw.get('cards', [])
        return {
            'version': raw.get('version', '1.0'),
            'updated_at': raw.get('updated_at', ''),
            'cards': cards if isinstance(cards, list) else [],
        }
    if isinstance(raw, list):
        return {'version': '1.0', 'updated_at': '', 'cards': raw}
    return {'version': '1.0', 'updated_at': '', 'cards': []}


def normalize_source_image_path(rel_path: str) -> str:
    """Normalize source image paths to the canonical directory: data/source-images/.

    Handles legacy paths like 'source_images/XXX.png' → 'data/source-images/XXX.png'.
    Also migrates the actual file if it exists at the old location but not the new one.
    """
    if not rel_path:
        return rel_path
    # Already canonical
    if rel_path.startswith('data/source-images/'):
        return rel_path
    # Legacy: source_images/XXX.ext → data/source-images/XXX.ext
    if rel_path.startswith('source_images/'):
        filename = rel_path[len('source_images/'):]
        canonical = f'data/source-images/{filename}'
        old_file = ROOT / rel_path
        new_file = ROOT / canonical
        if old_file.exists() and not new_file.exists():
            new_file.parent.mkdir(parents=True, exist_ok=True)
            old_file.rename(new_file)
        return canonical
    return rel_path


def normalize_card_source_images(card: dict) -> dict:
    """Normalize all source_images paths in a card dict (in place). Returns card for chaining."""
    raw = card.get('source_images') or []
    normalized = [normalize_source_image_path(p) for p in raw if p]
    if normalized != raw:
        card['source_images'] = normalized
    return card


def load_index():
    return normalize_index(read_json(INDEX))


def hash_password(password: str, salt: str):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 200000).hex()


def load_users():
    ensure_store()
    return read_json(USERS)


def save_users(data):
    write_json(USERS, data)


def load_sessions():
    ensure_store()
    data = read_json(SESSIONS)
    sessions = data.get('sessions', {})
    current = now_ts()
    sessions = {k: v for k, v in sessions.items() if v.get('expires_at', 0) > current}
    data['sessions'] = sessions
    write_json(SESSIONS, data)
    return data


def save_sessions(data):
    write_json(SESSIONS, data)


def find_user(username: str):
    users = load_users().get('users', [])
    return next((u for u in users if u.get('username') == username), None)


def verify_password(user, password: str):
    return user and user.get('password_hash') == hash_password(password, user.get('salt', ''))


def create_session(username: str):
    sessions = load_sessions()
    token = secrets.token_urlsafe(32)
    sessions['sessions'][token] = {'username': username, 'expires_at': now_ts() + SESSION_TTL}
    save_sessions(sessions)
    return token


def delete_session(token: str):
    sessions = load_sessions()
    sessions.get('sessions', {}).pop(token, None)
    save_sessions(sessions)


def parse_cookie(handler):
    raw = handler.headers.get('Cookie', '')
    if not raw:
        return {}
    cookie = SimpleCookie()
    cookie.load(raw)
    return {k: v.value for k, v in cookie.items()}


def current_user(handler):
    token = parse_cookie(handler).get(SESSION_COOKIE)
    if not token:
        return None, None
    sess = load_sessions().get('sessions', {}).get(token)
    if not sess:
        return None, None
    user = find_user(sess.get('username'))
    return user, token


def require_user(handler, roles=None, allow_pending=False):
    user, token = current_user(handler)
    if not user:
        json_response(handler, 401, {'ok': False, 'error': 'UNAUTHORIZED'})
        return None, None
    role = user.get('role', 'pending')
    if not allow_pending and role == 'pending':
        json_response(handler, 403, {'ok': False, 'error': 'PENDING_APPROVAL'})
        return None, None
    if roles and role not in roles:
        json_response(handler, 403, {'ok': False, 'error': 'FORBIDDEN'})
        return None, None
    return user, token


def json_response(handler, status, data, set_cookie=None, clear_cookie=False):
    payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(payload)))
    handler.send_header('Cache-Control', 'no-store')
    if set_cookie:
        handler.send_header('Set-Cookie', f'{SESSION_COOKIE}={set_cookie}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL}')
    if clear_cookie:
        handler.send_header('Set-Cookie', f'{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0')
    handler.end_headers()
    handler.wfile.write(payload)


def safe_read_body(handler):
    length = int(handler.headers.get('Content-Length', '0') or '0')
    raw = handler.rfile.read(length) if length > 0 else b'{}'
    return json.loads(raw.decode('utf-8') or '{}')


def get_card_path_by_id(distill_id: str):
    index = load_index()
    for item in index.get('cards', []):
        if item.get('id') == distill_id:
            card_path = item.get('card_path') or f"cards/{distill_id}.json"
            item['card_path'] = card_path
            return index, item, ROOT / card_path
    return None, None, None


def collect_asset_paths(card):
    paths = []
    thumb = card.get('thumb')
    if thumb:
        paths.append(thumb)
    for p in card.get('source_images', []) or []:
        if p:
            paths.append(p)
    la = card.get('layout_analysis') or {}
    skeleton = la.get('skeleton_image')
    if skeleton:
        paths.append(skeleton)
    skeleton_png = la.get('skeleton_png')
    if skeleton_png:
        paths.append(skeleton_png)
    return sorted(set(paths))


def asset_is_referenced_elsewhere(index_cards, deleted_id, rel_path):
    for item in index_cards:
        if item.get('id') == deleted_id:
            continue
        try:
            card = read_json(ROOT / item['card_path'])
        except Exception:
            continue
        if rel_path == card.get('thumb'):
            return True
        if rel_path in (card.get('source_images', []) or []):
            return True
        skeleton = (card.get('layout_analysis') or {}).get('skeleton_image')
        if rel_path == skeleton:
            return True
    return False


# --- Skeleton regeneration (SVG + PNG) ---

# Import shared functions from layout_analyzer to avoid code duplication
sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_analyzer import generate_skeleton_svg, _svg_to_png_file


def _regenerate_skeleton(distill_id, layout):
    """Rebuild SVG + PNG from current layout elements.

    Updates layout['skeleton_image'] (SVG) and layout['skeleton_png'] (PNG) in place.
    Caller is responsible for persisting the updated layout to disk after calling this.
    Returns True when PNG generation succeeds, else False.
    """
    elements = layout.get('elements', [])
    if not elements:
        return False
    title = layout.get('_title', distill_id)
    svg_rel = layout.get('skeleton_image', '')
    if not svg_rel:
        num = distill_id[-3:] if distill_id else '000'
        svg_rel = f"site/assets/posters/poster-skeleton-{num}.svg"
    svg_path = ROOT / svg_rel
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg = generate_skeleton_svg(elements, title)
    svg_path.write_text(svg, encoding='utf-8')
    # Generate PNG companion (named by distill_id for stable references)
    png_dir = ROOT / 'site' / 'assets' / 'skeletons'
    png_dir.mkdir(parents=True, exist_ok=True)
    png_name = f"{distill_id}.png"
    png_path = png_dir / png_name
    png_ok = _svg_to_png_file(svg_path, png_path)
    if png_ok:
        layout['skeleton_png'] = f"site/assets/skeletons/{png_name}"
    else:
        layout['skeleton_png'] = ''
        print(f'[warn] failed to regenerate skeleton PNG for {distill_id} from {svg_rel}')
    return png_ok


# --- HTTP Handler ---

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs for cleaner terminal

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        super().end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/api/auth/me':
            user, _ = current_user(self)
            if user:
                return json_response(self, 200, {'ok': True, 'user': {'username': user['username'], 'role': user.get('role', 'pending')}})
            return json_response(self, 401, {'ok': False})

        if path == '/api/library':
            user, _ = current_user(self)
            if not user:
                return json_response(self, 401, {'ok': False, 'error': 'UNAUTHORIZED'})
            index = load_index()
            cards = []
            for item in index.get('cards', []):
                card_path = item.get('card_path') or f"cards/{item.get('id')}.json"
                try:
                    card = read_json(ROOT / card_path)
                    normalize_card_source_images(card)
                    cards.append({
                        'id': item.get('id'),
                        'slug': item.get('slug', item.get('id')),
                        'title': card.get('title', ''),
                        'subtitle': card.get('subtitle', ''),
                        'summary': card.get('summary', ''),
                        'tags': card.get('tags', []),
                        'status': card.get('status', 'draft'),
                        'distill_version': card.get('distill_version', 'v2'),
                        'thumb': card.get('thumb', ''),
                        'source_images': card.get('source_images', []),
                        'layout_analysis': {
                            'status': (card.get('layout_analysis') or {}).get('status', 'pending'),
                            'skeleton_image': (card.get('layout_analysis') or {}).get('skeleton_image', ''),
                            'element_count': len((card.get('layout_analysis') or {}).get('elements', [])),
                            'analyzed_at': (card.get('layout_analysis') or {}).get('analyzed_at', ''),
                        },
                    })
                except Exception:
                    cards.append(item)
            return json_response(self, 200, {'ok': True, 'cards': cards})

        if path.startswith('/api/card/'):
            user, _ = current_user(self)
            if not user:
                return json_response(self, 401, {'ok': False, 'error': 'UNAUTHORIZED'})
            distill_id = unquote(path.split('/api/card/', 1)[1])
            _, _, card_path = get_card_path_by_id(distill_id)
            if not card_path or not card_path.exists():
                return json_response(self, 404, {'ok': False, 'error': 'CARD_NOT_FOUND'})
            card = read_json(card_path)
            normalize_card_source_images(card)
            return json_response(self, 200, {'ok': True, 'card': card})

        if path == '/api/admin/users':
            admin, _ = require_user(self, roles={'admin'})
            if not admin:
                return
            users_data = load_users()
            return json_response(self, 200, {'ok': True, 'users': users_data.get('users', [])})

        # Serve static files (whitelisted directory prefixes)
        stripped = path.lstrip('/')
        if any(stripped.startswith(prefix) for prefix in ALLOWED_STATIC_PREFIXES):
            return self._serve_static(stripped)
        if path == '/' or path == '/index.html':
            return self._serve_static('site/index.html')

        return json_response(self, 404, {'ok': False, 'error': 'NOT_FOUND'})

    def do_POST(self):
        path = urlparse(self.path).path
        body = safe_read_body(self)

        if path == '/api/auth/register':
            username = (body.get('username') or '').strip()
            password = body.get('password') or ''
            if len(username) < 2 or len(password) < 6:
                return json_response(self, 400, {'ok': False, 'error': 'INVALID_INPUT'})
            users_data = load_users()
            users = users_data.get('users', [])
            if any(u.get('username') == username for u in users):
                return json_response(self, 409, {'ok': False, 'error': 'USERNAME_EXISTS'})
            role = 'admin' if len(users) == 0 else 'pending'
            salt = secrets.token_hex(16)
            users.append({
                'username': username, 'salt': salt,
                'password_hash': hash_password(password, salt),
                'role': role, 'created_at': now_ts()
            })
            users_data['users'] = users
            save_users(users_data)
            token = create_session(username)
            return json_response(self, 200, {'ok': True, 'registered': True, 'role': role}, set_cookie=token)

        if path == '/api/auth/login':
            username = (body.get('username') or '').strip()
            password = body.get('password') or ''
            user = find_user(username)
            if not verify_password(user, password):
                return json_response(self, 401, {'ok': False, 'error': 'INVALID_CREDENTIALS'})
            token = create_session(username)
            return json_response(self, 200, {'ok': True, 'role': user.get('role', 'pending')}, set_cookie=token)

        if path == '/api/auth/logout':
            _, token = current_user(self)
            if token:
                delete_session(token)
            return json_response(self, 200, {'ok': True}, clear_cookie=True)

        if path.startswith('/api/card/') and path.endswith('/analyze'):
            user, _ = require_user(self, roles={'admin', 'editor'})
            if not user:
                return
            distill_id = unquote(path.split('/api/card/', 1)[1].split('/analyze')[0])
            try:
                sys_path = str(Path(__file__).resolve().parent)
                if sys_path not in sys.path:
                    sys.path.insert(0, sys_path)
                from layout_analyzer import analyze_card
                result = analyze_card(distill_id)
                return json_response(self, 200 if result.get('ok') else 500, result)
            except Exception as e:
                return json_response(self, 500, {'ok': False, 'error': 'ANALYSIS_FAILED', 'detail': str(e)})

        if path.startswith('/api/card/') and path.endswith('/regenerate-skeleton'):
            user, _ = require_user(self, roles={'admin', 'editor'})
            if not user:
                return
            distill_id = unquote(path.split('/api/card/', 1)[1].split('/regenerate-skeleton')[0])
            _, _, card_path = get_card_path_by_id(distill_id)
            if not card_path or not card_path.exists():
                return json_response(self, 404, {'ok': False, 'error': 'CARD_NOT_FOUND'})
            try:
                card = read_json(card_path)
                la = card.get('layout_analysis') or {}
                elements = la.get('elements') or []
                if not elements:
                    return json_response(self, 400, {'ok': False, 'error': 'NO_ELEMENTS', 'message': '卡片没有版式元素，请先执行蒸馏分析'})
                title = card.get('title', distill_id)
                la['_title'] = title
                _regenerate_skeleton(distill_id, la)
                # Persist updated skeleton_png path to card
                card['layout_analysis'] = la
                write_json(card_path, card)
                return json_response(self, 200, {'ok': True, 'id': distill_id, 'skeleton_image': la.get('skeleton_image', ''), 'skeleton_png': la.get('skeleton_png', '')})
            except Exception as e:
                return json_response(self, 500, {'ok': False, 'error': 'REGENERATE_FAILED', 'detail': str(e)})

        if path == '/api/batch/analyze':
            user, _ = require_user(self, roles={'admin', 'editor'})
            if not user:
                return
            ids = body.get('ids') or []
            if not ids:
                return json_response(self, 400, {'ok': False, 'error': 'NO_IDS'})
            try:
                sys_path = str(Path(__file__).resolve().parent)
                if sys_path not in sys.path:
                    sys.path.insert(0, sys_path)
                from layout_analyzer import analyze_card
            except Exception as e:
                return json_response(self, 500, {'ok': False, 'error': 'IMPORT_FAILED', 'detail': str(e)})
            results = []
            for distill_id in ids:
                try:
                    result = analyze_card(distill_id)
                    results.append({'id': distill_id, 'ok': result.get('ok', False), 'error': result.get('error')})
                except Exception as e:
                    results.append({'id': distill_id, 'ok': False, 'error': str(e)})
            return json_response(self, 200, {'ok': True, 'results': results})

        if path.startswith('/api/admin/users/'):
            admin, _ = require_user(self, roles={'admin'})
            if not admin:
                return
            username = unquote(path.split('/api/admin/users/', 1)[1])
            role = (body.get('role') or '').strip()
            if role not in {'admin', 'editor', 'viewer', 'pending'}:
                return json_response(self, 400, {'ok': False, 'error': 'INVALID_ROLE'})
            users_data = load_users()
            for user in users_data.get('users', []):
                if user.get('username') == username:
                    user['role'] = role
                    save_users(users_data)
                    return json_response(self, 200, {'ok': True})
            return json_response(self, 404, {'ok': False, 'error': 'USER_NOT_FOUND'})

        return json_response(self, 404, {'ok': False, 'error': 'NOT_FOUND'})

    def do_PATCH(self):
        path = urlparse(self.path).path
        body = safe_read_body(self)

        if path.startswith('/api/card/') and '/layout' in path:
            user, _ = require_user(self, roles={'admin', 'editor'})
            if not user:
                return
            distill_id = unquote(path.split('/api/card/', 1)[1].split('/layout')[0])
            _, _, card_path = get_card_path_by_id(distill_id)
            if not card_path or not card_path.exists():
                return json_response(self, 404, {'ok': False, 'error': 'CARD_NOT_FOUND'})
            card = read_json(card_path)
            layout = body.get('layout_analysis')
            if not layout or not isinstance(layout, dict):
                return json_response(self, 400, {'ok': False, 'error': 'INVALID_LAYOUT'})
            layout['status'] = 'ready'
            layout['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())
            layout['analyzer_model'] = layout.get('analyzer_model', 'manual-edit')
            card['layout_analysis'] = layout
            write_json(card_path, card)
            # Regenerate skeleton (SVG + PNG)
            card_title = card.get('title', distill_id)
            layout['_title'] = card_title
            png_ok = _regenerate_skeleton(distill_id, layout)
            # Persist updated skeleton_png path to card
            card['layout_analysis'] = layout
            write_json(card_path, card)
            return json_response(self, 200, {'ok': True, 'id': distill_id, 'skeleton_png': layout.get('skeleton_png', ''), 'skeleton_png_ok': png_ok})

        if path.startswith('/api/card/'):
            user, _ = require_user(self, roles={'admin', 'editor'})
            if not user:
                return
            distill_id = unquote(path.split('/api/card/', 1)[1])
            _, _, card_path = get_card_path_by_id(distill_id)
            if not card_path or not card_path.exists():
                return json_response(self, 404, {'ok': False, 'error': 'CARD_NOT_FOUND'})
            card = read_json(card_path)
            for key in EDITABLE_STRING_FIELDS:
                if key in body:
                    val = body[key]
                    if isinstance(val, str):
                        card[key] = val.strip()
            for key in EDITABLE_ARRAY_FIELDS:
                if key in body:
                    val = body[key]
                    if isinstance(val, list):
                        card[key] = [s.strip() for s in val if isinstance(s, str) and s.strip()]
            normalize_card_source_images(card)
            write_json(card_path, card)
            return json_response(self, 200, {'ok': True, 'id': distill_id})

        return json_response(self, 404, {'ok': False, 'error': 'NOT_FOUND'})

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith('/api/card/'):
            admin, _ = require_user(self, roles={'admin'})
            if not admin:
                return
            distill_id = unquote(path.split('/api/card/', 1)[1])
            index, item, card_path = get_card_path_by_id(distill_id)
            if not card_path or not card_path.exists():
                return json_response(self, 404, {'ok': False, 'error': 'CARD_NOT_FOUND'})
            # Delete assets that are not referenced by other cards
            try:
                card = read_json(card_path)
                for rel_path in collect_asset_paths(card):
                    asset_path = ROOT / rel_path
                    if asset_path.exists() and not asset_is_referenced_elsewhere(index.get('cards', []), distill_id, rel_path):
                        asset_path.unlink()
            except Exception:
                pass
            card_path.unlink(missing_ok=True)
            # Remove from index
            index['cards'] = [c for c in index.get('cards', []) if c.get('id') != distill_id]
            write_json(INDEX, index)
            return json_response(self, 200, {'ok': True, 'deleted': distill_id})
        return json_response(self, 404, {'ok': False, 'error': 'NOT_FOUND'})

    def _serve_static(self, rel_path):
        rel_path = unquote(rel_path)
        full_path = ROOT / rel_path
        if not full_path.exists() or not full_path.is_file():
            return json_response(self, 404, {'ok': False, 'error': 'FILE_NOT_FOUND'})
        ct, _ = mimetypes.guess_type(str(full_path))
        ct = ct or 'application/octet-stream'
        data = full_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', str(len(data)))
        # HTML files should never be cached
        if ct and 'html' in ct:
            self.send_header('Cache-Control', 'no-cache, no-store')
        else:
            self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(data)


def main():
    ensure_store()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f'Distill Library v3 server running at http://{HOST}:{PORT}')
    print(f'Open http://{HOST}:{PORT}/site/index.html in your browser')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.shutdown()


if __name__ == '__main__':
    main()
