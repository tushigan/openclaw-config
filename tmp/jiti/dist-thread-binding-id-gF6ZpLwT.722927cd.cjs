"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolveThreadBindingConversationIdFromBindingId;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
//#region src/channels/thread-binding-id.ts
function resolveThreadBindingConversationIdFromBindingId(params) {
  const bindingId = (0, _stringCoerceBje8XVt.c)(params.bindingId);
  if (!bindingId) return;
  const prefix = `${params.accountId}:`;
  if (!bindingId.startsWith(prefix)) return;
  return (0, _stringCoerceBje8XVt.c)(bindingId.slice(prefix.length)) || void 0;
}
//#endregion /* v9-bba9d68db7af0970 */
