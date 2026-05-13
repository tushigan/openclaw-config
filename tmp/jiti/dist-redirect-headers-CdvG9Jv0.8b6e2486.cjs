"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = retainSafeHeadersForCrossOriginRedirect;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _fetchHeadersDrgi2oEU = require("./fetch-headers-Drgi2oEU.js");
//#region src/infra/net/redirect-headers.ts
const CROSS_ORIGIN_REDIRECT_SAFE_HEADERS = new Set([
"accept",
"accept-encoding",
"accept-language",
"cache-control",
"content-language",
"content-type",
"if-match",
"if-modified-since",
"if-none-match",
"if-unmodified-since",
"pragma",
"range",
"user-agent"]
);
function retainSafeHeadersForCrossOriginRedirect(headers) {
  if (!headers) return headers;
  const incoming = new Headers((0, _fetchHeadersDrgi2oEU.t)(headers));
  const safeHeaders = {};
  for (const [key, value] of incoming.entries()) if (CROSS_ORIGIN_REDIRECT_SAFE_HEADERS.has((0, _stringCoerceBje8XVt.a)(key))) safeHeaders[key] = value;
  return safeHeaders;
}
//#endregion /* v9-25c616065f35e268 */
