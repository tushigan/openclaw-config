"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = unsetConfigValueAtPath;exports.n = parseConfigPath;exports.r = setConfigValueAtPath;exports.t = getConfigValueAtPath;var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _prototypeKeysBWjW0VW = require("./prototype-keys-BWjW0VW8.js");
//#region src/config/config-paths.ts
function parseConfigPath(raw) {
  const trimmed = raw.trim();
  if (!trimmed) return {
    ok: false,
    error: "Invalid path. Use dot notation (e.g. foo.bar)."
  };
  const parts = trimmed.split(".").map((part) => part.trim());
  if (parts.some((part) => !part)) return {
    ok: false,
    error: "Invalid path. Use dot notation (e.g. foo.bar)."
  };
  if (parts.some((part) => (0, _prototypeKeysBWjW0VW.t)(part))) return {
    ok: false,
    error: "Invalid path segment."
  };
  return {
    ok: true,
    path: parts
  };
}
function setConfigValueAtPath(root, path, value) {
  let cursor = root;
  for (let idx = 0; idx < path.length - 1; idx += 1) {
    const key = path[idx];
    const next = cursor[key];
    if (!(0, _utilsD5swhEXt.x)(next)) cursor[key] = {};
    cursor = cursor[key];
  }
  cursor[path[path.length - 1]] = value;
}
function unsetConfigValueAtPath(root, path) {
  const stack = [];
  let cursor = root;
  for (let idx = 0; idx < path.length - 1; idx += 1) {
    const key = path[idx];
    const next = cursor[key];
    if (!(0, _utilsD5swhEXt.x)(next)) return false;
    stack.push({
      node: cursor,
      key
    });
    cursor = next;
  }
  const leafKey = path[path.length - 1];
  if (!(leafKey in cursor)) return false;
  delete cursor[leafKey];
  for (let idx = stack.length - 1; idx >= 0; idx -= 1) {
    const { node, key } = stack[idx];
    const child = node[key];
    if ((0, _utilsD5swhEXt.x)(child) && Object.keys(child).length === 0) delete node[key];else
    break;
  }
  return true;
}
function getConfigValueAtPath(root, path) {
  let cursor = root;
  for (const key of path) {
    if (!(0, _utilsD5swhEXt.x)(cursor)) return;
    cursor = cursor[key];
  }
  return cursor;
}
//#endregion /* v9-2304721aad5dab83 */
