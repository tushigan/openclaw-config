"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = parseNonNegativeByteSize;exports.r = parseByteSize;exports.t = void 0;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _zodSchemaInstallsBrZxLEMx = require("./zod-schema.installs-BrZxLEMx.js");
var _parseDurationCIsOpJPW = require("./parse-duration-CIsOpJPW.js");
var _zodSchemaAgentRuntimeBgmaoJWM = require("./zod-schema.agent-runtime-BgmaoJWM.js");
var _zodSchemaCoreB8hU4HYi = require("./zod-schema.core-B8hU4HYi.js");
var _zodSchemaSensitive4zM6OUv = require("./zod-schema.sensitive-4zM6OUv7.js");
var _zodSchemaProvidersWhatsappCSmjq_Ez = require("./zod-schema.providers-whatsapp-CSmjq_Ez.js");
var _nodePath = _interopRequireDefault(require("node:path"));
var _zod = require("zod");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/cli/parse-bytes.ts
const UNIT_MULTIPLIERS = {
  b: 1,
  kb: 1024,
  k: 1024,
  mb: 1024 ** 2,
  m: 1024 ** 2,
  gb: 1024 ** 3,
  g: 1024 ** 3,
  tb: 1024 ** 4,
  t: 1024 ** 4
};
function parseByteSize(raw, opts) {
  const trimmed = (0, _stringCoerceBje8XVt.a)((0, _stringCoerceBje8XVt.c)(raw) ?? "");
  if (!trimmed) throw new Error("invalid byte size (empty)");
  const m = /^(\d+(?:\.\d+)?)([a-z]+)?$/.exec(trimmed);
  if (!m) throw new Error(`invalid byte size: ${raw}`);
  const value = Number(m[1]);
  if (!Number.isFinite(value) || value < 0) throw new Error(`invalid byte size: ${raw}`);
  const multiplier = UNIT_MULTIPLIERS[(0, _stringCoerceBje8XVt.a)(m[2] ?? opts?.defaultUnit ?? "b")];
  if (!multiplier) throw new Error(`invalid byte size unit: ${raw}`);
  const bytes = Math.round(value * multiplier);
  if (!Number.isFinite(bytes)) throw new Error(`invalid byte size: ${raw}`);
  return bytes;
}
//#endregion
//#region src/config/control-ui-css.ts
const CSS_WIDTH_KEYWORDS = new Set([
"none",
"min-content",
"max-content"]
);
const CSS_WIDTH_FUNCTIONS = new Set([
"calc",
"clamp",
"fit-content",
"max",
"min"]
);
const CSS_WIDTH_UNITS = new Set([
"ch",
"em",
"rem",
"vh",
"vmax",
"vmin",
"vw",
"px"]
);
const CSS_WIDTH_ALLOWED_CHARS = /^[0-9A-Za-z.%+\-*/(),\s]+$/;
const CSS_WIDTH_IDENTIFIER_RE = /[A-Za-z][A-Za-z0-9-]*/g;
const CSS_WIDTH_SIMPLE_RE = /^(?:\d+(?:\.\d+)?|\.\d+)(?:px|rem|em|ch|vw|vh|vmin|vmax|%)$/i;
const CSS_WIDTH_MAX_LENGTH = 96;
function hasBalancedParentheses(value) {
  let depth = 0;
  for (const char of value) if (char === "(") depth++;else
  if (char === ")") {
    depth--;
    if (depth < 0) return false;
  }
  return depth === 0;
}
function hasAllowedIdentifiers(value) {
  for (const match of value.matchAll(CSS_WIDTH_IDENTIFIER_RE)) {
    const identifier = match[0].toLowerCase();
    if (!CSS_WIDTH_FUNCTIONS.has(identifier) && !CSS_WIDTH_KEYWORDS.has(identifier) && !CSS_WIDTH_UNITS.has(identifier)) return false;
  }
  return true;
}
function normalizeControlUiChatMessageMaxWidth(value) {
  return value.trim().replace(/\s+/g, " ");
}
function isValidControlUiChatMessageMaxWidth(value) {
  const normalized = normalizeControlUiChatMessageMaxWidth(value);
  if (normalized.length === 0 || normalized.length > CSS_WIDTH_MAX_LENGTH) return false;
  if (CSS_WIDTH_KEYWORDS.has(normalized.toLowerCase())) return true;
  if (CSS_WIDTH_SIMPLE_RE.test(normalized)) return true;
  if (!CSS_WIDTH_ALLOWED_CHARS.test(normalized)) return false;
  if (!hasBalancedParentheses(normalized) || !hasAllowedIdentifiers(normalized)) return false;
  return /^(?:calc|clamp|fit-content|max|min)\(.+\)$/i.test(normalized);
}
//#endregion
//#region src/config/byte-size.ts
/**
* Parse an optional byte-size value from config.
* Accepts non-negative numbers or strings like "2mb".
*/
function parseNonNegativeByteSize(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    const int = Math.floor(value);
    return int >= 0 ? int : null;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    try {
      const bytes = parseByteSize(trimmed, { defaultUnit: "b" });
      return bytes >= 0 ? bytes : null;
    } catch {
      return null;
    }
  }
  return null;
}
function isValidNonNegativeByteSizeString(value) {
  return parseNonNegativeByteSize(value) !== null;
}
//#endregion
//#region src/config/zod-schema.agent-defaults.ts
const SilentReplyPolicySchema = _zod.z.union([_zod.z.literal("allow"), _zod.z.literal("disallow")]);
const NonNegativeByteSizeSchema = _zod.z.union([_zod.z.number().int().nonnegative(), _zod.z.string().refine(isValidNonNegativeByteSizeString, "Expected byte size string like 2mb")]);
const OptionalBootstrapFileNameSchema = _zod.z.enum([
"SOUL.md",
"USER.md",
"HEARTBEAT.md",
"IDENTITY.md"]
);
const SilentReplyPolicyConfigSchema = _zod.z.object({
  direct: SilentReplyPolicySchema.optional(),
  group: SilentReplyPolicySchema.optional(),
  internal: SilentReplyPolicySchema.optional()
}).strict();
const SilentReplyRewriteConfigSchema = _zod.z.object({
  direct: _zod.z.boolean().optional(),
  group: _zod.z.boolean().optional(),
  internal: _zod.z.boolean().optional()
}).strict();
const AgentDefaultsSchema = _zod.z.object({
  /** Global default provider params applied to all models before per-model and per-agent overrides. */
  params: _zod.z.record(_zod.z.string(), _zod.z.unknown()).optional(),
  agentRuntime: _zodSchemaAgentRuntimeBgmaoJWM.i,
  embeddedHarness: _zodSchemaAgentRuntimeBgmaoJWM.n,
  model: _zodSchemaAgentRuntimeBgmaoJWM.d.optional(),
  imageModel: _zodSchemaAgentRuntimeBgmaoJWM.d.optional(),
  imageGenerationModel: _zodSchemaAgentRuntimeBgmaoJWM.d.optional(),
  videoGenerationModel: _zodSchemaAgentRuntimeBgmaoJWM.d.optional(),
  musicGenerationModel: _zodSchemaAgentRuntimeBgmaoJWM.d.optional(),
  mediaGenerationAutoProviderFallback: _zod.z.boolean().optional(),
  pdfModel: _zodSchemaAgentRuntimeBgmaoJWM.d.optional(),
  pdfMaxBytesMb: _zod.z.number().positive().optional(),
  pdfMaxPages: _zod.z.number().int().positive().optional(),
  models: _zod.z.record(_zod.z.string(), _zod.z.object({
    alias: _zod.z.string().optional(),
    /** Provider-specific API parameters (e.g., GLM-4.7 thinking mode). */
    params: _zod.z.record(_zod.z.string(), _zod.z.unknown()).optional(),
    /** Enable streaming for this model (default: true, false for Ollama to avoid SDK issue #1205). */
    streaming: _zod.z.boolean().optional()
  }).strict()).optional(),
  workspace: _zod.z.string().optional(),
  skills: _zod.z.array(_zod.z.string()).optional(),
  silentReply: SilentReplyPolicyConfigSchema.optional(),
  silentReplyRewrite: SilentReplyRewriteConfigSchema.optional(),
  repoRoot: _zod.z.string().optional(),
  systemPromptOverride: _zod.z.string().optional(),
  promptOverlays: _zod.z.object({ gpt5: _zod.z.object({ personality: _zod.z.union([
      _zod.z.literal("friendly"),
      _zod.z.literal("on"),
      _zod.z.literal("off")]
      ).optional() }).strict().optional() }).strict().optional(),
  skipBootstrap: _zod.z.boolean().optional(),
  skipOptionalBootstrapFiles: _zod.z.array(OptionalBootstrapFileNameSchema).optional(),
  contextInjection: _zod.z.union([
  _zod.z.literal("always"),
  _zod.z.literal("continuation-skip"),
  _zod.z.literal("never")]
  ).optional(),
  bootstrapMaxChars: _zod.z.number().int().positive().optional(),
  bootstrapTotalMaxChars: _zod.z.number().int().positive().optional(),
  experimental: _zod.z.object({ localModelLean: _zod.z.boolean().optional() }).strict().optional(),
  bootstrapPromptTruncationWarning: _zod.z.union([
  _zod.z.literal("off"),
  _zod.z.literal("once"),
  _zod.z.literal("always")]
  ).optional(),
  userTimezone: _zod.z.string().optional(),
  startupContext: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    applyOn: _zod.z.array(_zod.z.union([_zod.z.literal("new"), _zod.z.literal("reset")])).optional(),
    dailyMemoryDays: _zod.z.number().int().min(1).max(14).optional(),
    maxFileBytes: _zod.z.number().int().min(1).max(64 * 1024).optional(),
    maxFileChars: _zod.z.number().int().min(1).max(1e4).optional(),
    maxTotalChars: _zod.z.number().int().min(1).max(5e4).optional()
  }).strict().optional(),
  contextLimits: _zodSchemaAgentRuntimeBgmaoJWM.t,
  timeFormat: _zod.z.union([
  _zod.z.literal("auto"),
  _zod.z.literal("12"),
  _zod.z.literal("24")]
  ).optional(),
  envelopeTimezone: _zod.z.string().optional(),
  envelopeTimestamp: _zod.z.union([_zod.z.literal("on"), _zod.z.literal("off")]).optional(),
  envelopeElapsed: _zod.z.union([_zod.z.literal("on"), _zod.z.literal("off")]).optional(),
  contextTokens: _zod.z.number().int().positive().optional(),
  cliBackends: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.r).optional(),
  memorySearch: _zodSchemaAgentRuntimeBgmaoJWM.c,
  contextPruning: _zod.z.object({
    mode: _zod.z.union([_zod.z.literal("off"), _zod.z.literal("cache-ttl")]).optional(),
    ttl: _zod.z.string().optional(),
    keepLastAssistants: _zod.z.number().int().nonnegative().optional(),
    softTrimRatio: _zod.z.number().min(0).max(1).optional(),
    hardClearRatio: _zod.z.number().min(0).max(1).optional(),
    minPrunableToolChars: _zod.z.number().int().nonnegative().optional(),
    tools: _zod.z.object({
      allow: _zod.z.array(_zod.z.string()).optional(),
      deny: _zod.z.array(_zod.z.string()).optional()
    }).strict().optional(),
    softTrim: _zod.z.object({
      maxChars: _zod.z.number().int().nonnegative().optional(),
      headChars: _zod.z.number().int().nonnegative().optional(),
      tailChars: _zod.z.number().int().nonnegative().optional()
    }).strict().optional(),
    hardClear: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      placeholder: _zod.z.string().optional()
    }).strict().optional()
  }).strict().optional(),
  compaction: _zod.z.object({
    mode: _zod.z.union([_zod.z.literal("default"), _zod.z.literal("safeguard")]).optional(),
    provider: _zod.z.string().optional(),
    reserveTokens: _zod.z.number().int().nonnegative().optional(),
    keepRecentTokens: _zod.z.number().int().positive().optional(),
    reserveTokensFloor: _zod.z.number().int().nonnegative().optional(),
    maxHistoryShare: _zod.z.number().min(.1).max(.9).optional(),
    customInstructions: _zod.z.string().optional(),
    identifierPolicy: _zod.z.union([
    _zod.z.literal("strict"),
    _zod.z.literal("off"),
    _zod.z.literal("custom")]
    ).optional(),
    identifierInstructions: _zod.z.string().optional(),
    recentTurnsPreserve: _zod.z.number().int().min(0).max(12).optional(),
    qualityGuard: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      maxRetries: _zod.z.number().int().nonnegative().optional()
    }).strict().optional(),
    midTurnPrecheck: _zod.z.object({ enabled: _zod.z.boolean().optional() }).strict().optional(),
    postIndexSync: _zod.z.enum([
    "off",
    "async",
    "await"]
    ).optional(),
    postCompactionSections: _zod.z.array(_zod.z.string()).optional(),
    model: _zod.z.string().optional(),
    timeoutSeconds: _zod.z.number().int().positive().optional(),
    memoryFlush: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      model: _zod.z.string().optional(),
      softThresholdTokens: _zod.z.number().int().nonnegative().optional(),
      forceFlushTranscriptBytes: NonNegativeByteSizeSchema.optional(),
      prompt: _zod.z.string().optional(),
      systemPrompt: _zod.z.string().optional()
    }).strict().optional(),
    truncateAfterCompaction: _zod.z.boolean().optional(),
    maxActiveTranscriptBytes: NonNegativeByteSizeSchema.optional(),
    notifyUser: _zod.z.boolean().optional()
  }).strict().optional(),
  embeddedPi: _zod.z.object({
    projectSettingsPolicy: _zod.z.union([
    _zod.z.literal("trusted"),
    _zod.z.literal("sanitize"),
    _zod.z.literal("ignore")]
    ).optional(),
    executionContract: _zod.z.union([_zod.z.literal("default"), _zod.z.literal("strict-agentic")]).optional()
  }).strict().optional(),
  thinkingDefault: _zod.z.union([
  _zod.z.literal("off"),
  _zod.z.literal("minimal"),
  _zod.z.literal("low"),
  _zod.z.literal("medium"),
  _zod.z.literal("high"),
  _zod.z.literal("xhigh"),
  _zod.z.literal("adaptive"),
  _zod.z.literal("max")]
  ).optional(),
  verboseDefault: _zod.z.union([
  _zod.z.literal("off"),
  _zod.z.literal("on"),
  _zod.z.literal("full")]
  ).optional(),
  toolProgressDetail: _zod.z.union([_zod.z.literal("explain"), _zod.z.literal("raw")]).optional(),
  reasoningDefault: _zod.z.union([
  _zod.z.literal("off"),
  _zod.z.literal("on"),
  _zod.z.literal("stream")]
  ).optional(),
  elevatedDefault: _zod.z.union([
  _zod.z.literal("off"),
  _zod.z.literal("on"),
  _zod.z.literal("ask"),
  _zod.z.literal("full")]
  ).optional(),
  blockStreamingDefault: _zod.z.union([_zod.z.literal("off"), _zod.z.literal("on")]).optional(),
  blockStreamingBreak: _zod.z.union([_zod.z.literal("text_end"), _zod.z.literal("message_end")]).optional(),
  blockStreamingChunk: _zodSchemaCoreB8hU4HYi.t.optional(),
  blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
  humanDelay: _zodSchemaCoreB8hU4HYi.d.optional(),
  timeoutSeconds: _zod.z.number().int().positive().optional(),
  mediaMaxMb: _zod.z.number().positive().optional(),
  imageMaxDimensionPx: _zod.z.number().int().positive().optional(),
  typingIntervalSeconds: _zod.z.number().int().positive().optional(),
  typingMode: _zodSchemaCoreB8hU4HYi.P.optional(),
  heartbeat: _zodSchemaAgentRuntimeBgmaoJWM.s,
  maxConcurrent: _zod.z.number().int().positive().optional(),
  subagents: _zod.z.object({
    allowAgents: _zod.z.array(_zod.z.string()).optional(),
    maxConcurrent: _zod.z.number().int().positive().optional(),
    maxSpawnDepth: _zod.z.number().int().min(1).max(5).optional().describe("Maximum nesting depth for sub-agent spawning. 1 = no nesting (default), 2 = sub-agents can spawn sub-sub-agents."),
    maxChildrenPerAgent: _zod.z.number().int().min(1).max(20).optional().describe("Maximum number of active children a single agent session can spawn (default: 5)."),
    archiveAfterMinutes: _zod.z.number().int().min(0).optional(),
    model: _zodSchemaAgentRuntimeBgmaoJWM.d.optional(),
    thinking: _zod.z.string().optional(),
    runTimeoutSeconds: _zod.z.number().int().min(0).optional(),
    announceTimeoutMs: _zod.z.number().int().positive().optional(),
    requireAgentId: _zod.z.boolean().optional()
  }).strict().optional(),
  sandbox: _zodSchemaAgentRuntimeBgmaoJWM.a
}).strict().optional();
//#endregion
//#region src/config/zod-schema.agents.ts
const AgentsSchema = _zod.z.object({
  defaults: _zod.z.lazy(() => AgentDefaultsSchema).optional(),
  list: _zod.z.array(_zodSchemaAgentRuntimeBgmaoJWM.r).optional()
}).strict().optional();
const BindingMatchSchema = _zod.z.object({
  channel: _zod.z.string(),
  accountId: _zod.z.string().optional(),
  peer: _zod.z.object({
    kind: _zod.z.union([
    _zod.z.literal("direct"),
    _zod.z.literal("group"),
    _zod.z.literal("channel"),
    _zod.z.literal("dm")]
    ),
    id: _zod.z.string()
  }).strict().optional(),
  guildId: _zod.z.string().optional(),
  teamId: _zod.z.string().optional(),
  roles: _zod.z.array(_zod.z.string()).optional()
}).strict();
const BindingSessionSchema = _zod.z.object({ dmScope: _zod.z.union([
  _zod.z.literal("main"),
  _zod.z.literal("per-peer"),
  _zod.z.literal("per-channel-peer"),
  _zod.z.literal("per-account-channel-peer")]
  ).optional() }).strict();
