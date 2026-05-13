"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.r = exports.o = exports.n = exports.i = exports.a = void 0;exports.s = isOperatorScope;exports.t = void 0; //#region src/gateway/operator-scopes.ts
const ADMIN_SCOPE = exports.t = "operator.admin";
const READ_SCOPE = exports.i = "operator.read";
const WRITE_SCOPE = exports.o = "operator.write";
const APPROVALS_SCOPE = exports.n = "operator.approvals";
const PAIRING_SCOPE = exports.r = "operator.pairing";
const TALK_SECRETS_SCOPE = exports.a = "operator.talk.secrets";
const KNOWN_OPERATOR_SCOPES = new Set([
ADMIN_SCOPE,
READ_SCOPE,
WRITE_SCOPE,
APPROVALS_SCOPE,
PAIRING_SCOPE,
TALK_SECRETS_SCOPE]
);
function isOperatorScope(value) {
  return typeof value === "string" && KNOWN_OPERATOR_SCOPES.has(value);
}
//#endregion /* v9-c2d1735ab2e06254 */
