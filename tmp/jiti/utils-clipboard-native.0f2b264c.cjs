"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.clipboard = void 0;var _module = require("module");
const _require = (0, _module.createRequire)("file:///opt/homebrew/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/dist/utils/clipboard-native.js");
let clipboard = exports.clipboard = null;
const hasDisplay = process.platform !== "linux" || Boolean(process.env.DISPLAY || process.env.WAYLAND_DISPLAY);
if (!process.env.TERMUX_VERSION && hasDisplay) {
  try {
    exports.clipboard = clipboard = _require("@mariozechner/clipboard");
  }
  catch {
    exports.clipboard = clipboard = null;
  }
} /* v9-c2e80685108936fa */
