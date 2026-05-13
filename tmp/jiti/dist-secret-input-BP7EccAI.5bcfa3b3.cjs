"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = buildSecretInputArraySchema;exports.r = buildSecretInputSchema;exports.t = buildOptionalSecretInputSchema;var _typesSecretsCL51SR4g = require("./types.secrets-CL51SR4g.js");
var _refContractFVeYRZYq = require("./ref-contract-FVeYRZYq.js");
var _zodSchemaSensitive4zM6OUv = require("./zod-schema.sensitive-4zM6OUv7.js");
var _zod = require("zod");
//#region src/plugin-sdk/secret-input-schema.ts
function buildSecretInputSchema() {
  return secretInputSchema;
}
const providerSchema = _zod.z.string().regex(_refContractFVeYRZYq.r, "Secret reference provider must match /^[a-z][a-z0-9_-]{0,63}$/ (example: \"default\").");
const secretInputSchema = _zod.z.union([_zod.z.string(), _zod.z.discriminatedUnion("source", [
_zod.z.object({
  source: _zod.z.literal("env"),
  provider: providerSchema,
  id: _zod.z.string().regex(_typesSecretsCL51SR4g.n, "Env secret reference id must match /^[A-Z][A-Z0-9_]{0,127}$/ (example: \"OPENAI_API_KEY\").")
}),
_zod.z.object({
  source: _zod.z.literal("file"),
  provider: providerSchema,
  id: _zod.z.string().refine(_refContractFVeYRZYq.s, "File secret reference id must be an absolute JSON pointer (example: \"/providers/openai/apiKey\"), or \"value\" for singleValue mode.")
}),
_zod.z.object({
  source: _zod.z.literal("exec"),
  provider: providerSchema,
  id: _zod.z.string().refine(_refContractFVeYRZYq.o, (0, _refContractFVeYRZYq.a)())
})]
)]).register(_zodSchemaSensitive4zM6OUv.t);
//#endregion
//#region src/plugin-sdk/secret-input.ts
/** Optional version of the shared secret-input schema. */
function buildOptionalSecretInputSchema() {
  return buildSecretInputSchema().optional();
}
/** Array version of the shared secret-input schema. */
function buildSecretInputArraySchema() {
  return _zod.z.array(buildSecretInputSchema());
}
//#endregion /* v9-07865b52ef0b7874 */