const RouteBindingSchema = _zod.z.object({
  type: _zod.z.literal("route").optional(),
  agentId: _zod.z.string(),
  comment: _zod.z.string().optional(),
  match: BindingMatchSchema,
  session: BindingSessionSchema.optional()
}).strict();
const AcpBindingSchema = _zod.z.object({
  type: _zod.z.literal("acp"),
  agentId: _zod.z.string(),
  comment: _zod.z.string().optional(),
  match: BindingMatchSchema,
  acp: _zod.z.object({
    mode: _zod.z.enum(["persistent", "oneshot"]).optional(),
    label: _zod.z.string().optional(),
    cwd: _zod.z.string().optional(),
    backend: _zod.z.string().optional()
  }).strict().optional()
}).strict().superRefine((value, ctx) => {
  if (!((0, _stringCoerceBje8XVt.c)(value.match.peer?.id) ?? "")) {
    ctx.addIssue({
      code: _zod.z.ZodIssueCode.custom,
      path: ["match", "peer"],
      message: "ACP bindings require match.peer.id to target a concrete conversation."
    });
    return;
  }
});
const BindingsSchema = _zod.z.array(_zod.z.union([RouteBindingSchema, AcpBindingSchema])).optional();
const BroadcastStrategySchema = _zod.z.enum(["parallel", "sequential"]);
const BroadcastSchema = _zod.z.object({ strategy: BroadcastStrategySchema.optional() }).catchall(_zod.z.array(_zod.z.string())).optional();
const AudioSchema = _zod.z.object({ transcription: _zodSchemaCoreB8hU4HYi.k }).strict().optional();
//#endregion
//#region src/config/zod-schema.approvals.ts
const ExecApprovalForwardTargetSchema = _zod.z.object({
  channel: _zod.z.string().min(1),
  to: _zod.z.string().min(1),
  accountId: _zod.z.string().optional(),
  threadId: _zod.z.union([_zod.z.string(), _zod.z.number()]).optional()
}).strict();
const ExecApprovalForwardingSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  mode: _zod.z.union([
  _zod.z.literal("session"),
  _zod.z.literal("targets"),
  _zod.z.literal("both")]
  ).optional(),
  agentFilter: _zod.z.array(_zod.z.string()).optional(),
  sessionFilter: _zod.z.array(_zod.z.string()).optional(),
  targets: _zod.z.array(ExecApprovalForwardTargetSchema).optional()
}).strict().optional();
const ApprovalsSchema = _zod.z.object({
  exec: ExecApprovalForwardingSchema,
  plugin: ExecApprovalForwardingSchema
}).strict().optional();
//#endregion
//#region src/config/zod-schema.hooks.ts
function isSafeRelativeModulePath(raw) {
  const value = raw.trim();
  if (!value) return false;
  if (_nodePath.default.isAbsolute(value)) return false;
  if (value.startsWith("~")) return false;
  if (value.includes(":")) return false;
  if (value.split(/[\\/]+/g).some((part) => part === "..")) return false;
  return true;
}
const SafeRelativeModulePathSchema = _zod.z.string().refine(isSafeRelativeModulePath, "module must be a safe relative path (no absolute paths)");
const HookMappingSchema = _zod.z.object({
  id: _zod.z.string().optional(),
  match: _zod.z.object({
    path: _zod.z.string().optional(),
    source: _zod.z.string().optional()
  }).optional(),
  action: _zod.z.union([_zod.z.literal("wake"), _zod.z.literal("agent")]).optional(),
  wakeMode: _zod.z.union([_zod.z.literal("now"), _zod.z.literal("next-heartbeat")]).optional(),
  name: _zod.z.string().optional(),
  agentId: _zod.z.string().optional(),
  sessionKey: _zod.z.string().optional().register(_zodSchemaSensitive4zM6OUv.t),
  messageTemplate: _zod.z.string().optional(),
  textTemplate: _zod.z.string().optional(),
  deliver: _zod.z.boolean().optional(),
  allowUnsafeExternalContent: _zod.z.boolean().optional(),
  channel: _zod.z.string().trim().min(1).optional(),
  to: _zod.z.string().optional(),
  model: _zod.z.string().optional(),
  thinking: _zod.z.string().optional(),
  timeoutSeconds: _zod.z.number().int().positive().optional(),
  transform: _zod.z.object({
    module: SafeRelativeModulePathSchema,
    export: _zod.z.string().optional()
  }).strict().optional()
}).strict().optional();
const InternalHookHandlerSchema = _zod.z.object({
  event: _zod.z.string(),
  module: SafeRelativeModulePathSchema,
  export: _zod.z.string().optional()
}).strict();
const HookConfigSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  env: _zod.z.record(_zod.z.string(), _zod.z.string()).optional()
}).passthrough();
const HookInstallRecordSchema = _zod.z.object({
  ..._zodSchemaInstallsBrZxLEMx.t,
  hooks: _zod.z.array(_zod.z.string()).optional()
}).strict();
const InternalHooksSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  handlers: _zod.z.array(InternalHookHandlerSchema).optional(),
  entries: _zod.z.record(_zod.z.string(), HookConfigSchema).optional(),
  load: _zod.z.object({ extraDirs: _zod.z.array(_zod.z.string()).optional() }).strict().optional(),
  installs: _zod.z.record(_zod.z.string(), HookInstallRecordSchema).optional()
}).strict().optional();
const HooksGmailSchema = _zod.z.object({
  account: _zod.z.string().optional(),
  label: _zod.z.string().optional(),
  topic: _zod.z.string().optional(),
  subscription: _zod.z.string().optional(),
  pushToken: _zod.z.string().optional().register(_zodSchemaSensitive4zM6OUv.t),
  hookUrl: _zod.z.string().optional(),
  includeBody: _zod.z.boolean().optional(),
  maxBytes: _zod.z.number().int().positive().optional(),
  renewEveryMinutes: _zod.z.number().int().positive().optional(),
  allowUnsafeExternalContent: _zod.z.boolean().optional(),
  serve: _zod.z.object({
    bind: _zod.z.string().optional(),
    port: _zod.z.number().int().positive().optional(),
    path: _zod.z.string().optional()
  }).strict().optional(),
  tailscale: _zod.z.object({
    mode: _zod.z.union([
    _zod.z.literal("off"),
    _zod.z.literal("serve"),
    _zod.z.literal("funnel")]
    ).optional(),
    path: _zod.z.string().optional(),
    target: _zod.z.string().optional()
  }).strict().optional(),
  model: _zod.z.string().optional(),
  thinking: _zod.z.union([
  _zod.z.literal("off"),
  _zod.z.literal("minimal"),
  _zod.z.literal("low"),
  _zod.z.literal("medium"),
  _zod.z.literal("high")]
  ).optional()
}).strict().optional();
//#endregion
//#region src/config/zod-schema.providers.ts
const ChannelModelByChannelSchema = _zod.z.record(_zod.z.string(), _zod.z.record(_zod.z.string(), _zod.z.string())).optional();
function addLegacyChannelAcpBindingIssues(value, ctx, path = []) {
  if (!value || typeof value !== "object") return;
  if (Array.isArray(value)) {
    value.forEach((entry, index) => addLegacyChannelAcpBindingIssues(entry, ctx, [...path, index]));
    return;
  }
  const record = value;
  const bindings = record.bindings;
  if (bindings && typeof bindings === "object" && !Array.isArray(bindings)) {
    const acp = bindings.acp;
    if (acp && typeof acp === "object") ctx.addIssue({
      code: _zod.z.ZodIssueCode.custom,
      path: [
      ...path,
      "bindings",
      "acp"],

      message: "Legacy channel-local ACP bindings were removed; use top-level bindings[] entries."
    });
  }
  for (const [key, entry] of Object.entries(record)) addLegacyChannelAcpBindingIssues(entry, ctx, [...path, key]);
}
const ChannelsSchema = _zod.z.object({
  defaults: _zod.z.object({
    groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional(),
    contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
    heartbeat: _zodSchemaProvidersWhatsappCSmjq_Ez.l
  }).strict().optional(),
  modelByChannel: ChannelModelByChannelSchema
}).passthrough().superRefine((value, ctx) => {
  addLegacyChannelAcpBindingIssues(value, ctx);
}).optional();
//#endregion
//#region src/config/zod-schema.proxy.ts
function isHttpProxyUrl(value) {
  try {
    return new URL(value).protocol === "http:";
  } catch {
    return false;
  }
}
const ProxyConfigSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  proxyUrl: _zod.z.string().url().refine(isHttpProxyUrl, { message: "proxyUrl must use http://" }).register(_zodSchemaSensitive4zM6OUv.t).optional()
}).strict().optional();
//#endregion
//#region src/config/zod-schema.session.ts
const SessionResetConfigSchema = _zod.z.object({
  mode: _zod.z.union([_zod.z.literal("daily"), _zod.z.literal("idle")]).optional(),
  atHour: _zod.z.number().int().min(0).max(23).optional(),
  idleMinutes: _zod.z.number().int().positive().optional()
}).strict();
const SessionSendPolicySchema = (0, _zodSchemaCoreB8hU4HYi.R)();
const SessionSchema = _zod.z.object({
  scope: _zod.z.union([_zod.z.literal("per-sender"), _zod.z.literal("global")]).optional(),
  dmScope: _zod.z.union([
  _zod.z.literal("main"),
  _zod.z.literal("per-peer"),
  _zod.z.literal("per-channel-peer"),
  _zod.z.literal("per-account-channel-peer")]
  ).optional(),
  identityLinks: _zod.z.record(_zod.z.string(), _zod.z.array(_zod.z.string())).optional(),
  resetTriggers: _zod.z.array(_zod.z.string()).optional(),
  idleMinutes: _zod.z.number().int().positive().optional(),
  reset: SessionResetConfigSchema.optional(),
  resetByType: _zod.z.object({
    direct: SessionResetConfigSchema.optional(),
    /** @deprecated Use `direct` instead. Kept for backward compatibility. */
    dm: SessionResetConfigSchema.optional(),
    group: SessionResetConfigSchema.optional(),
    thread: SessionResetConfigSchema.optional()
  }).strict().optional(),
  resetByChannel: _zod.z.record(_zod.z.string(), SessionResetConfigSchema).optional(),
  store: _zod.z.string().optional(),
  typingIntervalSeconds: _zod.z.number().int().positive().optional(),
  typingMode: _zodSchemaCoreB8hU4HYi.P.optional(),
  mainKey: _zod.z.string().optional(),
  sendPolicy: SessionSendPolicySchema.optional(),
  writeLock: _zod.z.object({ acquireTimeoutMs: _zod.z.number().int().positive().optional() }).strict().optional(),
  agentToAgent: _zod.z.object({ maxPingPongTurns: _zod.z.number().int().min(0).max(5).optional() }).strict().optional(),
  threadBindings: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    idleHours: _zod.z.number().nonnegative().optional(),
    maxAgeHours: _zod.z.number().nonnegative().optional(),
    spawnSessions: _zod.z.boolean().optional(),
    defaultSpawnContext: _zod.z.enum(["isolated", "fork"]).optional()
  }).strict().optional(),
  maintenance: _zod.z.object({
    mode: _zod.z.enum(["enforce", "warn"]).optional(),
    pruneAfter: _zod.z.union([_zod.z.string(), _zod.z.number()]).optional(),
    /** @deprecated Use pruneAfter instead. */
    pruneDays: _zod.z.number().int().positive().optional(),
    maxEntries: _zod.z.number().int().positive().optional(),
    rotateBytes: _zod.z.union([_zod.z.string(), _zod.z.number()]).optional(),
    resetArchiveRetention: _zod.z.union([
    _zod.z.string(),
    _zod.z.number(),
    _zod.z.literal(false)]
    ).optional(),
    maxDiskBytes: _zod.z.union([_zod.z.string(), _zod.z.number()]).optional(),
    highWaterBytes: _zod.z.union([_zod.z.string(), _zod.z.number()]).optional()
  }).strict().superRefine((val, ctx) => {
    if (val.pruneAfter !== void 0) try {
      (0, _parseDurationCIsOpJPW.t)((0, _stringCoerceBje8XVt.d)(val.pruneAfter) ?? "", { defaultUnit: "d" });
    } catch {
      ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        path: ["pruneAfter"],
        message: "invalid duration (use ms, s, m, h, d)"
      });
    }
    if (val.resetArchiveRetention !== void 0 && val.resetArchiveRetention !== false) try {
      (0, _parseDurationCIsOpJPW.t)((0, _stringCoerceBje8XVt.d)(val.resetArchiveRetention) ?? "", { defaultUnit: "d" });
    } catch {
      ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        path: ["resetArchiveRetention"],
        message: "invalid duration (use ms, s, m, h, d)"
      });
    }
    if (val.maxDiskBytes !== void 0) try {
      parseByteSize((0, _stringCoerceBje8XVt.d)(val.maxDiskBytes) ?? "", { defaultUnit: "b" });
    } catch {
      ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        path: ["maxDiskBytes"],
        message: "invalid size (use b, kb, mb, gb, tb)"
      });
    }
    if (val.highWaterBytes !== void 0) try {
      parseByteSize((0, _stringCoerceBje8XVt.d)(val.highWaterBytes) ?? "", { defaultUnit: "b" });
    } catch {
      ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        path: ["highWaterBytes"],
        message: "invalid size (use b, kb, mb, gb, tb)"
      });
    }
  }).optional()
}).strict().optional();
const MessagesSchema = _zod.z.object({
  messagePrefix: _zod.z.string().optional(),
  visibleReplies: _zodSchemaCoreB8hU4HYi.F.optional(),
  responsePrefix: _zod.z.string().optional(),
  groupChat: _zodSchemaCoreB8hU4HYi.c,
  queue: _zodSchemaCoreB8hU4HYi.y,
  inbound: _zodSchemaCoreB8hU4HYi.p,
  ackReaction: _zod.z.string().optional(),
  ackReactionScope: _zod.z.enum([
  "group-mentions",
  "group-all",
  "direct",
  "all",
  "off",
  "none"]
  ).optional(),
  removeAckAfterReply: _zod.z.boolean().optional(),
  statusReactions: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    emojis: _zod.z.object({
      thinking: _zod.z.string().optional(),
      tool: _zod.z.string().optional(),
      coding: _zod.z.string().optional(),
      web: _zod.z.string().optional(),
      done: _zod.z.string().optional(),
      error: _zod.z.string().optional(),
      stallSoft: _zod.z.string().optional(),
      stallHard: _zod.z.string().optional(),
      compacting: _zod.z.string().optional()
    }).strict().optional(),
    timing: _zod.z.object({
      debounceMs: _zod.z.number().int().min(0).optional(),
      stallSoftMs: _zod.z.number().int().min(0).optional(),
      stallHardMs: _zod.z.number().int().min(0).optional(),
      doneHoldMs: _zod.z.number().int().min(0).optional(),
      errorHoldMs: _zod.z.number().int().min(0).optional()
    }).strict().optional()
  }).strict().optional(),
  suppressToolErrors: _zod.z.boolean().optional(),
  tts: _zodSchemaCoreB8hU4HYi.j
}).strict().optional();
const CommandsSchema = _zod.z.object({
  native: _zodSchemaCoreB8hU4HYi._.optional().default("auto"),
  nativeSkills: _zodSchemaCoreB8hU4HYi._.optional().default("auto"),
  text: _zod.z.boolean().optional(),
  bash: _zod.z.boolean().optional(),
  bashForegroundMs: _zod.z.number().int().min(0).max(3e4).optional(),
  config: _zod.z.boolean().optional(),
  mcp: _zod.z.boolean().optional(),
  plugins: _zod.z.boolean().optional(),
  debug: _zod.z.boolean().optional(),
  restart: _zod.z.boolean().optional().default(true),
  useAccessGroups: _zod.z.boolean().optional(),
  ownerAllowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  ownerDisplay: _zod.z.enum(["raw", "hash"]).optional().default("raw"),
  ownerDisplaySecret: _zod.z.string().optional().register(_zodSchemaSensitive4zM6OUv.t),
  allowFrom: _zodSchemaAgentRuntimeBgmaoJWM.o.optional()
}).strict().optional().default(() => ({
  native: "auto",
  nativeSkills: "auto",
  restart: true,
  ownerDisplay: "raw"
}));
//#endregion
//#region src/config/zod-schema.ts
const BrowserSnapshotDefaultsSchema = _zod.z.object({ mode: _zod.z.literal("efficient").optional() }).strict().optional();
const NodeHostSchema = _zod.z.object({ browserProxy: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    allowProfiles: _zod.z.array(_zod.z.string()).optional()
  }).strict().optional() }).strict().optional();
