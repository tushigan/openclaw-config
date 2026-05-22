"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = writeJsonFileAtomically;exports.t = readJsonFileWithFallback;var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _jsonFilesDPM4MwsB = require("./json-files-DPM4MwsB.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugin-sdk/json-store.ts
/** Read JSON from disk and fall back cleanly when the file is missing or invalid. */
async function readJsonFileWithFallback(filePath, fallback) {
  try {
    const parsed = (0, _utilsD5swhEXt.m)(await _nodeFs.default.promises.readFile(filePath, "utf-8"));
    if (parsed == null) return {
      value: fallback,
      exists: true
    };
    return {
      value: parsed,
      exists: true
    };
  } catch (err) {
    if (err.code === "ENOENT") return {
      value: fallback,
      exists: false
    };
    return {
      value: fallback,
      exists: false
    };
  }
}
/** Write JSON with secure file permissions and atomic replacement semantics. */
async function writeJsonFileAtomically(filePath, value) {
  await (0, _jsonFilesDPM4MwsB.o)(filePath, value, {
    mode: 384,
    trailingNewline: true,
    ensureDirMode: 448
  });
}
//#endregion /* v9-56c73fceaf20f07b */
