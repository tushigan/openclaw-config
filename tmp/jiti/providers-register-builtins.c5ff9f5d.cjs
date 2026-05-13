"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.registerBuiltInApiProviders = registerBuiltInApiProviders;exports.resetApiProviders = resetApiProviders;exports.setBedrockProviderModule = setBedrockProviderModule;exports.streamSimpleOpenAIResponses = exports.streamSimpleOpenAICompletions = exports.streamSimpleOpenAICodexResponses = exports.streamSimpleMistral = exports.streamSimpleGoogleVertex = exports.streamSimpleGoogle = exports.streamSimpleAzureOpenAIResponses = exports.streamSimpleAnthropic = exports.streamOpenAIResponses = exports.streamOpenAICompletions = exports.streamOpenAICodexResponses = exports.streamMistral = exports.streamGoogleVertex = exports.streamGoogle = exports.streamAzureOpenAIResponses = exports.streamAnthropic = void 0;var _apiRegistry = require("../api-registry.js");
var _eventStream = require("../utils/event-stream.js");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
const importNodeOnlyProvider = (specifier) => ((specifier) => new Promise((r) => r(`${specifier}`)).then((s) => jitiImport(s).then((m) => _interopRequireWildcard(m))))(specifier);
let anthropicProviderModulePromise;
let azureOpenAIResponsesProviderModulePromise;
let googleProviderModulePromise;
let googleVertexProviderModulePromise;
let mistralProviderModulePromise;
let openAICodexResponsesProviderModulePromise;
let openAICompletionsProviderModulePromise;
let openAIResponsesProviderModulePromise;
let bedrockProviderModuleOverride;
let bedrockProviderModulePromise;
function setBedrockProviderModule(module) {
  bedrockProviderModuleOverride = {
    stream: module.streamBedrock,
    streamSimple: module.streamSimpleBedrock
  };
}
function forwardStream(target, source) {
  (async () => {
    for await (const event of source) {
      target.push(event);
    }
    target.end();
  })();
}
function createLazyLoadErrorMessage(model, error) {
  return {
    role: "assistant",
    content: [],
    api: model.api,
    provider: model.provider,
    model: model.id,
    usage: {
      input: 0,
      output: 0,
      cacheRead: 0,
      cacheWrite: 0,
      totalTokens: 0,
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 }
    },
    stopReason: "error",
    errorMessage: error instanceof Error ? error.message : String(error),
    timestamp: Date.now()
  };
}
function createLazyStream(loadModule) {
  return (model, context, options) => {
    const outer = new _eventStream.AssistantMessageEventStream();
    loadModule().
    then((module) => {
      const inner = module.stream(model, context, options);
      forwardStream(outer, inner);
    }).
    catch((error) => {
      const message = createLazyLoadErrorMessage(model, error);
      outer.push({ type: "error", reason: "error", error: message });
      outer.end(message);
    });
    return outer;
  };
}
function createLazySimpleStream(loadModule) {
  return (model, context, options) => {
    const outer = new _eventStream.AssistantMessageEventStream();
    loadModule().
    then((module) => {
      const inner = module.streamSimple(model, context, options);
      forwardStream(outer, inner);
    }).
    catch((error) => {
      const message = createLazyLoadErrorMessage(model, error);
      outer.push({ type: "error", reason: "error", error: message });
      outer.end(message);
    });
    return outer;
  };
}
function loadAnthropicProviderModule() {
  anthropicProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./anthropic.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamAnthropic,
      streamSimple: provider.streamSimpleAnthropic
    };
  });
  return anthropicProviderModulePromise;
}
function loadAzureOpenAIResponsesProviderModule() {
  azureOpenAIResponsesProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./azure-openai-responses.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamAzureOpenAIResponses,
      streamSimple: provider.streamSimpleAzureOpenAIResponses
    };
  });
  return azureOpenAIResponsesProviderModulePromise;
}
function loadGoogleProviderModule() {
  googleProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./google.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamGoogle,
      streamSimple: provider.streamSimpleGoogle
    };
  });
  return googleProviderModulePromise;
}
function loadGoogleVertexProviderModule() {
  googleVertexProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./google-vertex.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamGoogleVertex,
      streamSimple: provider.streamSimpleGoogleVertex
    };
  });
  return googleVertexProviderModulePromise;
}
function loadMistralProviderModule() {
  mistralProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./mistral.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamMistral,
      streamSimple: provider.streamSimpleMistral
    };
  });
  return mistralProviderModulePromise;
}
function loadOpenAICodexResponsesProviderModule() {
  openAICodexResponsesProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./openai-codex-responses.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamOpenAICodexResponses,
      streamSimple: provider.streamSimpleOpenAICodexResponses
    };
  });
  return openAICodexResponsesProviderModulePromise;
}
function loadOpenAICompletionsProviderModule() {
  openAICompletionsProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./openai-completions.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamOpenAICompletions,
      streamSimple: provider.streamSimpleOpenAICompletions
    };
  });
  return openAICompletionsProviderModulePromise;
}
function loadOpenAIResponsesProviderModule() {
  openAIResponsesProviderModulePromise ||= Promise.resolve().then(() => jitiImport("./openai-responses.js").then((m) => _interopRequireWildcard(m))).then((module) => {
    const provider = module;
    return {
      stream: provider.streamOpenAIResponses,
      streamSimple: provider.streamSimpleOpenAIResponses
    };
  });
  return openAIResponsesProviderModulePromise;
}
function loadBedrockProviderModule() {
  if (bedrockProviderModuleOverride) {
    return Promise.resolve(bedrockProviderModuleOverride);
  }
  bedrockProviderModulePromise ||= importNodeOnlyProvider("./amazon-bedrock.js").then((module) => {
    const provider = module;
    return {
      stream: provider.streamBedrock,
      streamSimple: provider.streamSimpleBedrock
    };
  });
  return bedrockProviderModulePromise;
}
const streamAnthropic = exports.streamAnthropic = createLazyStream(loadAnthropicProviderModule);
const streamSimpleAnthropic = exports.streamSimpleAnthropic = createLazySimpleStream(loadAnthropicProviderModule);
const streamAzureOpenAIResponses = exports.streamAzureOpenAIResponses = createLazyStream(loadAzureOpenAIResponsesProviderModule);
const streamSimpleAzureOpenAIResponses = exports.streamSimpleAzureOpenAIResponses = createLazySimpleStream(loadAzureOpenAIResponsesProviderModule);
const streamGoogle = exports.streamGoogle = createLazyStream(loadGoogleProviderModule);
const streamSimpleGoogle = exports.streamSimpleGoogle = createLazySimpleStream(loadGoogleProviderModule);
const streamGoogleVertex = exports.streamGoogleVertex = createLazyStream(loadGoogleVertexProviderModule);
const streamSimpleGoogleVertex = exports.streamSimpleGoogleVertex = createLazySimpleStream(loadGoogleVertexProviderModule);
const streamMistral = exports.streamMistral = createLazyStream(loadMistralProviderModule);
const streamSimpleMistral = exports.streamSimpleMistral = createLazySimpleStream(loadMistralProviderModule);
const streamOpenAICodexResponses = exports.streamOpenAICodexResponses = createLazyStream(loadOpenAICodexResponsesProviderModule);
const streamSimpleOpenAICodexResponses = exports.streamSimpleOpenAICodexResponses = createLazySimpleStream(loadOpenAICodexResponsesProviderModule);
const streamOpenAICompletions = exports.streamOpenAICompletions = createLazyStream(loadOpenAICompletionsProviderModule);
const streamSimpleOpenAICompletions = exports.streamSimpleOpenAICompletions = createLazySimpleStream(loadOpenAICompletionsProviderModule);
const streamOpenAIResponses = exports.streamOpenAIResponses = createLazyStream(loadOpenAIResponsesProviderModule);
const streamSimpleOpenAIResponses = exports.streamSimpleOpenAIResponses = createLazySimpleStream(loadOpenAIResponsesProviderModule);
const streamBedrockLazy = createLazyStream(loadBedrockProviderModule);
const streamSimpleBedrockLazy = createLazySimpleStream(loadBedrockProviderModule);
function registerBuiltInApiProviders() {
  (0, _apiRegistry.registerApiProvider)({
    api: "anthropic-messages",
    stream: streamAnthropic,
    streamSimple: streamSimpleAnthropic
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "openai-completions",
    stream: streamOpenAICompletions,
    streamSimple: streamSimpleOpenAICompletions
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "mistral-conversations",
    stream: streamMistral,
    streamSimple: streamSimpleMistral
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "openai-responses",
    stream: streamOpenAIResponses,
    streamSimple: streamSimpleOpenAIResponses
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "azure-openai-responses",
    stream: streamAzureOpenAIResponses,
    streamSimple: streamSimpleAzureOpenAIResponses
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "openai-codex-responses",
    stream: streamOpenAICodexResponses,
    streamSimple: streamSimpleOpenAICodexResponses
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "google-generative-ai",
    stream: streamGoogle,
    streamSimple: streamSimpleGoogle
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "google-vertex",
    stream: streamGoogleVertex,
    streamSimple: streamSimpleGoogleVertex
  });
  (0, _apiRegistry.registerApiProvider)({
    api: "bedrock-converse-stream",
    stream: streamBedrockLazy,
    streamSimple: streamSimpleBedrockLazy
  });
}
function resetApiProviders() {
  (0, _apiRegistry.clearApiProviders)();
  registerBuiltInApiProviders();
}
registerBuiltInApiProviders(); /* v9-51dd13ca0f654b88 */