const AccessGroupsSchema = _zod.z.record(_zod.z.string().min(1), _zod.z.discriminatedUnion("type", [_zod.z.object({
  type: _zod.z.literal("discord.channelAudience"),
  guildId: _zod.z.string().min(1),
  channelId: _zod.z.string().min(1),
  membership: _zod.z.literal("canViewChannel").optional()
}).strict(), _zod.z.object({
  type: _zod.z.literal("message.senders"),
  members: _zod.z.record(_zod.z.string().min(1), _zod.z.array(_zod.z.string().min(1)))
}).strict()])).optional();
const MemoryQmdPathSchema = _zod.z.object({
  path: _zod.z.string(),
  name: _zod.z.string().optional(),
  pattern: _zod.z.string().optional()
}).strict();
const MemoryQmdSessionSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  exportDir: _zod.z.string().optional(),
  retentionDays: _zod.z.number().int().nonnegative().optional()
}).strict();
const MemoryQmdUpdateSchema = _zod.z.object({
  interval: _zod.z.string().optional(),
  debounceMs: _zod.z.number().int().nonnegative().optional(),
  onBoot: _zod.z.boolean().optional(),
  startup: _zod.z.enum([
  "off",
  "idle",
  "immediate"]
  ).optional(),
  startupDelayMs: _zod.z.number().int().nonnegative().optional(),
  waitForBootSync: _zod.z.boolean().optional(),
  embedInterval: _zod.z.string().optional(),
  commandTimeoutMs: _zod.z.number().int().nonnegative().optional(),
  updateTimeoutMs: _zod.z.number().int().nonnegative().optional(),
  embedTimeoutMs: _zod.z.number().int().nonnegative().optional()
}).strict();
const MemoryQmdLimitsSchema = _zod.z.object({
  maxResults: _zod.z.number().int().positive().optional(),
  maxSnippetChars: _zod.z.number().int().positive().optional(),
  maxInjectedChars: _zod.z.number().int().positive().optional(),
  timeoutMs: _zod.z.number().int().nonnegative().optional()
}).strict();
const MemoryQmdMcporterSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  serverName: _zod.z.string().optional(),
  startDaemon: _zod.z.boolean().optional()
}).strict();
const LoggingLevelSchema = _zod.z.union([
_zod.z.literal("silent"),
_zod.z.literal("fatal"),
_zod.z.literal("error"),
_zod.z.literal("warn"),
_zod.z.literal("info"),
_zod.z.literal("debug"),
_zod.z.literal("trace")]
);
const MemoryQmdSchema = _zod.z.object({
  command: _zod.z.string().optional(),
  mcporter: MemoryQmdMcporterSchema.optional(),
  searchMode: _zod.z.union([
  _zod.z.literal("query"),
  _zod.z.literal("search"),
  _zod.z.literal("vsearch")]
  ).optional(),
  searchTool: _zod.z.string().trim().min(1).optional(),
  includeDefaultMemory: _zod.z.boolean().optional(),
  paths: _zod.z.array(MemoryQmdPathSchema).optional(),
  sessions: MemoryQmdSessionSchema.optional(),
  update: MemoryQmdUpdateSchema.optional(),
  limits: MemoryQmdLimitsSchema.optional(),
  scope: SessionSendPolicySchema.optional()
}).strict();
const MemorySchema = _zod.z.object({
  backend: _zod.z.union([_zod.z.literal("builtin"), _zod.z.literal("qmd")]).optional(),
  citations: _zod.z.union([
  _zod.z.literal("auto"),
  _zod.z.literal("on"),
  _zod.z.literal("off")]
  ).optional(),
  qmd: MemoryQmdSchema.optional()
}).strict().optional();
const HttpUrlSchema = _zod.z.string().url().refine((value) => {
  const protocol = new URL(value).protocol;
  return protocol === "http:" || protocol === "https:";
}, "Expected http:// or https:// URL");
const ResponsesEndpointUrlFetchShape = {
  allowUrl: _zod.z.boolean().optional(),
  urlAllowlist: _zod.z.array(_zod.z.string()).optional(),
  allowedMimes: _zod.z.array(_zod.z.string()).optional(),
  maxBytes: _zod.z.number().int().positive().optional(),
  maxRedirects: _zod.z.number().int().nonnegative().optional(),
  timeoutMs: _zod.z.number().int().positive().optional()
};
const SkillEntrySchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  apiKey: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  env: _zod.z.record(_zod.z.string(), _zod.z.string()).optional(),
  config: _zod.z.record(_zod.z.string(), _zod.z.unknown()).optional()
}).strict();
const PluginEntrySchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  hooks: _zod.z.object({
    allowPromptInjection: _zod.z.boolean().optional(),
    allowConversationAccess: _zod.z.boolean().optional(),
    timeoutMs: _zod.z.number().int().positive().max(6e5).optional(),
    timeouts: _zod.z.record(_zod.z.string(), _zod.z.number().int().positive().max(6e5)).optional()
  }).strict().optional(),
  subagent: _zod.z.object({
    allowModelOverride: _zod.z.boolean().optional(),
    allowedModels: _zod.z.array(_zod.z.string()).optional()
  }).strict().optional(),
  config: _zod.z.record(_zod.z.string(), _zod.z.unknown()).optional()
}).strict();
const TalkProviderEntrySchema = _zod.z.object({ apiKey: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t) }).catchall(_zod.z.unknown());
const TalkSchema = _zod.z.object({
  provider: _zod.z.string().optional(),
  providers: _zod.z.record(_zod.z.string(), TalkProviderEntrySchema).optional(),
  speechLocale: _zod.z.string().optional(),
  interruptOnSpeech: _zod.z.boolean().optional(),
  silenceTimeoutMs: _zod.z.number().int().positive().optional()
}).strict().superRefine((talk, ctx) => {
  const provider = (0, _stringCoerceBje8XVt.a)(talk.provider ?? "");
  const providers = talk.providers ? Object.keys(talk.providers) : [];
  if (provider && providers.length > 0 && !(provider in talk.providers)) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: ["provider"],
    message: `talk.provider must match a key in talk.providers (missing "${provider}")`
  });
  if (!provider && providers.length > 1) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: ["provider"],
    message: "talk.provider is required when talk.providers defines multiple providers"
  });
});
const McpServerSchema = _zod.z.object({
  command: _zod.z.string().optional(),
  args: _zod.z.array(_zod.z.string()).optional(),
  env: _zod.z.record(_zod.z.string(), _zod.z.union([
  _zod.z.string(),
  _zod.z.number(),
  _zod.z.boolean()]
  )).optional(),
  cwd: _zod.z.string().optional(),
  workingDirectory: _zod.z.string().optional(),
  url: HttpUrlSchema.optional(),
  transport: _zod.z.union([_zod.z.literal("sse"), _zod.z.literal("streamable-http")]).optional(),
  headers: _zod.z.record(_zod.z.string(), _zod.z.union([
  _zod.z.string().register(_zodSchemaSensitive4zM6OUv.t),
  _zod.z.number(),
  _zod.z.boolean()]
  ).register(_zodSchemaSensitive4zM6OUv.t)).optional()
}).catchall(_zod.z.unknown());
const McpConfigSchema = _zod.z.object({
  servers: _zod.z.record(_zod.z.string(), McpServerSchema).optional(),
  sessionIdleTtlMs: _zod.z.number().finite().min(0).optional()
}).strict().optional();
const CrestodianSchema = _zod.z.object({ rescue: _zod.z.object({
    enabled: _zod.z.union([_zod.z.literal("auto"), _zod.z.boolean()]).optional(),
    ownerDmOnly: _zod.z.boolean().optional(),
    pendingTtlMinutes: _zod.z.number().int().positive().optional()
  }).strict().optional() }).strict().optional();
const CommitmentsSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  maxPerDay: _zod.z.number().int().positive().optional()
}).strict().optional();
const OpenClawSchema = exports.t = _zod.z.object({
  $schema: _zod.z.string().optional(),
  meta: _zod.z.object({
    lastTouchedVersion: _zod.z.string().optional(),
    lastTouchedAt: _zod.z.union([_zod.z.string(), _zod.z.number().transform((n, ctx) => {
      const d = new Date(n);
      if (Number.isNaN(d.getTime())) {
        ctx.addIssue({
          code: _zod.z.ZodIssueCode.custom,
          message: "Invalid timestamp"
        });
        return _zod.z.NEVER;
      }
      return d.toISOString();
    })]).optional()
  }).strict().optional(),
  env: _zod.z.object({
    shellEnv: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      timeoutMs: _zod.z.number().int().nonnegative().optional()
    }).strict().optional(),
    vars: _zod.z.record(_zod.z.string(), _zod.z.string()).optional()
  }).catchall(_zod.z.string()).optional(),
  wizard: _zod.z.object({
    lastRunAt: _zod.z.string().optional(),
    lastRunVersion: _zod.z.string().optional(),
    lastRunCommit: _zod.z.string().optional(),
    lastRunCommand: _zod.z.string().optional(),
    lastRunMode: _zod.z.union([_zod.z.literal("local"), _zod.z.literal("remote")]).optional()
  }).strict().optional(),
  diagnostics: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    flags: _zod.z.array(_zod.z.string()).optional(),
    stuckSessionWarnMs: _zod.z.number().int().positive().optional(),
    otel: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      endpoint: _zod.z.string().optional(),
      tracesEndpoint: _zod.z.string().optional(),
      metricsEndpoint: _zod.z.string().optional(),
      logsEndpoint: _zod.z.string().optional(),
      protocol: _zod.z.union([_zod.z.literal("http/protobuf"), _zod.z.literal("grpc")]).optional(),
      headers: _zod.z.record(_zod.z.string(), _zod.z.string()).optional(),
      serviceName: _zod.z.string().optional(),
      traces: _zod.z.boolean().optional(),
      metrics: _zod.z.boolean().optional(),
      logs: _zod.z.boolean().optional(),
      sampleRate: _zod.z.number().min(0).max(1).optional(),
      flushIntervalMs: _zod.z.number().int().nonnegative().optional(),
      captureContent: _zod.z.union([_zod.z.boolean(), _zod.z.object({
        enabled: _zod.z.boolean().optional(),
        inputMessages: _zod.z.boolean().optional(),
        outputMessages: _zod.z.boolean().optional(),
        toolInputs: _zod.z.boolean().optional(),
        toolOutputs: _zod.z.boolean().optional(),
        systemPrompt: _zod.z.boolean().optional()
      }).strict()]).optional()
    }).strict().optional(),
    cacheTrace: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      filePath: _zod.z.string().optional(),
      includeMessages: _zod.z.boolean().optional(),
      includePrompt: _zod.z.boolean().optional(),
      includeSystem: _zod.z.boolean().optional()
    }).strict().optional()
  }).strict().optional(),
  logging: _zod.z.object({
    level: LoggingLevelSchema.optional(),
    file: _zod.z.string().optional(),
    maxFileBytes: _zod.z.number().int().positive().optional(),
    consoleLevel: LoggingLevelSchema.optional(),
    consoleStyle: _zod.z.union([
    _zod.z.literal("pretty"),
    _zod.z.literal("compact"),
    _zod.z.literal("json")]
    ).optional(),
    redactSensitive: _zod.z.union([_zod.z.literal("off"), _zod.z.literal("tools")]).optional(),
    redactPatterns: _zod.z.array(_zod.z.string()).optional()
  }).strict().optional(),
  cli: _zod.z.object({ banner: _zod.z.object({ taglineMode: _zod.z.union([
      _zod.z.literal("random"),
      _zod.z.literal("default"),
      _zod.z.literal("off")]
      ).optional() }).strict().optional() }).strict().optional(),
  crestodian: CrestodianSchema,
  update: _zod.z.object({
    channel: _zod.z.union([
    _zod.z.literal("stable"),
    _zod.z.literal("beta"),
    _zod.z.literal("dev")]
    ).optional(),
    checkOnStart: _zod.z.boolean().optional(),
    auto: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      stableDelayHours: _zod.z.number().nonnegative().max(168).optional(),
      stableJitterHours: _zod.z.number().nonnegative().max(168).optional(),
      betaCheckIntervalHours: _zod.z.number().positive().max(24).optional()
    }).strict().optional()
  }).strict().optional(),
  browser: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    evaluateEnabled: _zod.z.boolean().optional(),
    cdpUrl: _zod.z.string().optional(),
    remoteCdpTimeoutMs: _zod.z.number().int().nonnegative().optional(),
    remoteCdpHandshakeTimeoutMs: _zod.z.number().int().nonnegative().optional(),
    localLaunchTimeoutMs: _zod.z.number().int().positive().max(12e4).optional(),
    localCdpReadyTimeoutMs: _zod.z.number().int().positive().max(12e4).optional(),
    actionTimeoutMs: _zod.z.number().int().positive().optional(),
    color: _zod.z.string().optional(),
    executablePath: _zod.z.string().optional(),
    headless: _zod.z.boolean().optional(),
    noSandbox: _zod.z.boolean().optional(),
    attachOnly: _zod.z.boolean().optional(),
    cdpPortRangeStart: _zod.z.number().int().min(1).max(65535).optional(),
    defaultProfile: _zod.z.string().optional(),
    snapshotDefaults: BrowserSnapshotDefaultsSchema,
    ssrfPolicy: _zod.z.object({
      dangerouslyAllowPrivateNetwork: _zod.z.boolean().optional(),
      allowedHostnames: _zod.z.array(_zod.z.string()).optional(),
      hostnameAllowlist: _zod.z.array(_zod.z.string()).optional()
    }).strict().optional(),
    profiles: _zod.z.record(_zod.z.string().regex(/^[a-z0-9-]+$/, "Profile names must be alphanumeric with hyphens only"), _zod.z.object({
      cdpPort: _zod.z.number().int().min(1).max(65535).optional(),
      cdpUrl: _zod.z.string().optional(),
      userDataDir: _zod.z.string().optional(),
      mcpCommand: _zod.z.string().optional(),
      mcpArgs: _zod.z.array(_zod.z.string()).optional(),
      driver: _zod.z.union([
      _zod.z.literal("openclaw"),
      _zod.z.literal("clawd"),
      _zod.z.literal("existing-session")]
      ).optional(),
      headless: _zod.z.boolean().optional(),
      executablePath: _zod.z.string().optional(),
      attachOnly: _zod.z.boolean().optional(),
      color: _zodSchemaCoreB8hU4HYi.u
    }).strict().refine((value) => value.driver === "existing-session" || value.cdpPort || value.cdpUrl, { message: "Profile must set cdpPort or cdpUrl" }).refine((value) => value.driver === "existing-session" || !value.userDataDir, { message: "Profile userDataDir is only supported with driver=\"existing-session\"" })).optional(),
    extraArgs: _zod.z.array(_zod.z.string()).optional(),
    tabCleanup: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      idleMinutes: _zod.z.number().int().nonnegative().optional(),
      maxTabsPerSession: _zod.z.number().int().nonnegative().optional(),
      sweepMinutes: _zod.z.number().int().positive().optional()
    }).strict().optional()
  }).strict().optional(),
  ui: _zod.z.object({
    seamColor: _zodSchemaCoreB8hU4HYi.u.optional(),
    assistant: _zod.z.object({
      name: _zod.z.string().max(50).optional(),
      avatar: _zod.z.string().max(2e6).optional()
    }).strict().optional()
  }).strict().optional(),
  secrets: _zodSchemaCoreB8hU4HYi.E,
  auth: _zod.z.object({
    profiles: _zod.z.record(_zod.z.string(), _zod.z.object({
      provider: _zod.z.string(),
      mode: _zod.z.union([
      _zod.z.literal("api_key"),
      _zod.z.literal("oauth"),
      _zod.z.literal("token")]
      ),
      email: _zod.z.string().optional(),
      displayName: _zod.z.string().optional()
    }).strict()).optional(),
    order: _zod.z.record(_zod.z.string(), _zod.z.array(_zod.z.string())).optional(),
    cooldowns: _zod.z.object({
      billingBackoffHours: _zod.z.number().positive().optional(),
      billingBackoffHoursByProvider: _zod.z.record(_zod.z.string(), _zod.z.number().positive()).optional(),
      billingMaxHours: _zod.z.number().positive().optional(),
      authPermanentBackoffMinutes: _zod.z.number().positive().optional(),
      authPermanentMaxMinutes: _zod.z.number().positive().optional(),
      failureWindowHours: _zod.z.number().positive().optional(),
      overloadedProfileRotations: _zod.z.number().int().nonnegative().optional(),
      overloadedBackoffMs: _zod.z.number().int().nonnegative().optional(),
      rateLimitedProfileRotations: _zod.z.number().int().nonnegative().optional()
    }).strict().optional()
  }).strict().optional(),
  accessGroups: AccessGroupsSchema,
  acp: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    dispatch: _zod.z.object({ enabled: _zod.z.boolean().optional() }).strict().optional(),
    backend: _zod.z.string().optional(),
    defaultAgent: _zod.z.string().optional(),
    allowedAgents: _zod.z.array(_zod.z.string()).optional(),
    maxConcurrentSessions: _zod.z.number().int().positive().optional(),
    stream: _zod.z.object({
      coalesceIdleMs: _zod.z.number().int().nonnegative().optional(),
      maxChunkChars: _zod.z.number().int().positive().optional(),
      repeatSuppression: _zod.z.boolean().optional(),
      deliveryMode: _zod.z.union([_zod.z.literal("live"), _zod.z.literal("final_only")]).optional(),
      hiddenBoundarySeparator: _zod.z.union([
      _zod.z.literal("none"),
      _zod.z.literal("space"),
      _zod.z.literal("newline"),
      _zod.z.literal("paragraph")]
      ).optional(),
      maxOutputChars: _zod.z.number().int().positive().optional(),
      maxSessionUpdateChars: _zod.z.number().int().positive().optional(),
      tagVisibility: _zod.z.record(_zod.z.string(), _zod.z.boolean()).optional()
    }).strict().optional(),
    runtime: _zod.z.object({
      ttlMinutes: _zod.z.number().int().positive().optional(),
      installCommand: _zod.z.string().optional()
    }).strict().optional()
  }).strict().optional(),
  models: _zodSchemaCoreB8hU4HYi.g,
  nodeHost: NodeHostSchema,
  agents: AgentsSchema,
  tools: _zodSchemaAgentRuntimeBgmaoJWM.u,
  bindings: BindingsSchema,
  broadcast: BroadcastSchema,
  audio: AudioSchema,
  media: _zod.z.object({
    preserveFilenames: _zod.z.boolean().optional(),
    ttlHours: _zod.z.number().int().min(1).max(168).optional()
  }).strict().optional(),
  messages: MessagesSchema,
  commands: CommandsSchema,
  approvals: ApprovalsSchema,
  session: SessionSchema,
  cron: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    store: _zod.z.string().optional(),
    maxConcurrentRuns: _zod.z.number().int().positive().optional(),
    retry: _zod.z.object({
      maxAttempts: _zod.z.number().int().min(0).max(10).optional(),
      backoffMs: _zod.z.array(_zod.z.number().int().nonnegative()).min(1).max(10).optional(),
      retryOn: _zod.z.array(_zod.z.enum([
      "rate_limit",
      "overloaded",
      "network",
      "timeout",
      "server_error"]
      )).min(1).optional()
    }).strict().optional(),
    webhook: HttpUrlSchema.optional(),
    webhookToken: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
    sessionRetention: _zod.z.union([_zod.z.string(), _zod.z.literal(false)]).optional(),
    runLog: _zod.z.object({
      maxBytes: _zod.z.union([_zod.z.string(), _zod.z.number()]).optional(),
      keepLines: _zod.z.number().int().positive().optional()
    }).strict().optional(),
    failureAlert: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      after: _zod.z.number().int().min(1).optional(),
      cooldownMs: _zod.z.number().int().min(0).optional(),
      includeSkipped: _zod.z.boolean().optional(),
      mode: _zod.z.enum(["announce", "webhook"]).optional(),
      accountId: _zod.z.string().optional()
    }).strict().optional(),
    failureDestination: _zod.z.object({
      channel: _zod.z.string().optional(),
      to: _zod.z.string().optional(),
      accountId: _zod.z.string().optional(),
      mode: _zod.z.enum(["announce", "webhook"]).optional()
    }).strict().optional()
  }).strict().superRefine((val, ctx) => {
    if (val.sessionRetention !== void 0 && val.sessionRetention !== false) try {
      (0, _parseDurationCIsOpJPW.t)((0, _stringCoerceBje8XVt.d)(val.sessionRetention) ?? "", { defaultUnit: "h" });
    } catch {
      ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        path: ["sessionRetention"],
        message: "invalid duration (use ms, s, m, h, d)"
      });
    }
    if (val.runLog?.maxBytes !== void 0) try {
      parseByteSize((0, _stringCoerceBje8XVt.d)(val.runLog.maxBytes) ?? "", { defaultUnit: "b" });
    } catch {
      ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        path: ["runLog", "maxBytes"],
        message: "invalid size (use b, kb, mb, gb, tb)"
      });
    }
  }).optional(),
  commitments: CommitmentsSchema,
  hooks: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    path: _zod.z.string().optional(),
    token: _zod.z.string().optional().register(_zodSchemaSensitive4zM6OUv.t),
    defaultSessionKey: _zod.z.string().optional(),
    allowRequestSessionKey: _zod.z.boolean().optional(),
    allowedSessionKeyPrefixes: _zod.z.array(_zod.z.string()).optional(),
    allowedAgentIds: _zod.z.array(_zod.z.string()).optional(),
    maxBodyBytes: _zod.z.number().int().positive().optional(),
    presets: _zod.z.array(_zod.z.string()).optional(),
    transformsDir: _zod.z.string().optional(),
    mappings: _zod.z.array(HookMappingSchema).optional(),
    gmail: HooksGmailSchema,
    internal: InternalHooksSchema
  }).strict().optional(),
  web: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    heartbeatSeconds: _zod.z.number().int().positive().optional(),
    reconnect: _zod.z.object({
      initialMs: _zod.z.number().positive().optional(),
      maxMs: _zod.z.number().positive().optional(),
      factor: _zod.z.number().positive().optional(),
      jitter: _zod.z.number().min(0).max(1).optional(),
      maxAttempts: _zod.z.number().int().min(0).optional()
    }).strict().optional(),
    whatsapp: _zod.z.object({
      keepAliveIntervalMs: _zod.z.number().int().positive().optional(),
      connectTimeoutMs: _zod.z.number().int().positive().optional(),
      defaultQueryTimeoutMs: _zod.z.number().int().positive().optional()
    }).strict().optional()
  }).strict().optional(),
  channels: ChannelsSchema,
  discovery: _zod.z.object({
    wideArea: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      domain: _zod.z.string().optional()
    }).strict().optional(),
    mdns: _zod.z.object({ mode: _zod.z.enum([
      "off",
      "minimal",
      "full"]
      ).optional() }).strict().optional()
  }).strict().optional(),
  canvasHost: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    root: _zod.z.string().optional(),
    port: _zod.z.number().int().positive().optional(),
    liveReload: _zod.z.boolean().optional()
  }).strict().optional(),
  talk: TalkSchema.optional(),
  gateway: _zod.z.object({
    port: _zod.z.number().int().positive().optional(),
    mode: _zod.z.union([_zod.z.literal("local"), _zod.z.literal("remote")]).optional(),
    bind: _zod.z.union([
    _zod.z.literal("auto"),
    _zod.z.literal("lan"),
    _zod.z.literal("loopback"),
    _zod.z.literal("custom"),
    _zod.z.literal("tailnet")]
    ).optional(),
    customBindHost: _zod.z.string().optional(),
    controlUi: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      basePath: _zod.z.string().optional(),
      root: _zod.z.string().optional(),
      embedSandbox: _zod.z.union([
      _zod.z.literal("strict"),
      _zod.z.literal("scripts"),
      _zod.z.literal("trusted")]
      ).optional(),
      allowExternalEmbedUrls: _zod.z.boolean().optional(),
      chatMessageMaxWidth: _zod.z.string().transform((value) => normalizeControlUiChatMessageMaxWidth(value)).refine((value) => isValidControlUiChatMessageMaxWidth(value), { message: "Expected a CSS width value such as 960px, 82%, min(1280px, 82%), or calc(100% - 2rem)" }).optional(),
      allowedOrigins: _zod.z.array(_zod.z.string()).optional(),
      dangerouslyAllowHostHeaderOriginFallback: _zod.z.boolean().optional(),
      allowInsecureAuth: _zod.z.boolean().optional(),
      dangerouslyDisableDeviceAuth: _zod.z.boolean().optional()
    }).strict().optional(),
    auth: _zod.z.object({
      mode: _zod.z.union([
      _zod.z.literal("none"),
      _zod.z.literal("token"),
      _zod.z.literal("password"),
      _zod.z.literal("trusted-proxy")]
      ).optional(),
      token: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
      password: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
      allowTailscale: _zod.z.boolean().optional(),
      rateLimit: _zod.z.object({
        maxAttempts: _zod.z.number().optional(),
        windowMs: _zod.z.number().optional(),
        lockoutMs: _zod.z.number().optional(),
        exemptLoopback: _zod.z.boolean().optional()
      }).strict().optional(),
      trustedProxy: _zod.z.object({
        userHeader: _zod.z.string().min(1, "userHeader is required for trusted-proxy mode"),
        requiredHeaders: _zod.z.array(_zod.z.string()).optional(),
        allowUsers: _zod.z.array(_zod.z.string()).optional(),
        allowLoopback: _zod.z.boolean().optional()
      }).strict().optional()
    }).strict().optional(),
    trustedProxies: _zod.z.array(_zod.z.string()).optional(),
    allowRealIpFallback: _zod.z.boolean().optional(),
    tools: _zod.z.object({
      deny: _zod.z.array(_zod.z.string()).optional(),
      allow: _zod.z.array(_zod.z.string()).optional()
    }).strict().optional(),
    webchat: _zod.z.object({ chatHistoryMaxChars: _zod.z.number().int().positive().max(5e5).optional() }).strict().optional(),
    handshakeTimeoutMs: _zod.z.number().int().min(1).optional(),
    channelHealthCheckMinutes: _zod.z.number().int().min(0).optional(),
    channelStaleEventThresholdMinutes: _zod.z.number().int().min(1).optional(),
    channelMaxRestartsPerHour: _zod.z.number().int().min(1).optional(),
    tailscale: _zod.z.object({
      mode: _zod.z.union([
      _zod.z.literal("off"),
      _zod.z.literal("serve"),
      _zod.z.literal("funnel")]
      ).optional(),
      resetOnExit: _zod.z.boolean().optional()
    }).strict().optional(),
    remote: _zod.z.object({
      url: _zod.z.string().optional(),
      transport: _zod.z.union([_zod.z.literal("ssh"), _zod.z.literal("direct")]).optional(),
      token: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
      password: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
      tlsFingerprint: _zod.z.string().optional(),
      sshTarget: _zod.z.string().optional(),
      sshIdentity: _zod.z.string().optional()
    }).strict().optional(),
    reload: _zod.z.object({
      mode: _zod.z.union([
      _zod.z.literal("off"),
      _zod.z.literal("restart"),
      _zod.z.literal("hot"),
      _zod.z.literal("hybrid")]
      ).optional(),
      debounceMs: _zod.z.number().int().min(0).optional(),
      deferralTimeoutMs: _zod.z.number().int().min(0).optional()
    }).strict().optional(),
    tls: _zod.z.object({
      enabled: _zod.z.boolean().optional(),
      autoGenerate: _zod.z.boolean().optional(),
      certPath: _zod.z.string().optional(),
      keyPath: _zod.z.string().optional(),
      caPath: _zod.z.string().optional()
    }).optional(),
    http: _zod.z.object({
      endpoints: _zod.z.object({
        chatCompletions: _zod.z.object({
          enabled: _zod.z.boolean().optional(),
          maxBodyBytes: _zod.z.number().int().positive().optional(),
          maxImageParts: _zod.z.number().int().nonnegative().optional(),
          maxTotalImageBytes: _zod.z.number().int().positive().optional(),
          images: _zod.z.object({ ...ResponsesEndpointUrlFetchShape }).strict().optional()
        }).strict().optional(),
        responses: _zod.z.object({
          enabled: _zod.z.boolean().optional(),
          maxBodyBytes: _zod.z.number().int().positive().optional(),
          maxUrlParts: _zod.z.number().int().nonnegative().optional(),
          files: _zod.z.object({
            ...ResponsesEndpointUrlFetchShape,
            maxChars: _zod.z.number().int().positive().optional(),
            pdf: _zod.z.object({
              maxPages: _zod.z.number().int().positive().optional(),
              maxPixels: _zod.z.number().int().positive().optional(),
              minTextChars: _zod.z.number().int().nonnegative().optional()
            }).strict().optional()
          }).strict().optional(),
          images: _zod.z.object({ ...ResponsesEndpointUrlFetchShape }).strict().optional()
        }).strict().optional()
      }).strict().optional(),
      securityHeaders: _zod.z.object({ strictTransportSecurity: _zod.z.union([_zod.z.string(), _zod.z.literal(false)]).optional() }).strict().optional()
    }).strict().optional(),
    push: _zod.z.object({ apns: _zod.z.object({ relay: _zod.z.object({
          baseUrl: _zod.z.string().optional(),
          timeoutMs: _zod.z.number().int().positive().optional()
        }).strict().optional() }).strict().optional() }).strict().optional(),
    nodes: _zod.z.object({
      browser: _zod.z.object({
        mode: _zod.z.union([
        _zod.z.literal("auto"),
        _zod.z.literal("manual"),
        _zod.z.literal("off")]
        ).optional(),
        node: _zod.z.string().optional()
      }).strict().optional(),
      pairing: _zod.z.object({ autoApproveCidrs: _zod.z.array(_zod.z.string()).optional() }).strict().optional(),
      allowCommands: _zod.z.array(_zod.z.string()).optional(),
      denyCommands: _zod.z.array(_zod.z.string()).optional()
    }).strict().optional()
  }).strict().superRefine((gateway, ctx) => {
    const effectiveHealthCheckMinutes = gateway.channelHealthCheckMinutes ?? 5;
    if (gateway.channelStaleEventThresholdMinutes != null && effectiveHealthCheckMinutes !== 0 && gateway.channelStaleEventThresholdMinutes < effectiveHealthCheckMinutes) ctx.addIssue({
      code: _zod.z.ZodIssueCode.custom,
      path: ["channelStaleEventThresholdMinutes"],
      message: "channelStaleEventThresholdMinutes should be >= channelHealthCheckMinutes to avoid delayed stale detection"
    });
  }).optional(),
  memory: MemorySchema,
  mcp: McpConfigSchema,
  skills: _zod.z.object({
    allowBundled: _zod.z.array(_zod.z.string()).optional(),
    load: _zod.z.object({
      extraDirs: _zod.z.array(_zod.z.string()).optional(),
      watch: _zod.z.boolean().optional(),
      watchDebounceMs: _zod.z.number().int().min(0).optional()
    }).strict().optional(),
    install: _zod.z.object({
      preferBrew: _zod.z.boolean().optional(),
      nodeManager: _zod.z.union([
      _zod.z.literal("npm"),
      _zod.z.literal("pnpm"),
      _zod.z.literal("yarn"),
      _zod.z.literal("bun")]
      ).optional()
    }).strict().optional(),
    limits: _zod.z.object({
      maxCandidatesPerRoot: _zod.z.number().int().min(1).optional(),
      maxSkillsLoadedPerSource: _zod.z.number().int().min(1).optional(),
      maxSkillsInPrompt: _zod.z.number().int().min(0).optional(),
      maxSkillsPromptChars: _zod.z.number().int().min(0).optional(),
      maxSkillFileBytes: _zod.z.number().int().min(0).optional()
    }).strict().optional(),
    entries: _zod.z.record(_zod.z.string(), SkillEntrySchema).optional()
  }).strict().optional(),
  plugins: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    allow: _zod.z.array(_zod.z.string()).optional(),
    deny: _zod.z.array(_zod.z.string()).optional(),
    load: _zod.z.object({ paths: _zod.z.array(_zod.z.string()).optional() }).strict().optional(),
    slots: _zod.z.object({
      memory: _zod.z.string().optional(),
      contextEngine: _zod.z.string().optional()
    }).strict().optional(),
    entries: _zod.z.record(_zod.z.string(), PluginEntrySchema).optional(),
    bundledDiscovery: _zod.z.enum(["compat", "allowlist"]).optional()
  }).strict().optional(),
  surfaces: _zod.z.record(_zod.z.string(), _zod.z.object({
    silentReply: SilentReplyPolicyConfigSchema.optional(),
    silentReplyRewrite: SilentReplyRewriteConfigSchema.optional()
  }).strict()).optional(),
  proxy: ProxyConfigSchema
}).strict().superRefine((cfg, ctx) => {
  const agents = cfg.agents?.list ?? [];
  if (agents.length === 0) return;
  const agentIds = new Set(agents.map((agent) => agent.id));
  const broadcast = cfg.broadcast;
  if (!broadcast) return;
  for (const [peerId, ids] of Object.entries(broadcast)) {
    if (peerId === "strategy") continue;
    if (!Array.isArray(ids)) continue;
    for (let idx = 0; idx < ids.length; idx += 1) {
      const agentId = ids[idx];
      if (!agentIds.has(agentId)) ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        path: [
        "broadcast",
        peerId,
        idx],

        message: `Unknown agent id "${agentId}" (not in agents.list).`
      });
    }
  }
});
//#endregion /* v9-f39e10f0990f33d2 */
