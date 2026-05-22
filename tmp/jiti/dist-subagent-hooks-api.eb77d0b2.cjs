"use strict";Object.defineProperty(exports, "__esModule", { value: true });Object.defineProperty(exports, "handleFeishuSubagentDeliveryTarget", { enumerable: true, get: function () {return _subagentHooksC3UhPVLV.t;} });Object.defineProperty(exports, "handleFeishuSubagentEnded", { enumerable: true, get: function () {return _subagentHooksC3UhPVLV.n;} });Object.defineProperty(exports, "handleFeishuSubagentSpawning", { enumerable: true, get: function () {return _subagentHooksC3UhPVLV.r;} });exports.registerFeishuSubagentHooks = registerFeishuSubagentHooks;var _subagentHooksC3UhPVLV = require("./subagent-hooks-C3UhPVLV.js");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
//#region extensions/feishu/subagent-hooks-api.ts
let feishuSubagentHooksPromise = null;
function loadFeishuSubagentHooksModule() {
  feishuSubagentHooksPromise ??= Promise.resolve().then(() => jitiImport("./subagent-hooks-C3UhPVLV.js").then((m) => _interopRequireWildcard(m))).then((n) => n.i);
  return feishuSubagentHooksPromise;
}
function registerFeishuSubagentHooks(api) {
  api.on("subagent_spawning", async (event, ctx) => {
    const { handleFeishuSubagentSpawning } = await loadFeishuSubagentHooksModule();
    return await handleFeishuSubagentSpawning(event, ctx);
  });
  api.on("subagent_delivery_target", async (event) => {
    const { handleFeishuSubagentDeliveryTarget } = await loadFeishuSubagentHooksModule();
    return handleFeishuSubagentDeliveryTarget(event);
  });
  api.on("subagent_ended", async (event) => {
    const { handleFeishuSubagentEnded } = await loadFeishuSubagentHooksModule();
    handleFeishuSubagentEnded(event);
  });
}
//#endregion /* v9-57abdec0ce1f3eec */
