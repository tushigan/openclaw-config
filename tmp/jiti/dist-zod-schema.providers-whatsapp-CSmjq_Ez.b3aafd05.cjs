"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = exports.s = exports.r = exports.o = exports.n = exports.l = exports.i = exports.c = exports.a = void 0;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _typesSecretsCL51SR4g = require("./types.secrets-CL51SR4g.js");
var _stringNormalizationC5SGsaST = require("./string-normalization-C5SGsaST.js");
var _zodSchemaAgentRuntimeBgmaoJWM = require("./zod-schema.agent-runtime-BgmaoJWM.js");
var _zodSchemaCoreB8hU4HYi = require("./zod-schema.core-B8hU4HYi.js");
var _zodSchemaSensitive4zM6OUv = require("./zod-schema.sensitive-4zM6OUv7.js");
var _scpHostDNpLXeIY = require("./scp-host-DNpLXeIY.js");
var _inboundPathPolicyCRVCy_2Y = require("./inbound-path-policy-CRVCy_2Y.js");
var _customCommandConfigCEx1DXac = require("./custom-command-config-CEx1DXac.js");
var _accountLookupDimKmpQR = require("./account-lookup-DimKmpQR.js");
var _zod = require("zod");
//#region src/config/zod-schema.channels.ts
const ChannelHeartbeatVisibilitySchema = exports.l = _zod.z.object({
  showOk: _zod.z.boolean().optional(),
  showAlerts: _zod.z.boolean().optional(),
  useIndicator: _zod.z.boolean().optional()
}).strict().optional();
const ChannelHealthMonitorSchema = _zod.z.object({ enabled: _zod.z.boolean().optional() }).strict().optional();
//#endregion
//#region src/config/zod-schema.secret-input-validation.ts
function forEachEnabledAccount(accounts, run) {
  if (!accounts) return;
  for (const [accountId, account] of Object.entries(accounts)) {
    if (!account || account.enabled === false) continue;
    run(accountId, account);
  }
}
function validateTelegramWebhookSecretRequirements(value, ctx) {
  const baseWebhookUrl = (0, _stringCoerceBje8XVt.c)(value.webhookUrl) ?? "";
  const hasBaseWebhookSecret = (0, _typesSecretsCL51SR4g.s)(value.webhookSecret);
  if (baseWebhookUrl && !hasBaseWebhookSecret) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    message: "channels.telegram.webhookUrl requires channels.telegram.webhookSecret",
    path: ["webhookSecret"]
  });
  forEachEnabledAccount(value.accounts, (accountId, account) => {
    if (!((0, _stringCoerceBje8XVt.c)(account.webhookUrl) ?? "")) return;
    if (!(0, _typesSecretsCL51SR4g.s)(account.webhookSecret) && !hasBaseWebhookSecret) ctx.addIssue({
      code: _zod.z.ZodIssueCode.custom,
      message: "channels.telegram.accounts.*.webhookUrl requires channels.telegram.webhookSecret or channels.telegram.accounts.*.webhookSecret",
      path: [
      "accounts",
      accountId,
      "webhookSecret"]

    });
  });
}
function validateSlackSigningSecretRequirements(value, ctx) {
  const baseMode = value.mode === "http" || value.mode === "socket" ? value.mode : "socket";
  if (baseMode === "http" && !(0, _typesSecretsCL51SR4g.s)(value.signingSecret)) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    message: "channels.slack.mode=\"http\" requires channels.slack.signingSecret",
    path: ["signingSecret"]
  });
  forEachEnabledAccount(value.accounts, (accountId, account) => {
    if ((account.mode === "http" || account.mode === "socket" ? account.mode : baseMode) !== "http") return;
    if (!(0, _typesSecretsCL51SR4g.s)(account.signingSecret ?? value.signingSecret)) ctx.addIssue({
      code: _zod.z.ZodIssueCode.custom,
      message: "channels.slack.accounts.*.mode=\"http\" requires channels.slack.signingSecret or channels.slack.accounts.*.signingSecret",
      path: [
      "accounts",
      accountId,
      "signingSecret"]

    });
  });
}
//#endregion
//#region src/config/zod-schema.providers-core.ts
const ToolPolicyBySenderSchema$1 = _zod.z.record(_zod.z.string(), _zodSchemaAgentRuntimeBgmaoJWM.l).optional();
const DiscordIdSchema = _zod.z.union([_zod.z.string(), _zod.z.number()]).transform((value, ctx) => {
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || value < 0) {
      ctx.addIssue({
        code: _zod.z.ZodIssueCode.custom,
        message: `Discord ID "${String(value)}" is not a valid non-negative safe integer. Wrap it in quotes in your config file.`
      });
      return _zod.z.NEVER;
    }
    return String(value);
  }
  return value;
}).pipe(_zod.z.string());
const DiscordIdListSchema = _zod.z.array(DiscordIdSchema);
const DiscordSnowflakeStringSchema = _zod.z.string().regex(/^\d+$/, "Discord user ID must be numeric");
const TelegramInlineButtonsScopeSchema = _zod.z.enum([
"off",
"dm",
"group",
"all",
"allowlist"]
);
const TelegramIdListSchema = _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()]));
const TelegramCapabilitiesSchema = _zod.z.union([_zod.z.array(_zod.z.string()), _zod.z.object({ inlineButtons: TelegramInlineButtonsScopeSchema.optional() }).strict()]);
const TextChunkModeSchema = _zod.z.enum(["length", "newline"]);
const UnifiedStreamingModeSchema = _zod.z.enum([
"off",
"partial",
"block",
"progress"]
);
const ChannelStreamingBlockSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  coalesce: _zodSchemaCoreB8hU4HYi.n.optional()
}).strict();
const ChannelStreamingPreviewSchema = _zod.z.object({
  chunk: _zodSchemaCoreB8hU4HYi.t.optional(),
  toolProgress: _zod.z.boolean().optional(),
  commandText: _zod.z.enum(["raw", "status"]).optional()
}).strict();
const ChannelStreamingProgressSchema = _zod.z.object({
  label: _zod.z.union([_zod.z.string(), _zod.z.literal(false)]).optional(),
  labels: _zod.z.array(_zod.z.string()).optional(),
  maxLines: _zod.z.number().int().positive().optional(),
  render: _zod.z.enum(["text", "rich"]).optional(),
  toolProgress: _zod.z.boolean().optional(),
  commandText: _zod.z.enum(["raw", "status"]).optional()
}).strict();
const ChannelPreviewStreamingConfigSchema = _zod.z.object({
  mode: UnifiedStreamingModeSchema.optional(),
  chunkMode: TextChunkModeSchema.optional(),
  preview: ChannelStreamingPreviewSchema.optional(),
  progress: ChannelStreamingProgressSchema.optional(),
  block: ChannelStreamingBlockSchema.optional()
}).strict();
const SlackStreamingConfigSchema = ChannelPreviewStreamingConfigSchema.extend({ nativeTransport: _zod.z.boolean().optional() }).strict();
const SlackCapabilitiesSchema = _zod.z.union([_zod.z.array(_zod.z.string()), _zod.z.object({ interactiveReplies: _zod.z.boolean().optional() }).strict()]);
const TelegramErrorPolicySchema = _zod.z.enum([
"always",
"once",
"silent"]
).optional();
const TelegramCustomCommandConfig = {
  label: "Telegram",
  pattern: /^[a-z0-9_]{1,32}$/,
  patternDescription: "use a-z, 0-9, underscore; max 32 chars"
};
const TelegramTopicSchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  ingest: _zod.z.boolean().optional(),
  disableAudioPreflight: _zod.z.boolean().optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional(),
  skills: _zod.z.array(_zod.z.string()).optional(),
  enabled: _zod.z.boolean().optional(),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  systemPrompt: _zod.z.string().optional(),
  agentId: _zod.z.string().optional(),
  errorPolicy: TelegramErrorPolicySchema,
  errorCooldownMs: _zod.z.number().int().nonnegative().optional()
}).strict();
const TelegramGroupSchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  ingest: _zod.z.boolean().optional(),
  disableAudioPreflight: _zod.z.boolean().optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  skills: _zod.z.array(_zod.z.string()).optional(),
  enabled: _zod.z.boolean().optional(),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  systemPrompt: _zod.z.string().optional(),
  topics: _zod.z.record(_zod.z.string(), TelegramTopicSchema.optional()).optional(),
  errorPolicy: TelegramErrorPolicySchema,
  errorCooldownMs: _zod.z.number().int().nonnegative().optional()
}).strict();
const TelegramDmThreadRepliesSchema = _zod.z.enum([
"off",
"inbound",
"always"]
);
const TelegramDmSchema = _zod.z.object({ threadReplies: TelegramDmThreadRepliesSchema.optional() }).strict();
const AutoTopicLabelSchema = _zod.z.union([_zod.z.boolean(), _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  prompt: _zod.z.string().optional()
}).strict()]).optional();
const TelegramDirectSchema = _zod.z.object({
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional(),
  threadReplies: _zod.z.enum([
  "off",
  "inbound",
  "always"]
  ).optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  skills: _zod.z.array(_zod.z.string()).optional(),
  enabled: _zod.z.boolean().optional(),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  systemPrompt: _zod.z.string().optional(),
  topics: _zod.z.record(_zod.z.string(), TelegramTopicSchema.optional()).optional(),
  errorPolicy: TelegramErrorPolicySchema,
  errorCooldownMs: _zod.z.number().int().nonnegative().optional(),
  requireTopic: _zod.z.boolean().optional(),
  autoTopicLabel: AutoTopicLabelSchema
}).strict();
const TelegramCustomCommandSchema = _zod.z.object({
  command: _zod.z.string().overwrite(_customCommandConfigCEx1DXac.n),
  description: _zod.z.string().overwrite(_customCommandConfigCEx1DXac.t)
}).strict();
const validateTelegramCustomCommands = (value, ctx) => {
  if (!value.customCommands || value.customCommands.length === 0) return;
  const { issues } = (0, _customCommandConfigCEx1DXac.r)({
    commands: value.customCommands,
    checkReserved: false,
    checkDuplicates: false,
    config: TelegramCustomCommandConfig
  });
  for (const issue of issues) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: [
    "customCommands",
    issue.index,
    issue.field],

    message: issue.message
  });
};
const TelegramAccountSchemaBase = _zod.z.object({
  name: _zod.z.string().optional(),
  capabilities: TelegramCapabilitiesSchema.optional(),
  execApprovals: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    approvers: TelegramIdListSchema.optional(),
    agentFilter: _zod.z.array(_zod.z.string()).optional(),
    sessionFilter: _zod.z.array(_zod.z.string()).optional(),
    target: _zod.z.enum([
    "dm",
    "channel",
    "both"]
    ).optional()
  }).strict().optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  enabled: _zod.z.boolean().optional(),
  commands: _zodSchemaCoreB8hU4HYi.v,
  customCommands: _zod.z.array(TelegramCustomCommandSchema).optional(),
  configWrites: _zod.z.boolean().optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional().default("pairing"),
  botToken: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  tokenFile: _zod.z.string().optional(),
  replyToMode: _zodSchemaCoreB8hU4HYi.x.optional(),
  dm: TelegramDmSchema.optional(),
  groups: _zod.z.record(_zod.z.string(), TelegramGroupSchema.optional()).optional(),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  defaultTo: _zod.z.union([_zod.z.string(), _zod.z.number()]).optional(),
  groupAllowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  direct: _zod.z.record(_zod.z.string(), TelegramDirectSchema.optional()).optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  streaming: ChannelPreviewStreamingConfigSchema.optional(),
  mediaMaxMb: _zod.z.number().positive().optional(),
  timeoutSeconds: _zod.z.number().int().positive().optional(),
  mediaGroupFlushMs: _zod.z.number().int().min(10).max(6e4).optional().describe("Buffer window in milliseconds for Telegram media groups/albums before dispatching them as one inbound message. Default: 500."),
  pollingStallThresholdMs: _zod.z.number().int().min(3e4).max(6e5).optional(),
  retry: _zodSchemaCoreB8hU4HYi.S,
  network: _zod.z.object({
    autoSelectFamily: _zod.z.boolean().optional(),
    dnsResultOrder: _zod.z.enum(["ipv4first", "verbatim"]).optional(),
    dangerouslyAllowPrivateNetwork: _zod.z.boolean().optional().describe("Dangerous opt-in for trusted Telegram fake-IP or transparent-proxy environments where api.telegram.org resolves to private/internal/special-use addresses during media downloads.")
  }).strict().optional(),
  proxy: _zod.z.string().optional(),
  webhookUrl: _zod.z.string().optional().describe("Public HTTPS webhook URL registered with Telegram for inbound updates. This must be internet-reachable and requires channels.telegram.webhookSecret."),
  webhookSecret: _zodSchemaCoreB8hU4HYi.C.optional().describe("Secret token sent to Telegram during webhook registration and verified on inbound webhook requests. Telegram returns this value for verification; this is not the gateway auth token and not the bot token.").register(_zodSchemaSensitive4zM6OUv.t),
  webhookPath: _zod.z.string().optional().describe("Local webhook route path served by the gateway listener. Defaults to /telegram-webhook."),
  webhookHost: _zod.z.string().optional().describe("Local bind host for the webhook listener. Defaults to 127.0.0.1; keep loopback unless you intentionally expose direct ingress."),
  webhookPort: _zod.z.number().int().nonnegative().optional().describe("Local bind port for the webhook listener. Defaults to 8787; set to 0 to let the OS assign an ephemeral port."),
  webhookCertPath: _zod.z.string().optional().describe("Path to the self-signed certificate (PEM) to upload to Telegram during webhook registration. Required for self-signed certs (direct IP or no domain)."),
  actions: _zod.z.object({
    reactions: _zod.z.boolean().optional(),
    sendMessage: _zod.z.boolean().optional(),
    poll: _zod.z.boolean().optional(),
    deleteMessage: _zod.z.boolean().optional(),
    editMessage: _zod.z.boolean().optional(),
    sticker: _zod.z.boolean().optional(),
    createForumTopic: _zod.z.boolean().optional(),
    editForumTopic: _zod.z.boolean().optional()
  }).strict().optional(),
  threadBindings: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    idleHours: _zod.z.number().nonnegative().optional(),
    maxAgeHours: _zod.z.number().nonnegative().optional(),
    spawnSessions: _zod.z.boolean().optional(),
    defaultSpawnContext: _zod.z.enum(["isolated", "fork"]).optional(),
    spawnSubagentSessions: _zod.z.boolean().optional(),
    spawnAcpSessions: _zod.z.boolean().optional()
  }).strict().optional(),
  reactionNotifications: _zod.z.enum([
  "off",
  "own",
  "all"]
  ).optional(),
  reactionLevel: _zod.z.enum([
  "off",
  "ack",
  "minimal",
  "extensive"]
  ).optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  linkPreview: _zod.z.boolean().optional(),
  silentErrorReplies: _zod.z.boolean().optional(),
  responsePrefix: _zod.z.string().optional(),
  ackReaction: _zod.z.string().optional(),
  errorPolicy: TelegramErrorPolicySchema,
  errorCooldownMs: _zod.z.number().int().nonnegative().optional(),
  apiRoot: _zod.z.string().url().optional(),
  trustedLocalFileRoots: _zod.z.array(_zod.z.string()).optional().describe("Trusted local filesystem roots for self-hosted Telegram Bot API absolute file_path values. Only absolute paths under these roots are read directly; all other absolute paths are rejected."),
  autoTopicLabel: AutoTopicLabelSchema
}).strict();
const TelegramAccountSchema = TelegramAccountSchemaBase.superRefine((value, ctx) => {
  validateTelegramCustomCommands(value, ctx);
});
const TelegramConfigSchema = exports.c = TelegramAccountSchemaBase.extend({
  accounts: _zod.z.record(_zod.z.string(), TelegramAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional()
}).superRefine((value, ctx) => {
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.telegram.dmPolicy=\"open\" requires channels.telegram.allowFrom to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.telegram.dmPolicy=\"allowlist\" requires channels.telegram.allowFrom to contain at least one sender ID"
  });
  validateTelegramCustomCommands(value, ctx);
  if (value.accounts) for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    const effectivePolicy = account.dmPolicy ?? value.dmPolicy;
    const effectiveAllowFrom = account.allowFrom ?? value.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.telegram.accounts.*.dmPolicy=\"open\" requires channels.telegram.accounts.*.allowFrom (or channels.telegram.allowFrom) to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.telegram.accounts.*.dmPolicy=\"allowlist\" requires channels.telegram.accounts.*.allowFrom (or channels.telegram.allowFrom) to contain at least one sender ID"
    });
  }
  if (!value.accounts) {
    validateTelegramWebhookSecretRequirements(value, ctx);
    return;
  }
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    if (account.enabled === false) continue;
    const effectiveDmPolicy = account.dmPolicy ?? value.dmPolicy;
    const effectiveAllowFrom = Array.isArray(account.allowFrom) ? account.allowFrom : value.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectiveDmPolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.telegram.accounts.*.dmPolicy=\"open\" requires channels.telegram.allowFrom or channels.telegram.accounts.*.allowFrom to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectiveDmPolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.telegram.accounts.*.dmPolicy=\"allowlist\" requires channels.telegram.allowFrom or channels.telegram.accounts.*.allowFrom to contain at least one sender ID"
    });
  }
  validateTelegramWebhookSecretRequirements(value, ctx);
});
const DiscordDmSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  policy: _zodSchemaCoreB8hU4HYi.o.optional(),
  allowFrom: DiscordIdListSchema.optional(),
  groupEnabled: _zod.z.boolean().optional(),
  groupChannels: DiscordIdListSchema.optional()
}).strict();
const DiscordThreadSchema = _zod.z.object({ inheritParent: _zod.z.boolean().optional() }).strict();
const DiscordGuildChannelSchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  ignoreOtherMentions: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  skills: _zod.z.array(_zod.z.string()).optional(),
  enabled: _zod.z.boolean().optional(),
  users: DiscordIdListSchema.optional(),
  roles: DiscordIdListSchema.optional(),
  systemPrompt: _zod.z.string().optional(),
  includeThreadStarter: _zod.z.boolean().optional(),
  autoThread: _zod.z.boolean().optional(),
  /** Naming strategy for auto-created threads. "message" uses message text; "generated" creates an LLM title after thread creation. */
  autoThreadName: _zod.z.enum(["message", "generated"]).optional(),
  /** Archive duration for auto-created threads in minutes. Discord supports 60, 1440 (1 day), 4320 (3 days), 10080 (1 week). Default: 60. */
  autoArchiveDuration: _zod.z.union([
  _zod.z.enum([
  "60",
  "1440",
  "4320",
  "10080"]
  ),
  _zod.z.literal(60),
  _zod.z.literal(1440),
  _zod.z.literal(4320),
  _zod.z.literal(10080)]
  ).optional()
}).strict();
const DiscordGuildSchema = _zod.z.object({
  slug: _zod.z.string().optional(),
  requireMention: _zod.z.boolean().optional(),
  ignoreOtherMentions: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  reactionNotifications: _zod.z.enum([
  "off",
  "own",
  "all",
  "allowlist"]
  ).optional(),
  users: DiscordIdListSchema.optional(),
  roles: DiscordIdListSchema.optional(),
  channels: _zod.z.record(_zod.z.string(), DiscordGuildChannelSchema.optional()).optional()
}).strict();
const DiscordUiSchema = _zod.z.object({ components: _zod.z.object({ accentColor: _zodSchemaCoreB8hU4HYi.u.optional() }).strict().optional() }).strict().optional();
const DiscordVoiceAutoJoinSchema = _zod.z.object({
  guildId: _zod.z.string().min(1),
  channelId: _zod.z.string().min(1)
}).strict();
const DiscordVoiceSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  model: _zod.z.string().min(1).optional(),
  autoJoin: _zod.z.array(DiscordVoiceAutoJoinSchema).optional(),
  daveEncryption: _zod.z.boolean().optional(),
  decryptionFailureTolerance: _zod.z.number().int().min(0).optional(),
  connectTimeoutMs: _zod.z.number().int().positive().max(12e4).optional(),
  reconnectGraceMs: _zod.z.number().int().positive().max(12e4).optional(),
  captureSilenceGraceMs: _zod.z.number().int().positive().max(3e4).optional(),
  tts: _zodSchemaCoreB8hU4HYi.j.optional()
}).strict().optional();
const DiscordAccountSchema = _zod.z.object({
  name: _zod.z.string().optional(),
  capabilities: _zod.z.array(_zod.z.string()).optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  enabled: _zod.z.boolean().optional(),
  commands: _zodSchemaCoreB8hU4HYi.v,
  configWrites: _zod.z.boolean().optional(),
  token: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  applicationId: DiscordIdSchema.optional(),
  proxy: _zod.z.string().optional(),
  gatewayInfoTimeoutMs: _zod.z.number().int().positive().max(12e4).optional(),
  gatewayReadyTimeoutMs: _zod.z.number().int().positive().max(12e4).optional(),
  gatewayRuntimeReadyTimeoutMs: _zod.z.number().int().positive().max(12e4).optional(),
  allowBots: _zod.z.union([_zod.z.boolean(), _zod.z.literal("mentions")]).optional(),
  dangerouslyAllowNameMatching: _zod.z.boolean().optional(),
  mentionAliases: _zod.z.record(_zod.z.string(), DiscordSnowflakeStringSchema).optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  streaming: ChannelPreviewStreamingConfigSchema.optional(),
  maxLinesPerMessage: _zod.z.number().int().positive().optional(),
  mediaMaxMb: _zod.z.number().positive().optional(),
  retry: _zodSchemaCoreB8hU4HYi.S,
  actions: _zod.z.object({
    reactions: _zod.z.boolean().optional(),
    stickers: _zod.z.boolean().optional(),
    emojiUploads: _zod.z.boolean().optional(),
    stickerUploads: _zod.z.boolean().optional(),
    polls: _zod.z.boolean().optional(),
    permissions: _zod.z.boolean().optional(),
    messages: _zod.z.boolean().optional(),
    threads: _zod.z.boolean().optional(),
    pins: _zod.z.boolean().optional(),
    search: _zod.z.boolean().optional(),
    memberInfo: _zod.z.boolean().optional(),
    roleInfo: _zod.z.boolean().optional(),
    roles: _zod.z.boolean().optional(),
    channelInfo: _zod.z.boolean().optional(),
    voiceStatus: _zod.z.boolean().optional(),
    events: _zod.z.boolean().optional(),
    moderation: _zod.z.boolean().optional(),
    channels: _zod.z.boolean().optional(),
    presence: _zod.z.boolean().optional()
  }).strict().optional(),
  replyToMode: _zodSchemaCoreB8hU4HYi.x.optional(),
  thread: DiscordThreadSchema.optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional(),
  allowFrom: DiscordIdListSchema.optional(),
  defaultTo: _zod.z.string().optional(),
  dm: DiscordDmSchema.optional(),
  guilds: _zod.z.record(_zod.z.string(), DiscordGuildSchema.optional()).optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  execApprovals: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    approvers: DiscordIdListSchema.optional(),
    agentFilter: _zod.z.array(_zod.z.string()).optional(),
    sessionFilter: _zod.z.array(_zod.z.string()).optional(),
    cleanupAfterResolve: _zod.z.boolean().optional(),
    target: _zod.z.enum([
    "dm",
    "channel",
    "both"]
    ).optional()
  }).strict().optional(),
  agentComponents: _zod.z.object({ enabled: _zod.z.boolean().optional() }).strict().optional(),
  ui: DiscordUiSchema,
  slashCommand: _zod.z.object({ ephemeral: _zod.z.boolean().optional() }).strict().optional(),
  threadBindings: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    idleHours: _zod.z.number().nonnegative().optional(),
    maxAgeHours: _zod.z.number().nonnegative().optional(),
    spawnSessions: _zod.z.boolean().optional(),
    defaultSpawnContext: _zod.z.enum(["isolated", "fork"]).optional(),
    spawnSubagentSessions: _zod.z.boolean().optional(),
    spawnAcpSessions: _zod.z.boolean().optional()
  }).strict().optional(),
  intents: _zod.z.object({
    presence: _zod.z.boolean().optional(),
    guildMembers: _zod.z.boolean().optional(),
    voiceStates: _zod.z.boolean().optional()
  }).strict().optional(),
  voice: DiscordVoiceSchema,
  pluralkit: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    token: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t)
  }).strict().optional(),
  responsePrefix: _zod.z.string().optional(),
  ackReaction: _zod.z.string().optional(),
  ackReactionScope: _zod.z.enum([
  "group-mentions",
  "group-all",
  "direct",
  "all",
  "off",
  "none"]
  ).optional(),
  activity: _zod.z.string().optional(),
  status: _zod.z.enum([
  "online",
  "dnd",
  "idle",
  "invisible"]
  ).optional(),
  autoPresence: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    intervalMs: _zod.z.number().int().positive().optional(),
    minUpdateIntervalMs: _zod.z.number().int().positive().optional(),
    healthyText: _zod.z.string().optional(),
    degradedText: _zod.z.string().optional(),
    exhaustedText: _zod.z.string().optional()
  }).strict().optional(),
  activityType: _zod.z.union([
  _zod.z.literal(0),
  _zod.z.literal(1),
  _zod.z.literal(2),
  _zod.z.literal(3),
  _zod.z.literal(4),
  _zod.z.literal(5)]
  ).optional(),
  activityUrl: _zod.z.string().url().optional(),
  inboundWorker: _zod.z.object({ runTimeoutMs: _zod.z.number().int().nonnegative().optional() }).strict().optional(),
  eventQueue: _zod.z.object({
    listenerTimeout: _zod.z.number().int().positive().optional(),
    maxQueueSize: _zod.z.number().int().positive().optional(),
    maxConcurrency: _zod.z.number().int().positive().optional()
  }).strict().optional()
}).strict().superRefine((value, ctx) => {
  const activityText = (0, _stringCoerceBje8XVt.c)(value.activity) ?? "";
  const hasActivity = Boolean(activityText);
  const hasActivityType = value.activityType !== void 0;
  const activityUrl = (0, _stringCoerceBje8XVt.c)(value.activityUrl) ?? "";
  const hasActivityUrl = Boolean(activityUrl);
  if ((hasActivityType || hasActivityUrl) && !hasActivity) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    message: "channels.discord.activity is required when activityType or activityUrl is set",
    path: ["activity"]
  });
  if (value.activityType === 1 && !hasActivityUrl) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    message: "channels.discord.activityUrl is required when activityType is 1 (Streaming)",
    path: ["activityUrl"]
  });
  if (hasActivityUrl && value.activityType !== 1) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    message: "channels.discord.activityType must be 1 (Streaming) when activityUrl is set",
    path: ["activityType"]
  });
  const autoPresenceInterval = value.autoPresence?.intervalMs;
  const autoPresenceMinUpdate = value.autoPresence?.minUpdateIntervalMs;
  if (typeof autoPresenceInterval === "number" && typeof autoPresenceMinUpdate === "number" && autoPresenceMinUpdate > autoPresenceInterval) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    message: "channels.discord.autoPresence.minUpdateIntervalMs must be less than or equal to channels.discord.autoPresence.intervalMs",
    path: ["autoPresence", "minUpdateIntervalMs"]
  });
});
const DiscordConfigSchema = exports.n = DiscordAccountSchema.extend({
  accounts: _zod.z.record(_zod.z.string(), DiscordAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional()
}).superRefine((value, ctx) => {
  const dmPolicy = value.dmPolicy ?? value.dm?.policy ?? "pairing";
  const allowFrom = value.allowFrom ?? value.dm?.allowFrom;
  const allowFromPath = value.allowFrom !== void 0 ? ["allowFrom"] : ["dm", "allowFrom"];
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: dmPolicy,
    allowFrom,
    ctx,
    path: [...allowFromPath],
    message: "channels.discord.dmPolicy=\"open\" requires channels.discord.allowFrom (or channels.discord.dm.allowFrom) to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: dmPolicy,
    allowFrom,
    ctx,
    path: [...allowFromPath],
    message: "channels.discord.dmPolicy=\"allowlist\" requires channels.discord.allowFrom (or channels.discord.dm.allowFrom) to contain at least one sender ID"
  });
  if (!value.accounts) return;
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    const effectivePolicy = account.dmPolicy ?? account.dm?.policy ?? value.dmPolicy ?? value.dm?.policy ?? "pairing";
    const effectiveAllowFrom = account.allowFrom ?? account.dm?.allowFrom ?? value.allowFrom ?? value.dm?.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.discord.accounts.*.dmPolicy=\"open\" requires channels.discord.accounts.*.allowFrom (or channels.discord.allowFrom) to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.discord.accounts.*.dmPolicy=\"allowlist\" requires channels.discord.accounts.*.allowFrom (or channels.discord.allowFrom) to contain at least one sender ID"
    });
  }
});
const GoogleChatDmSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  policy: _zodSchemaCoreB8hU4HYi.o.optional().default("pairing"),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional()
}).strict().superRefine((value, ctx) => {
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: value.policy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.googlechat.dm.policy=\"open\" requires channels.googlechat.dm.allowFrom to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: value.policy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.googlechat.dm.policy=\"allowlist\" requires channels.googlechat.dm.allowFrom to contain at least one sender ID"
  });
});
const GoogleChatGroupSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  requireMention: _zod.z.boolean().optional(),
  users: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  systemPrompt: _zod.z.string().optional()
}).strict();
const GoogleChatAccountSchema = _zod.z.object({
  name: _zod.z.string().optional(),
  capabilities: _zod.z.array(_zod.z.string()).optional(),
  enabled: _zod.z.boolean().optional(),
  configWrites: _zod.z.boolean().optional(),
  allowBots: _zod.z.boolean().optional(),
  dangerouslyAllowNameMatching: _zod.z.boolean().optional(),
  requireMention: _zod.z.boolean().optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  groupAllowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  groups: _zod.z.record(_zod.z.string(), GoogleChatGroupSchema.optional()).optional(),
  defaultTo: _zod.z.string().optional(),
  serviceAccount: _zod.z.union([
  _zod.z.string(),
  _zod.z.record(_zod.z.string(), _zod.z.unknown()),
  _zodSchemaCoreB8hU4HYi.T]
  ).optional().register(_zodSchemaSensitive4zM6OUv.t),
  serviceAccountRef: _zodSchemaCoreB8hU4HYi.T.optional().register(_zodSchemaSensitive4zM6OUv.t),
  serviceAccountFile: _zod.z.string().optional(),
  audienceType: _zod.z.enum(["app-url", "project-number"]).optional(),
  audience: _zod.z.string().optional(),
  appPrincipal: _zod.z.string().optional(),
  webhookPath: _zod.z.string().optional(),
  webhookUrl: _zod.z.string().optional(),
  botUser: _zod.z.string().optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  chunkMode: _zod.z.enum(["length", "newline"]).optional(),
  blockStreaming: _zod.z.boolean().optional(),
  blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
  mediaMaxMb: _zod.z.number().positive().optional(),
  replyToMode: _zodSchemaCoreB8hU4HYi.x.optional(),
  actions: _zod.z.object({ reactions: _zod.z.boolean().optional() }).strict().optional(),
  dm: GoogleChatDmSchema.optional(),
  healthMonitor: ChannelHealthMonitorSchema,
  typingIndicator: _zod.z.enum([
  "none",
  "message",
  "reaction"]
  ).optional(),
  responsePrefix: _zod.z.string().optional()
}).strict();
const GoogleChatConfigSchema = exports.r = GoogleChatAccountSchema.extend({
  accounts: _zod.z.record(_zod.z.string(), GoogleChatAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional()
});
const SlackDmSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  policy: _zodSchemaCoreB8hU4HYi.o.optional(),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  groupEnabled: _zod.z.boolean().optional(),
  groupChannels: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  replyToMode: _zodSchemaCoreB8hU4HYi.x.optional()
}).strict();
const SlackChannelSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  requireMention: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  allowBots: _zod.z.boolean().optional(),
  users: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  skills: _zod.z.array(_zod.z.string()).optional(),
  systemPrompt: _zod.z.string().optional()
}).strict();
const SlackThreadSchema = _zod.z.object({
  historyScope: _zod.z.enum(["thread", "channel"]).optional(),
  inheritParent: _zod.z.boolean().optional(),
  initialHistoryLimit: _zod.z.number().int().min(0).optional(),
  requireExplicitMention: _zod.z.boolean().optional()
}).strict();
const SlackReplyToModeByChatTypeSchema = _zod.z.object({
  direct: _zodSchemaCoreB8hU4HYi.x.optional(),
  group: _zodSchemaCoreB8hU4HYi.x.optional(),
  channel: _zodSchemaCoreB8hU4HYi.x.optional()
}).strict();
const SlackSocketModeSchema = _zod.z.object({
  clientPingTimeout: _zod.z.number().int().positive().optional(),
  serverPingTimeout: _zod.z.number().int().positive().optional(),
  pingPongLoggingEnabled: _zod.z.boolean().optional()
}).strict();
const SlackAccountSchema = _zod.z.object({
  name: _zod.z.string().optional(),
  mode: _zod.z.enum(["socket", "http"]).optional(),
  socketMode: SlackSocketModeSchema.optional(),
  signingSecret: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  webhookPath: _zod.z.string().optional(),
  capabilities: SlackCapabilitiesSchema.optional(),
  execApprovals: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    approvers: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
    agentFilter: _zod.z.array(_zod.z.string()).optional(),
    sessionFilter: _zod.z.array(_zod.z.string()).optional(),
    target: _zod.z.enum([
    "dm",
    "channel",
    "both"]
    ).optional()
  }).strict().optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  enabled: _zod.z.boolean().optional(),
  commands: _zodSchemaCoreB8hU4HYi.v,
  configWrites: _zod.z.boolean().optional(),
  botToken: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  appToken: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  userToken: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  userTokenReadOnly: _zod.z.boolean().optional().default(true),
  allowBots: _zod.z.boolean().optional(),
  dangerouslyAllowNameMatching: _zod.z.boolean().optional(),
  requireMention: _zod.z.boolean().optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional(),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  streaming: SlackStreamingConfigSchema.optional(),
  mediaMaxMb: _zod.z.number().positive().optional(),
  reactionNotifications: _zod.z.enum([
  "off",
  "own",
  "all",
  "allowlist"]
  ).optional(),
  reactionAllowlist: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  replyToMode: _zodSchemaCoreB8hU4HYi.x.optional(),
  replyToModeByChatType: SlackReplyToModeByChatTypeSchema.optional(),
  thread: SlackThreadSchema.optional(),
  actions: _zod.z.object({
    reactions: _zod.z.boolean().optional(),
    messages: _zod.z.boolean().optional(),
    pins: _zod.z.boolean().optional(),
    search: _zod.z.boolean().optional(),
    permissions: _zod.z.boolean().optional(),
    memberInfo: _zod.z.boolean().optional(),
    channelInfo: _zod.z.boolean().optional(),
    emojiList: _zod.z.boolean().optional()
  }).strict().optional(),
  slashCommand: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    name: _zod.z.string().optional(),
    sessionPrefix: _zod.z.string().optional(),
    ephemeral: _zod.z.boolean().optional()
  }).strict().optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional(),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  defaultTo: _zod.z.string().optional(),
  dm: SlackDmSchema.optional(),
  channels: _zod.z.record(_zod.z.string(), SlackChannelSchema.optional()).optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  responsePrefix: _zod.z.string().optional(),
  ackReaction: _zod.z.string().optional(),
  typingReaction: _zod.z.string().optional()
}).strict().superRefine(() => {});
const SlackConfigSchema = exports.s = SlackAccountSchema.safeExtend({
  mode: _zod.z.enum(["socket", "http"]).optional().default("socket"),
  signingSecret: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  webhookPath: _zod.z.string().optional().default("/slack/events"),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  accounts: _zod.z.record(_zod.z.string(), SlackAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional()
}).superRefine((value, ctx) => {
  const dmPolicy = value.dmPolicy ?? value.dm?.policy ?? "pairing";
  const allowFrom = value.allowFrom ?? value.dm?.allowFrom;
  const allowFromPath = value.allowFrom !== void 0 ? ["allowFrom"] : ["dm", "allowFrom"];
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: dmPolicy,
    allowFrom,
    ctx,
    path: [...allowFromPath],
    message: "channels.slack.dmPolicy=\"open\" requires channels.slack.allowFrom (or channels.slack.dm.allowFrom) to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: dmPolicy,
    allowFrom,
    ctx,
    path: [...allowFromPath],
    message: "channels.slack.dmPolicy=\"allowlist\" requires channels.slack.allowFrom (or channels.slack.dm.allowFrom) to contain at least one sender ID"
  });
  const baseMode = value.mode ?? "socket";
  if (!value.accounts) {
    validateSlackSigningSecretRequirements(value, ctx);
    return;
  }
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    if (account.enabled === false) continue;
    const accountMode = account.mode ?? baseMode;
    const effectivePolicy = account.dmPolicy ?? account.dm?.policy ?? value.dmPolicy ?? value.dm?.policy ?? "pairing";
    const effectiveAllowFrom = account.allowFrom ?? account.dm?.allowFrom ?? value.allowFrom ?? value.dm?.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.slack.accounts.*.dmPolicy=\"open\" requires channels.slack.accounts.*.allowFrom (or channels.slack.allowFrom) to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.slack.accounts.*.dmPolicy=\"allowlist\" requires channels.slack.accounts.*.allowFrom (or channels.slack.allowFrom) to contain at least one sender ID"
    });
    if (accountMode !== "http") continue;
  }
  validateSlackSigningSecretRequirements(value, ctx);
});
const SignalGroupEntrySchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  ingest: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1
}).strict();
const SignalGroupsSchema = _zod.z.record(_zod.z.string(), SignalGroupEntrySchema.optional()).optional();
const SignalAccountSchemaBase = _zod.z.object({
  name: _zod.z.string().optional(),
  capabilities: _zod.z.array(_zod.z.string()).optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  enabled: _zod.z.boolean().optional(),
  configWrites: _zod.z.boolean().optional(),
  account: _zod.z.string().optional(),
  accountUuid: _zod.z.string().optional(),
  httpUrl: _zod.z.string().optional(),
  httpHost: _zod.z.string().optional(),
  httpPort: _zod.z.number().int().positive().optional(),
  cliPath: _zodSchemaCoreB8hU4HYi.s.optional(),
  autoStart: _zod.z.boolean().optional(),
  startupTimeoutMs: _zod.z.number().int().min(1e3).max(12e4).optional(),
  receiveMode: _zod.z.union([_zod.z.literal("on-start"), _zod.z.literal("manual")]).optional(),
  ignoreAttachments: _zod.z.boolean().optional(),
  ignoreStories: _zod.z.boolean().optional(),
  sendReadReceipts: _zod.z.boolean().optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional().default("pairing"),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  defaultTo: _zod.z.string().optional(),
  groupAllowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  groups: SignalGroupsSchema,
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  chunkMode: _zod.z.enum(["length", "newline"]).optional(),
  blockStreaming: _zod.z.boolean().optional(),
  blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
  mediaMaxMb: _zod.z.number().int().positive().optional(),
  reactionNotifications: _zod.z.enum([
  "off",
  "own",
  "all",
  "allowlist"]
  ).optional(),
  reactionAllowlist: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  actions: _zod.z.object({ reactions: _zod.z.boolean().optional() }).strict().optional(),
  reactionLevel: _zod.z.enum([
  "off",
  "ack",
  "minimal",
  "extensive"]
  ).optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  responsePrefix: _zod.z.string().optional()
}).strict();
const SignalAccountSchema = SignalAccountSchemaBase;
const SignalConfigSchema = exports.o = SignalAccountSchemaBase.extend({
  accounts: _zod.z.record(_zod.z.string(), SignalAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional()
}).superRefine((value, ctx) => {
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.signal.dmPolicy=\"open\" requires channels.signal.allowFrom to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.signal.dmPolicy=\"allowlist\" requires channels.signal.allowFrom to contain at least one sender ID"
  });
  if (!value.accounts) return;
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    const effectivePolicy = account.dmPolicy ?? value.dmPolicy;
    const effectiveAllowFrom = account.allowFrom ?? value.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.signal.accounts.*.dmPolicy=\"open\" requires channels.signal.accounts.*.allowFrom (or channels.signal.allowFrom) to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.signal.accounts.*.dmPolicy=\"allowlist\" requires channels.signal.accounts.*.allowFrom (or channels.signal.allowFrom) to contain at least one sender ID"
    });
  }
});
const IrcGroupSchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  skills: _zod.z.array(_zod.z.string()).optional(),
  enabled: _zod.z.boolean().optional(),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  systemPrompt: _zod.z.string().optional()
}).strict();
const IrcNickServSchema = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  service: _zod.z.string().optional(),
  password: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  passwordFile: _zod.z.string().optional(),
  register: _zod.z.boolean().optional(),
  registerEmail: _zod.z.string().optional()
}).strict();
const IrcAccountSchemaBase = _zod.z.object({
  name: _zod.z.string().optional(),
  capabilities: _zod.z.array(_zod.z.string()).optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  enabled: _zod.z.boolean().optional(),
  configWrites: _zod.z.boolean().optional(),
  host: _zod.z.string().optional(),
  port: _zod.z.number().int().min(1).max(65535).optional(),
  tls: _zod.z.boolean().optional(),
  nick: _zod.z.string().optional(),
  username: _zod.z.string().optional(),
  realname: _zod.z.string().optional(),
  password: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  passwordFile: _zod.z.string().optional(),
  nickserv: IrcNickServSchema.optional(),
  channels: _zod.z.array(_zod.z.string()).optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional().default("pairing"),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  defaultTo: _zod.z.string().optional(),
  groupAllowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  groups: _zod.z.record(_zod.z.string(), IrcGroupSchema.optional()).optional(),
  mentionPatterns: _zod.z.array(_zod.z.string()).optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  chunkMode: _zod.z.enum(["length", "newline"]).optional(),
  blockStreaming: _zod.z.boolean().optional(),
  blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
  mediaMaxMb: _zod.z.number().positive().optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  responsePrefix: _zod.z.string().optional()
}).strict();
function refineIrcAllowFromAndNickserv(value, ctx) {
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.irc.dmPolicy=\"open\" requires channels.irc.allowFrom to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.irc.dmPolicy=\"allowlist\" requires channels.irc.allowFrom to contain at least one sender ID"
  });
  if (value.nickserv?.register && !value.nickserv.registerEmail?.trim()) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: ["nickserv", "registerEmail"],
    message: "channels.irc.nickserv.register=true requires channels.irc.nickserv.registerEmail"
  });
}
const IrcAccountSchema = IrcAccountSchemaBase.superRefine((value, ctx) => {
  if (value.nickserv?.register && !value.nickserv.registerEmail?.trim()) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: ["nickserv", "registerEmail"],
    message: "channels.irc.nickserv.register=true requires channels.irc.nickserv.registerEmail"
  });
});
IrcAccountSchemaBase.extend({
  accounts: _zod.z.record(_zod.z.string(), IrcAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional()
}).superRefine((value, ctx) => {
  refineIrcAllowFromAndNickserv(value, ctx);
  if (!value.accounts) return;
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    const effectivePolicy = account.dmPolicy ?? value.dmPolicy;
    const effectiveAllowFrom = account.allowFrom ?? value.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.irc.accounts.*.dmPolicy=\"open\" requires channels.irc.accounts.*.allowFrom (or channels.irc.allowFrom) to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.irc.accounts.*.dmPolicy=\"allowlist\" requires channels.irc.accounts.*.allowFrom (or channels.irc.allowFrom) to contain at least one sender ID"
    });
  }
});
const IMessageAccountSchemaBase = _zod.z.object({
  name: _zod.z.string().optional(),
  capabilities: _zod.z.array(_zod.z.string()).optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  enabled: _zod.z.boolean().optional(),
  configWrites: _zod.z.boolean().optional(),
  cliPath: _zodSchemaCoreB8hU4HYi.s.optional(),
  dbPath: _zod.z.string().optional(),
  remoteHost: _zod.z.string().refine(_scpHostDNpLXeIY.t, "expected SSH host or user@host (no spaces/options)").optional(),
  service: _zod.z.union([
  _zod.z.literal("imessage"),
  _zod.z.literal("sms"),
  _zod.z.literal("auto")]
  ).optional(),
  region: _zod.z.string().optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional().default("pairing"),
  allowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  defaultTo: _zod.z.string().optional(),
  groupAllowFrom: _zod.z.array(_zod.z.union([_zod.z.string(), _zod.z.number()])).optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  includeAttachments: _zod.z.boolean().optional(),
  attachmentRoots: _zod.z.array(_zod.z.string().refine(_inboundPathPolicyCRVCy_2Y.n, "expected absolute path root")).optional(),
  remoteAttachmentRoots: _zod.z.array(_zod.z.string().refine(_inboundPathPolicyCRVCy_2Y.n, "expected absolute path root")).optional(),
  mediaMaxMb: _zod.z.number().int().positive().optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  chunkMode: _zod.z.enum(["length", "newline"]).optional(),
  blockStreaming: _zod.z.boolean().optional(),
  blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
  groups: _zod.z.record(_zod.z.string(), _zod.z.object({
    requireMention: _zod.z.boolean().optional(),
    tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
    toolsBySender: ToolPolicyBySenderSchema$1
  }).strict().optional()).optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  responsePrefix: _zod.z.string().optional()
}).strict();
const IMessageAccountSchema = IMessageAccountSchemaBase;
const IMessageConfigSchema = exports.i = IMessageAccountSchemaBase.extend({
  accounts: _zod.z.record(_zod.z.string(), IMessageAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional()
}).superRefine((value, ctx) => {
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.imessage.dmPolicy=\"open\" requires channels.imessage.allowFrom to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.imessage.dmPolicy=\"allowlist\" requires channels.imessage.allowFrom to contain at least one sender ID"
  });
  if (!value.accounts) return;
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    const effectivePolicy = account.dmPolicy ?? value.dmPolicy;
    const effectiveAllowFrom = account.allowFrom ?? value.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.imessage.accounts.*.dmPolicy=\"open\" requires channels.imessage.accounts.*.allowFrom (or channels.imessage.allowFrom) to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.imessage.accounts.*.dmPolicy=\"allowlist\" requires channels.imessage.accounts.*.allowFrom (or channels.imessage.allowFrom) to contain at least one sender ID"
    });
  }
});
const BlueBubblesAllowFromEntry = _zod.z.union([_zod.z.string(), _zod.z.number()]);
const BlueBubblesActionSchema = _zod.z.object({
  reactions: _zod.z.boolean().optional(),
  edit: _zod.z.boolean().optional(),
  unsend: _zod.z.boolean().optional(),
  reply: _zod.z.boolean().optional(),
  sendWithEffect: _zod.z.boolean().optional(),
  renameGroup: _zod.z.boolean().optional(),
  setGroupIcon: _zod.z.boolean().optional(),
  addParticipant: _zod.z.boolean().optional(),
  removeParticipant: _zod.z.boolean().optional(),
  leaveGroup: _zod.z.boolean().optional(),
  sendAttachment: _zod.z.boolean().optional()
}).strict().optional();
const BlueBubblesGroupConfigSchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1
}).strict();
const BlueBubblesAccountSchemaBase = _zod.z.object({
  name: _zod.z.string().optional(),
  capabilities: _zod.z.array(_zod.z.string()).optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  configWrites: _zod.z.boolean().optional(),
  enabled: _zod.z.boolean().optional(),
  serverUrl: _zod.z.string().optional(),
  password: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  webhookPath: _zod.z.string().optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional().default("pairing"),
  allowFrom: _zod.z.array(BlueBubblesAllowFromEntry).optional(),
  groupAllowFrom: _zod.z.array(BlueBubblesAllowFromEntry).optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  sendTimeoutMs: _zod.z.number().int().positive().optional(),
  chunkMode: _zod.z.enum(["length", "newline"]).optional(),
  mediaMaxMb: _zod.z.number().int().positive().optional(),
  mediaLocalRoots: _zod.z.array(_zod.z.string()).optional(),
  sendReadReceipts: _zod.z.boolean().optional(),
  network: _zod.z.object({ dangerouslyAllowPrivateNetwork: _zod.z.boolean().optional() }).strict().optional(),
  blockStreaming: _zod.z.boolean().optional(),
  blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
  groups: _zod.z.record(_zod.z.string(), BlueBubblesGroupConfigSchema.optional()).optional(),
  enrichGroupParticipantsFromContacts: _zod.z.boolean().optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  responsePrefix: _zod.z.string().optional(),
  coalesceSameSenderDms: _zod.z.boolean().optional()
}).strict();
const BlueBubblesAccountSchema = BlueBubblesAccountSchemaBase;
BlueBubblesAccountSchemaBase.extend({
  accounts: _zod.z.record(_zod.z.string(), BlueBubblesAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional(),
  actions: BlueBubblesActionSchema
}).superRefine((value, ctx) => {
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.bluebubbles.dmPolicy=\"open\" requires channels.bluebubbles.allowFrom to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.bluebubbles.dmPolicy=\"allowlist\" requires channels.bluebubbles.allowFrom to contain at least one sender ID"
  });
  if (!value.accounts) return;
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    const effectivePolicy = account.dmPolicy ?? value.dmPolicy;
    const effectiveAllowFrom = account.allowFrom ?? value.allowFrom;
    (0, _zodSchemaCoreB8hU4HYi.L)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.bluebubbles.accounts.*.dmPolicy=\"open\" requires channels.bluebubbles.accounts.*.allowFrom (or channels.bluebubbles.allowFrom) to include \"*\""
    });
    (0, _zodSchemaCoreB8hU4HYi.I)({
      policy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.bluebubbles.accounts.*.dmPolicy=\"allowlist\" requires channels.bluebubbles.accounts.*.allowFrom (or channels.bluebubbles.allowFrom) to contain at least one sender ID"
    });
  }
});
const MSTeamsChannelSchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  replyStyle: _zodSchemaCoreB8hU4HYi.m.optional()
}).strict();
const MSTeamsTeamSchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema$1,
  replyStyle: _zodSchemaCoreB8hU4HYi.m.optional(),
  channels: _zod.z.record(_zod.z.string(), MSTeamsChannelSchema.optional()).optional()
}).strict();
const MSTeamsConfigSchema = exports.a = _zod.z.object({
  enabled: _zod.z.boolean().optional(),
  capabilities: _zod.z.array(_zod.z.string()).optional(),
  dangerouslyAllowNameMatching: _zod.z.boolean().optional(),
  markdown: _zodSchemaCoreB8hU4HYi.h,
  configWrites: _zod.z.boolean().optional(),
  appId: _zod.z.string().optional(),
  appPassword: _zodSchemaCoreB8hU4HYi.C.optional().register(_zodSchemaSensitive4zM6OUv.t),
  tenantId: _zod.z.string().optional(),
  authType: _zod.z.enum(["secret", "federated"]).optional(),
  certificatePath: _zod.z.string().optional(),
  certificateThumbprint: _zod.z.string().optional(),
  useManagedIdentity: _zod.z.boolean().optional(),
  managedIdentityClientId: _zod.z.string().optional(),
  webhook: _zod.z.object({
    port: _zod.z.number().int().positive().optional(),
    path: _zod.z.string().optional()
  }).strict().optional(),
  dmPolicy: _zodSchemaCoreB8hU4HYi.o.optional().default("pairing"),
  allowFrom: _zod.z.array(_zod.z.string()).optional(),
  defaultTo: _zod.z.string().optional(),
  groupAllowFrom: _zod.z.array(_zod.z.string()).optional(),
  groupPolicy: _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist"),
  contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
  textChunkLimit: _zod.z.number().int().positive().optional(),
  chunkMode: _zod.z.enum(["length", "newline"]).optional(),
  streaming: ChannelPreviewStreamingConfigSchema.optional(),
  typingIndicator: _zod.z.boolean().optional(),
  blockStreaming: _zod.z.boolean().optional(),
  blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
  mediaAllowHosts: _zod.z.array(_zod.z.string()).optional(),
  mediaAuthAllowHosts: _zod.z.array(_zod.z.string()).optional(),
  requireMention: _zod.z.boolean().optional(),
  historyLimit: _zod.z.number().int().min(0).optional(),
  dmHistoryLimit: _zod.z.number().int().min(0).optional(),
  dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
  replyStyle: _zodSchemaCoreB8hU4HYi.m.optional(),
  teams: _zod.z.record(_zod.z.string(), MSTeamsTeamSchema.optional()).optional(),
  /** Max media size in MB (default: 100MB for OneDrive upload support). */
  mediaMaxMb: _zod.z.number().positive().optional(),
  /** SharePoint site ID for file uploads in group chats/channels (e.g., "contoso.sharepoint.com,guid1,guid2") */
  sharePointSiteId: _zod.z.string().optional(),
  heartbeat: ChannelHeartbeatVisibilitySchema,
  healthMonitor: ChannelHealthMonitorSchema,
  responsePrefix: _zod.z.string().optional(),
  welcomeCard: _zod.z.boolean().optional(),
  promptStarters: _zod.z.array(_zod.z.string()).optional(),
  groupWelcomeCard: _zod.z.boolean().optional(),
  feedbackEnabled: _zod.z.boolean().optional(),
  feedbackReflection: _zod.z.boolean().optional(),
  feedbackReflectionCooldownMs: _zod.z.number().int().min(0).optional(),
  delegatedAuth: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    scopes: _zod.z.array(_zod.z.string()).optional()
  }).strict().optional(),
  sso: _zod.z.object({
    enabled: _zod.z.boolean().optional(),
    connectionName: _zod.z.string().optional()
  }).strict().optional()
}).strict().superRefine((value, ctx) => {
  (0, _zodSchemaCoreB8hU4HYi.L)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.msteams.dmPolicy=\"open\" requires channels.msteams.allowFrom to include \"*\""
  });
  (0, _zodSchemaCoreB8hU4HYi.I)({
    policy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    path: ["allowFrom"],
    message: "channels.msteams.dmPolicy=\"allowlist\" requires channels.msteams.allowFrom to contain at least one sender ID"
  });
  if (value.sso?.enabled === true && !value.sso.connectionName?.trim()) ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: ["sso", "connectionName"],
    message: "channels.msteams.sso.enabled=true requires channels.msteams.sso.connectionName to identify the Bot Framework OAuth connection"
  });
});
//#endregion
//#region src/config/zod-schema.providers-whatsapp.ts
const ToolPolicyBySenderSchema = _zod.z.record(_zod.z.string(), _zodSchemaAgentRuntimeBgmaoJWM.l).optional();
const WhatsAppGroupEntrySchema = _zod.z.object({
  requireMention: _zod.z.boolean().optional(),
  tools: _zodSchemaAgentRuntimeBgmaoJWM.l,
  toolsBySender: ToolPolicyBySenderSchema,
  systemPrompt: _zod.z.string().optional()
}).strict().optional();
const WhatsAppGroupsSchema = _zod.z.record(_zod.z.string(), WhatsAppGroupEntrySchema).optional();
const WhatsAppDirectEntrySchema = _zod.z.object({ systemPrompt: _zod.z.string().optional() }).strict().optional();
const WhatsAppDirectSchema = _zod.z.record(_zod.z.string(), WhatsAppDirectEntrySchema).optional();
const WhatsAppAckReactionSchema = _zod.z.object({
  emoji: _zod.z.string().optional(),
  direct: _zod.z.boolean().optional().default(true),
  group: _zod.z.enum([
  "always",
  "mentions",
  "never"]
  ).optional().default("mentions")
}).strict().optional();
function stripDeprecatedWhatsAppNoopKeys(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return value;
  if (!Object.hasOwn(value, "exposeErrorText")) return value;
  const next = { ...value };
  delete next.exposeErrorText;
  return next;
}
function buildWhatsAppCommonShape(params) {
  return {
    enabled: _zod.z.boolean().optional(),
    capabilities: _zod.z.array(_zod.z.string()).optional(),
    markdown: _zodSchemaCoreB8hU4HYi.h,
    configWrites: _zod.z.boolean().optional(),
    sendReadReceipts: _zod.z.boolean().optional(),
    messagePrefix: _zod.z.string().optional(),
    responsePrefix: _zod.z.string().optional(),
    dmPolicy: params.useDefaults ? _zodSchemaCoreB8hU4HYi.o.optional().default("pairing") : _zodSchemaCoreB8hU4HYi.o.optional(),
    selfChatMode: _zod.z.boolean().optional(),
    allowFrom: _zod.z.array(_zod.z.string()).optional(),
    defaultTo: _zod.z.string().optional(),
    groupAllowFrom: _zod.z.array(_zod.z.string()).optional(),
    groupPolicy: params.useDefaults ? _zodSchemaCoreB8hU4HYi.l.optional().default("allowlist") : _zodSchemaCoreB8hU4HYi.l.optional(),
    contextVisibility: _zodSchemaCoreB8hU4HYi.i.optional(),
    historyLimit: _zod.z.number().int().min(0).optional(),
    dmHistoryLimit: _zod.z.number().int().min(0).optional(),
    dms: _zod.z.record(_zod.z.string(), _zodSchemaCoreB8hU4HYi.a.optional()).optional(),
    textChunkLimit: _zod.z.number().int().positive().optional(),
    chunkMode: _zod.z.enum(["length", "newline"]).optional(),
    blockStreaming: _zod.z.boolean().optional(),
    blockStreamingCoalesce: _zodSchemaCoreB8hU4HYi.n.optional(),
    groups: WhatsAppGroupsSchema,
    direct: WhatsAppDirectSchema,
    ackReaction: WhatsAppAckReactionSchema,
    reactionLevel: _zod.z.enum([
    "off",
    "ack",
    "minimal",
    "extensive"]
    ).optional(),
    debounceMs: params.useDefaults ? _zod.z.number().int().nonnegative().optional().default(0) : _zod.z.number().int().nonnegative().optional(),
    replyToMode: _zodSchemaCoreB8hU4HYi.x.optional(),
    heartbeat: ChannelHeartbeatVisibilitySchema,
    healthMonitor: ChannelHealthMonitorSchema
  };
}
function enforceOpenDmPolicyAllowFromStar(params) {
  if (params.dmPolicy !== "open") return;
  if ((0, _stringNormalizationC5SGsaST.s)(Array.isArray(params.allowFrom) ? params.allowFrom : []).includes("*")) return;
  params.ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: params.path ?? ["allowFrom"],
    message: params.message
  });
}
function enforceAllowlistDmPolicyAllowFrom(params) {
  if (params.dmPolicy !== "allowlist") return;
  if ((0, _stringNormalizationC5SGsaST.s)(Array.isArray(params.allowFrom) ? params.allowFrom : []).length > 0) return;
  params.ctx.addIssue({
    code: _zod.z.ZodIssueCode.custom,
    path: params.path ?? ["allowFrom"],
    message: params.message
  });
}
const WhatsAppAccountObjectSchema = _zod.z.object({
  ...buildWhatsAppCommonShape({ useDefaults: false }),
  name: _zod.z.string().optional(),
  enabled: _zod.z.boolean().optional(),
  /** Override auth directory for this WhatsApp account (Baileys multi-file auth state). */
  authDir: _zod.z.string().optional(),
  mediaMaxMb: _zod.z.number().int().positive().optional()
}).strict();
const WhatsAppAccountSchema = _zod.z.preprocess(stripDeprecatedWhatsAppNoopKeys, WhatsAppAccountObjectSchema);
const WhatsAppConfigObjectSchema = _zod.z.object({
  ...buildWhatsAppCommonShape({ useDefaults: true }),
  accounts: _zod.z.record(_zod.z.string(), WhatsAppAccountSchema.optional()).optional(),
  defaultAccount: _zod.z.string().optional(),
  mediaMaxMb: _zod.z.number().int().positive().optional().default(50),
  actions: _zod.z.object({
    reactions: _zod.z.boolean().optional(),
    sendMessage: _zod.z.boolean().optional(),
    polls: _zod.z.boolean().optional()
  }).strict().optional()
}).strict().superRefine((value, ctx) => {
  const defaultAccount = (0, _accountLookupDimKmpQR.t)(value.accounts, "default");
  enforceOpenDmPolicyAllowFromStar({
    dmPolicy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    message: "channels.whatsapp.dmPolicy=\"open\" requires channels.whatsapp.allowFrom to include \"*\""
  });
  enforceAllowlistDmPolicyAllowFrom({
    dmPolicy: value.dmPolicy,
    allowFrom: value.allowFrom,
    ctx,
    message: "channels.whatsapp.dmPolicy=\"allowlist\" requires channels.whatsapp.allowFrom to contain at least one sender ID"
  });
  if (!value.accounts) return;
  for (const [accountId, account] of Object.entries(value.accounts)) {
    if (!account) continue;
    const effectivePolicy = account.dmPolicy ?? (accountId === "default" ? void 0 : defaultAccount?.dmPolicy) ?? value.dmPolicy;
    const effectiveAllowFrom = account.allowFrom ?? (accountId === "default" ? void 0 : defaultAccount?.allowFrom) ?? value.allowFrom;
    enforceOpenDmPolicyAllowFromStar({
      dmPolicy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.whatsapp.accounts.*.dmPolicy=\"open\" requires channels.whatsapp.accounts.*.allowFrom (or channels.whatsapp.allowFrom) to include \"*\""
    });
    enforceAllowlistDmPolicyAllowFrom({
      dmPolicy: effectivePolicy,
      allowFrom: effectiveAllowFrom,
      ctx,
      path: [
      "accounts",
      accountId,
      "allowFrom"],

      message: "channels.whatsapp.accounts.*.dmPolicy=\"allowlist\" requires channels.whatsapp.accounts.*.allowFrom (or channels.whatsapp.allowFrom) to contain at least one sender ID"
    });
  }
});
const WhatsAppConfigSchema = exports.t = _zod.z.preprocess(stripDeprecatedWhatsAppNoopKeys, WhatsAppConfigObjectSchema);
//#endregion /* v9-078b8957b112b424 */
