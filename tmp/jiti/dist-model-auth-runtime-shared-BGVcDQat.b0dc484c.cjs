"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveAwsSdkEnvVarName;exports.t = requireApiKey;var _normalizeSecretInputG30DI_5w = require("./normalize-secret-input-G30DI_5w.js");
//#region src/agents/model-auth-runtime-shared.ts
const AWS_BEARER_ENV = "AWS_BEARER_TOKEN_BEDROCK";
const AWS_ACCESS_KEY_ENV = "AWS_ACCESS_KEY_ID";
const AWS_SECRET_KEY_ENV = "AWS_SECRET_ACCESS_KEY";
const AWS_PROFILE_ENV = "AWS_PROFILE";
function resolveAwsSdkEnvVarName(env = process.env) {
  if (env[AWS_BEARER_ENV]?.trim()) return AWS_BEARER_ENV;
  if (env[AWS_ACCESS_KEY_ENV]?.trim() && env[AWS_SECRET_KEY_ENV]?.trim()) return AWS_ACCESS_KEY_ENV;
  if (env[AWS_PROFILE_ENV]?.trim()) return AWS_PROFILE_ENV;
}
function requireApiKey(auth, provider) {
  const key = (0, _normalizeSecretInputG30DI_5w.n)(auth.apiKey);
  if (key) return key;
  throw new Error(`No API key resolved for provider "${provider}" (auth mode: ${auth.mode}).`);
}
//#endregion /* v9-fce98ea2264b9687 */
