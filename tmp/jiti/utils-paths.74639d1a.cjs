"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.canonicalizePath = canonicalizePath;exports.isLocalPath = isLocalPath;var _nodeFs = require("node:fs");
/**
 * Resolve a path to its canonical (real) form, following symlinks.
 * Falls back to the raw path if resolution fails (e.g. the target does
 * not exist yet), so that callers never crash on missing filesystem
 * entries.
 */
function canonicalizePath(path) {
  try {
    return (0, _nodeFs.realpathSync)(path);
  }
  catch {
    return path;
  }
}
/**
 * Returns true if the value is NOT a package source (npm:, git:, etc.)
 * or a URL protocol. Bare names and relative paths without ./ prefix
 * are considered local.
 */
function isLocalPath(value) {
  const trimmed = value.trim();
  // Known non-local prefixes
  if (trimmed.startsWith("npm:") ||
  trimmed.startsWith("git:") ||
  trimmed.startsWith("github:") ||
  trimmed.startsWith("http:") ||
  trimmed.startsWith("https:") ||
  trimmed.startsWith("ssh:")) {
    return false;
  }
  return true;
} /* v9-f80b8e95dc2d0faf */
