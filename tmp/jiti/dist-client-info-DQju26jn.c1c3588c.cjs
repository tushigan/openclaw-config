"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = hasGatewayClientCap;exports.c = normalizeGatewayClientName;exports.n = exports.i = void 0;exports.o = normalizeGatewayClientId;exports.r = void 0;exports.s = normalizeGatewayClientMode;exports.t = void 0;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
//#region src/gateway/protocol/client-info.ts
const GATEWAY_CLIENT_IDS = exports.n = {
  WEBCHAT_UI: "webchat-ui",
  CONTROL_UI: "openclaw-control-ui",
  TUI: "openclaw-tui",
  WEBCHAT: "webchat",
  CLI: "cli",
  GATEWAY_CLIENT: "gateway-client",
  MACOS_APP: "openclaw-macos",
  IOS_APP: "openclaw-ios",
  ANDROID_APP: "openclaw-android",
  NODE_HOST: "node-host",
  TEST: "test",
  FINGERPRINT: "fingerprint",
  PROBE: "openclaw-probe"
};
const GATEWAY_CLIENT_NAMES = exports.i = GATEWAY_CLIENT_IDS;
const GATEWAY_CLIENT_MODES = exports.r = {
  WEBCHAT: "webchat",
  CLI: "cli",
  UI: "ui",
  BACKEND: "backend",
  NODE: "node",
  PROBE: "probe",
  TEST: "test"
};
const GATEWAY_CLIENT_CAPS = exports.t = { TOOL_EVENTS: "tool-events" };
const GATEWAY_CLIENT_ID_SET = new Set(Object.values(GATEWAY_CLIENT_IDS));
const GATEWAY_CLIENT_MODE_SET = new Set(Object.values(GATEWAY_CLIENT_MODES));
function normalizeGatewayClientId(raw) {
  const normalized = (0, _stringCoerceBje8XVt.s)(raw);
  if (!normalized) return;
  return GATEWAY_CLIENT_ID_SET.has(normalized) ? normalized : void 0;
}
function normalizeGatewayClientName(raw) {
  return normalizeGatewayClientId(raw);
}
function normalizeGatewayClientMode(raw) {
  const normalized = (0, _stringCoerceBje8XVt.s)(raw);
  if (!normalized) return;
  return GATEWAY_CLIENT_MODE_SET.has(normalized) ? normalized : void 0;
}
function hasGatewayClientCap(caps, cap) {
  if (!Array.isArray(caps)) return false;
  return caps.includes(cap);
}
//#endregion /* v9-1d4b677d3dc51aa2 */
