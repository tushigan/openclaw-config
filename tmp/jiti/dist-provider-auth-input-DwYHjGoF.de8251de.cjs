"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = normalizeSecretInputModeInput;exports.i = normalizeApiKeyInput;exports.n = ensureApiKeyFromOptionEnvOrPrompt;exports.o = normalizeTokenProviderInput;exports.r = formatApiKeyPreview;exports.s = void 0;exports.t = ensureApiKeyFromEnvOrPrompt;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _modelAuthEnvZyutsTwR = require("./model-auth-env-zyutsTwR.js");
var _providerAuthModeBlaEOjHN = require("./provider-auth-mode-BlaEOjHN.js");
var _providerAuthRefCpXbtPPP = require("./provider-auth-ref-CpXbtPPP.js");
//#region src/plugins/provider-auth-input.ts
const DEFAULT_KEY_PREVIEW = {
  head: 4,
  tail: 4
};
function normalizeApiKeyInput(raw) {
  const trimmed = (0, _stringCoerceBje8XVt.d)(raw) ?? "";
  if (!trimmed) return "";
  const assignmentMatch = trimmed.match(/^(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=\s*(.+)$/);
  const valuePart = assignmentMatch ? assignmentMatch[1].trim() : trimmed;
  const unquoted = valuePart.length >= 2 && (valuePart.startsWith("\"") && valuePart.endsWith("\"") || valuePart.startsWith("'") && valuePart.endsWith("'") || valuePart.startsWith("`") && valuePart.endsWith("`")) ? valuePart.slice(1, -1) : valuePart;
  return (unquoted.endsWith(";") ? unquoted.slice(0, -1) : unquoted).trim();
}
const validateApiKeyInput = (value) => normalizeApiKeyInput(value).length > 0 ? void 0 : "Required";exports.s = validateApiKeyInput;
function formatApiKeyPreview(raw, opts = {}) {
  const trimmed = raw.trim();
  if (!trimmed) return "…";
  const head = opts.head ?? DEFAULT_KEY_PREVIEW.head;
  const tail = opts.tail ?? DEFAULT_KEY_PREVIEW.tail;
  if (trimmed.length <= head + tail) {
    const shortHead = Math.min(2, trimmed.length);
    const shortTail = Math.min(2, trimmed.length - shortHead);
    if (shortTail <= 0) return `${trimmed.slice(0, shortHead)}…`;
    return `${trimmed.slice(0, shortHead)}…${trimmed.slice(-shortTail)}`;
  }
  return `${trimmed.slice(0, head)}…${trimmed.slice(-tail)}`;
}
function normalizeTokenProviderInput(tokenProvider) {
  return (0, _stringCoerceBje8XVt.s)(tokenProvider);
}
function normalizeSecretInputModeInput(secretInputMode) {
  const normalized = (0, _stringCoerceBje8XVt.s)(secretInputMode);
  if (normalized === "plaintext" || normalized === "ref") return normalized;
}
async function maybeApplyApiKeyFromOption(params) {
  const tokenProvider = normalizeTokenProviderInput(params.tokenProvider);
  const expectedProviders = params.expectedProviders.map((provider) => normalizeTokenProviderInput(provider)).filter((provider) => Boolean(provider));
  if (!params.token || !tokenProvider || !expectedProviders.includes(tokenProvider)) return;
  const apiKey = params.normalize(params.token);
  await params.setCredential(apiKey, params.secretInputMode);
  return apiKey;
}
async function ensureApiKeyFromOptionEnvOrPrompt(params) {
  const optionApiKey = await maybeApplyApiKeyFromOption({
    token: params.token,
    tokenProvider: params.tokenProvider,
    secretInputMode: params.secretInputMode,
    expectedProviders: params.expectedProviders,
    normalize: params.normalize,
    setCredential: params.setCredential
  });
  if (optionApiKey) return optionApiKey;
  if (params.noteMessage) await params.prompter.note(params.noteMessage, params.noteTitle);
  return await ensureApiKeyFromEnvOrPrompt({
    config: params.config,
    env: params.env,
    provider: params.provider,
    envLabel: params.envLabel,
    promptMessage: params.promptMessage,
    normalize: params.normalize,
    validate: params.validate,
    prompter: params.prompter,
    secretInputMode: params.secretInputMode,
    setCredential: params.setCredential
  });
}
async function ensureApiKeyFromEnvOrPrompt(params) {
  const selectedMode = await (0, _providerAuthModeBlaEOjHN.t)({
    prompter: params.prompter,
    explicitMode: params.secretInputMode
  });
  const env = params.env ?? process.env;
  const envKey = (0, _modelAuthEnvZyutsTwR.t)(params.provider, env);
  if (selectedMode === "ref") {
    if (typeof params.prompter.select !== "function") {
      const fallback = (0, _providerAuthRefCpXbtPPP.r)({
        config: params.config,
        provider: params.provider,
        preferredEnvVar: envKey?.source ? (0, _providerAuthRefCpXbtPPP.t)(envKey.source) : void 0,
        env
      });
      await params.setCredential(fallback.ref, selectedMode);
      return fallback.resolvedValue;
    }
    const resolved = await (0, _providerAuthRefCpXbtPPP.n)({
      provider: params.provider,
      config: params.config,
      prompter: params.prompter,
      preferredEnvVar: envKey?.source ? (0, _providerAuthRefCpXbtPPP.t)(envKey.source) : void 0,
      env
    });
    await params.setCredential(resolved.ref, selectedMode);
    return resolved.resolvedValue;
  }
  if (envKey && selectedMode === "plaintext") {
    if (await params.prompter.confirm({
      message: `Use existing ${params.envLabel} (${envKey.source}, ${formatApiKeyPreview(envKey.apiKey)})?`,
      initialValue: true
    })) {
      await params.setCredential(envKey.apiKey, selectedMode);
      return envKey.apiKey;
    }
  }
  const key = await params.prompter.text({
    message: params.promptMessage,
    placeholder: "API key",
    validate: params.validate,
    sensitive: true
  });
  const apiKey = params.normalize(key ?? "");
  await params.setCredential(apiKey, selectedMode);
  return apiKey;
}
//#endregion /* v9-2748b1a2be63c2c3 */
