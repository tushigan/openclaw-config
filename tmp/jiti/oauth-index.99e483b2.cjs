"use strict";Object.defineProperty(exports, "__esModule", { value: true });var _exportNames = { getOAuthProvider: true, registerOAuthProvider: true, unregisterOAuthProvider: true, resetOAuthProviders: true, getOAuthProviders: true, getOAuthProviderInfoList: true, refreshOAuthToken: true, getOAuthApiKey: true, anthropicOAuthProvider: true, loginAnthropic: true, refreshAnthropicToken: true, getGitHubCopilotBaseUrl: true, githubCopilotOAuthProvider: true, loginGitHubCopilot: true, normalizeDomain: true, refreshGitHubCopilotToken: true, loginOpenAICodex: true, openaiCodexOAuthProvider: true, refreshOpenAICodexToken: true };Object.defineProperty(exports, "anthropicOAuthProvider", { enumerable: true, get: function () {return _anthropic.anthropicOAuthProvider;} });Object.defineProperty(exports, "getGitHubCopilotBaseUrl", { enumerable: true, get: function () {return _githubCopilot.getGitHubCopilotBaseUrl;} });exports.getOAuthApiKey = getOAuthApiKey;exports.getOAuthProvider = getOAuthProvider;exports.getOAuthProviderInfoList = getOAuthProviderInfoList;exports.getOAuthProviders = getOAuthProviders;Object.defineProperty(exports, "githubCopilotOAuthProvider", { enumerable: true, get: function () {return _githubCopilot.githubCopilotOAuthProvider;} });Object.defineProperty(exports, "loginAnthropic", { enumerable: true, get: function () {return _anthropic.loginAnthropic;} });Object.defineProperty(exports, "loginGitHubCopilot", { enumerable: true, get: function () {return _githubCopilot.loginGitHubCopilot;} });Object.defineProperty(exports, "loginOpenAICodex", { enumerable: true, get: function () {return _openaiCodex.loginOpenAICodex;} });Object.defineProperty(exports, "normalizeDomain", { enumerable: true, get: function () {return _githubCopilot.normalizeDomain;} });Object.defineProperty(exports, "openaiCodexOAuthProvider", { enumerable: true, get: function () {return _openaiCodex.openaiCodexOAuthProvider;} });Object.defineProperty(exports, "refreshAnthropicToken", { enumerable: true, get: function () {return _anthropic.refreshAnthropicToken;} });Object.defineProperty(exports, "refreshGitHubCopilotToken", { enumerable: true, get: function () {return _githubCopilot.refreshGitHubCopilotToken;} });exports.refreshOAuthToken = refreshOAuthToken;Object.defineProperty(exports, "refreshOpenAICodexToken", { enumerable: true, get: function () {return _openaiCodex.refreshOpenAICodexToken;} });exports.registerOAuthProvider = registerOAuthProvider;exports.resetOAuthProviders = resetOAuthProviders;exports.unregisterOAuthProvider = unregisterOAuthProvider;








var _anthropic = require("./anthropic.js");

var _githubCopilot = require("./github-copilot.js");

var _openaiCodex = require("./openai-codex.js");
var _types = require("./types.js");Object.keys(_types).forEach(function (key) {if (key === "default" || key === "__esModule") return;if (Object.prototype.hasOwnProperty.call(_exportNames, key)) return;if (key in exports && exports[key] === _types[key]) return;Object.defineProperty(exports, key, { enumerable: true, get: function () {return _types[key];} });}); /**
 * OAuth credential management for AI providers.
 *
 * This module handles login, token refresh, and credential storage
 * for OAuth-based providers:
 * - Anthropic (Claude Pro/Max)
 * - GitHub Copilot
 */ // Anthropic
// GitHub Copilot
// OpenAI Codex (ChatGPT OAuth)
// ============================================================================
// Provider Registry
// ============================================================================
const BUILT_IN_OAUTH_PROVIDERS = [_anthropic.anthropicOAuthProvider, _githubCopilot.githubCopilotOAuthProvider, _openaiCodex.openaiCodexOAuthProvider];const oauthProviderRegistry = new Map(BUILT_IN_OAUTH_PROVIDERS.map((provider) => [provider.id, provider])); /**
 * Get an OAuth provider by ID
 */
function getOAuthProvider(id) {
  return oauthProviderRegistry.get(id);
}
/**
 * Register a custom OAuth provider
 */
function registerOAuthProvider(provider) {
  oauthProviderRegistry.set(provider.id, provider);
}
/**
 * Unregister an OAuth provider.
 *
 * If the provider is built-in, restores the built-in implementation.
 * Custom providers are removed completely.
 */
function unregisterOAuthProvider(id) {
  const builtInProvider = BUILT_IN_OAUTH_PROVIDERS.find((provider) => provider.id === id);
  if (builtInProvider) {
    oauthProviderRegistry.set(id, builtInProvider);
    return;
  }
  oauthProviderRegistry.delete(id);
}
/**
 * Reset OAuth providers to built-ins.
 */
function resetOAuthProviders() {
  oauthProviderRegistry.clear();
  for (const provider of BUILT_IN_OAUTH_PROVIDERS) {
    oauthProviderRegistry.set(provider.id, provider);
  }
}
/**
 * Get all registered OAuth providers
 */
function getOAuthProviders() {
  return Array.from(oauthProviderRegistry.values());
}
/**
 * @deprecated Use getOAuthProviders() which returns OAuthProviderInterface[]
 */
function getOAuthProviderInfoList() {
  return getOAuthProviders().map((p) => ({
    id: p.id,
    name: p.name,
    available: true
  }));
}
// ============================================================================
// High-level API (uses provider registry)
// ============================================================================
/**
 * Refresh token for any OAuth provider.
 * @deprecated Use getOAuthProvider(id).refreshToken() instead
 */
async function refreshOAuthToken(providerId, credentials) {
  const provider = getOAuthProvider(providerId);
  if (!provider) {
    throw new Error(`Unknown OAuth provider: ${providerId}`);
  }
  return provider.refreshToken(credentials);
}
/**
 * Get API key for a provider from OAuth credentials.
 * Automatically refreshes expired tokens.
 *
 * @returns API key string and updated credentials, or null if no credentials
 * @throws Error if refresh fails
 */
async function getOAuthApiKey(providerId, credentials) {
  const provider = getOAuthProvider(providerId);
  if (!provider) {
    throw new Error(`Unknown OAuth provider: ${providerId}`);
  }
  let creds = credentials[providerId];
  if (!creds) {
    return null;
  }
  // Refresh if expired
  if (Date.now() >= creds.expires) {
    try {
      creds = await provider.refreshToken(creds);
    }
    catch (_error) {
      throw new Error(`Failed to refresh OAuth token for ${providerId}`);
    }
  }
  const apiKey = provider.getApiKey(creds);
  return { newCredentials: creds, apiKey };
} /* v9-9966738aed7dfe38 */
