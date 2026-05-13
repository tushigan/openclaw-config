"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = isAutoLinkedFileRef;exports.t = void 0;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
const FILE_REF_EXTENSIONS_WITH_TLD = exports.t = new Set([
"md",
"go",
"py",
"pl",
"sh",
"am",
"at",
"be",
"cc"]
);
function isAutoLinkedFileRef(href, label) {
  if (href.replace(/^https?:\/\//i, "") !== label) return false;
  const dotIndex = label.lastIndexOf(".");
  if (dotIndex < 1) return false;
  const ext = (0, _stringCoerceBje8XVt.a)(label.slice(dotIndex + 1));
  if (!FILE_REF_EXTENSIONS_WITH_TLD.has(ext)) return false;
  const segments = label.split("/");
  if (segments.length > 1) {
    for (let i = 0; i < segments.length - 1; i += 1) if (segments[i]?.includes(".")) return false;
  }
  return true;
}
//#endregion /* v9-a2c9cd8c87433eea */
