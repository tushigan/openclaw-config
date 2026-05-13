"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = sanitizeGoogleAssistantFirstOrdering;exports.t = isGemma4ModelId;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
//#region src/shared/google-turn-ordering.ts
const GOOGLE_TURN_ORDER_BOOTSTRAP_TEXT = "(session bootstrap)";
function sanitizeGoogleAssistantFirstOrdering(messages) {
  const first = messages[0];
  const role = first?.role;
  const content = first?.content;
  if (role === "user" && typeof content === "string" && content.trim() === GOOGLE_TURN_ORDER_BOOTSTRAP_TEXT) return messages;
  if (role !== "assistant") return messages;
  return [{
    role: "user",
    content: GOOGLE_TURN_ORDER_BOOTSTRAP_TEXT,
    timestamp: Date.now()
  }, ...messages];
}
//#endregion
//#region src/shared/google-models.ts
function isGemma4ModelId(modelId) {
  const normalized = (0, _stringCoerceBje8XVt.a)(modelId);
  return /(?:^|[/_:-])gemma[-_]?4(?:$|[/_.:-])/.test(normalized);
}
//#endregion /* v9-7a3f810e0e26b4bd */
