"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = isAvatarImageDataUrl;exports.c = isWindowsAbsolutePath;exports.d = resolveAvatarMime;exports.i = isAvatarHttpUrl;exports.l = isWorkspaceRelativeAvatarPath;exports.n = hasAvatarUriScheme;exports.o = isPathWithinRoot;exports.r = isAvatarDataUrl;exports.s = isSupportedLocalAvatarExtension;exports.t = void 0;exports.u = looksLikeAvatarPath;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/shared/avatar-policy.ts
const AVATAR_MAX_BYTES = exports.t = 2 * 1024 * 1024;
const LOCAL_AVATAR_EXTENSIONS = new Set([
".png",
".jpg",
".jpeg",
".gif",
".webp",
".svg"]
);
const AVATAR_MIME_BY_EXT = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".bmp": "image/bmp",
  ".tif": "image/tiff",
  ".tiff": "image/tiff"
};
const AVATAR_DATA_RE = /^data:/i;
const AVATAR_IMAGE_DATA_RE = /^data:image\//i;
const AVATAR_HTTP_RE = /^https?:\/\//i;
const AVATAR_SCHEME_RE = /^[a-z][a-z0-9+.-]*:/i;
const WINDOWS_ABS_RE = /^[a-zA-Z]:[\\/]/;
const AVATAR_PATH_EXT_RE = /\.(png|jpe?g|gif|webp|svg|ico)$/i;
function resolveAvatarMime(filePath) {
  return AVATAR_MIME_BY_EXT[(0, _stringCoerceBje8XVt.a)(_nodePath.default.extname(filePath))] ?? "application/octet-stream";
}
function isAvatarDataUrl(value) {
  return AVATAR_DATA_RE.test(value);
}
function isAvatarImageDataUrl(value) {
  return AVATAR_IMAGE_DATA_RE.test(value);
}
function isAvatarHttpUrl(value) {
  return AVATAR_HTTP_RE.test(value);
}
function hasAvatarUriScheme(value) {
  return AVATAR_SCHEME_RE.test(value);
}
function isWindowsAbsolutePath(value) {
  return WINDOWS_ABS_RE.test(value);
}
function isWorkspaceRelativeAvatarPath(value) {
  if (!value) return false;
  if (value.startsWith("~")) return false;
  if (hasAvatarUriScheme(value) && !isWindowsAbsolutePath(value)) return false;
  return true;
}
function isPathWithinRoot(rootDir, targetPath) {
  const relative = _nodePath.default.relative(rootDir, targetPath);
  if (relative === "") return true;
  return !relative.startsWith("..") && !_nodePath.default.isAbsolute(relative);
}
function looksLikeAvatarPath(value) {
  if (/[\\/]/.test(value)) return true;
  return AVATAR_PATH_EXT_RE.test(value);
}
function isSupportedLocalAvatarExtension(filePath) {
  const ext = (0, _stringCoerceBje8XVt.a)(_nodePath.default.extname(filePath));
  return LOCAL_AVATAR_EXTENSIONS.has(ext);
}
//#endregion /* v9-8b35f20f297cf582 */
