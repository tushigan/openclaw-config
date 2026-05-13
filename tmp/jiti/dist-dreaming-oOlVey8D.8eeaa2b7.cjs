"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.F = exports.E = exports.D = exports.C = exports.B = exports.A = void 0;exports.G = resolveMemoryDreamingConfig;exports.H = isSameMemoryDreamingDay;exports.I = void 0;exports.J = resolveMemoryDreamingWorkspaces;exports.K = resolveMemoryDreamingPluginConfig;exports.U = exports.T = exports.S = exports.R = exports.P = exports.O = exports.N = exports.M = exports.L = void 0;exports.V = formatMemoryDreamingDay;exports.W = resolveMemoryDeepDreamingConfig;exports.X = resolveMemoryRemDreamingConfig;exports.Y = resolveMemoryLightDreamingConfig;exports.p = exports.o = exports.n = exports.m = exports.l = exports.k = exports.j = exports.i = exports.h = exports.g = exports.f = exports.d = exports.c = exports.b = exports.a = exports._ = void 0;exports.q = resolveMemoryDreamingPluginId;exports.z = exports.y = exports.x = exports.w = exports.v = exports.u = exports.t = exports.s = exports.r = void 0;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _agentScopeB6RIBoEj = require("./agent-scope-B6RIBoEj.js");
var _recordCoerceBjNW89OI = require("./record-coerce-BjNW89OI.js");
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/memory-host-sdk/dreaming.ts
const DEFAULT_MEMORY_DREAMING_ENABLED = exports.h = false;
const DEFAULT_MEMORY_DREAMING_TIMEZONE = exports.S = void 0;
const DEFAULT_MEMORY_DREAMING_VERBOSE_LOGGING = exports.C = false;
const DEFAULT_MEMORY_DREAMING_STORAGE_MODE = exports.b = "separate";
const DEFAULT_MEMORY_DREAMING_SEPARATE_REPORTS = exports.v = false;
const DEFAULT_MEMORY_DREAMING_FREQUENCY = exports.g = "0 3 * * *";
const DEFAULT_MEMORY_DREAMING_PLUGIN_ID = exports._ = "memory-core";
const MANAGED_MEMORY_DREAMING_CRON_NAME = exports.R = "Memory Dreaming Promotion";
const MANAGED_MEMORY_DREAMING_CRON_TAG = exports.z = "[managed-by=memory-core.short-term-promotion]";
const MEMORY_DREAMING_SYSTEM_EVENT_TEXT = exports.B = "__openclaw_memory_core_short_term_promotion_dream__";
const LEGACY_MEMORY_LIGHT_DREAMING_CRON_NAME = exports.M = "Memory Light Dreaming";
const LEGACY_MEMORY_LIGHT_DREAMING_CRON_TAG = exports.N = "[managed-by=memory-core.dreaming.light]";
const LEGACY_MEMORY_LIGHT_DREAMING_EVENT_TEXT = exports.P = "__openclaw_memory_core_light_sleep__";
const LEGACY_MEMORY_REM_DREAMING_CRON_NAME = exports.F = "Memory REM Dreaming";
const LEGACY_MEMORY_REM_DREAMING_CRON_TAG = exports.I = "[managed-by=memory-core.dreaming.rem]";
const LEGACY_MEMORY_REM_DREAMING_EVENT_TEXT = exports.L = "__openclaw_memory_core_rem_sleep__";
const DEFAULT_MEMORY_LIGHT_DREAMING_CRON_EXPR = exports.w = "0 */6 * * *";
const DEFAULT_MEMORY_LIGHT_DREAMING_LOOKBACK_DAYS = exports.D = 2;
const DEFAULT_MEMORY_LIGHT_DREAMING_LIMIT = exports.E = 100;
const DEFAULT_MEMORY_LIGHT_DREAMING_DEDUPE_SIMILARITY = exports.T = .9;
const DEFAULT_MEMORY_DEEP_DREAMING_CRON_EXPR = exports.t = "0 3 * * *";
const DEFAULT_MEMORY_DEEP_DREAMING_LIMIT = exports.n = 10;
const DEFAULT_MEMORY_DEEP_DREAMING_MIN_SCORE = exports.a = .8;
const DEFAULT_MEMORY_DEEP_DREAMING_MIN_RECALL_COUNT = exports.i = 3;
const DEFAULT_MEMORY_DEEP_DREAMING_MIN_UNIQUE_QUERIES = exports.o = 3;
const DEFAULT_MEMORY_DEEP_DREAMING_RECENCY_HALF_LIFE_DAYS = exports.s = 14;
const DEFAULT_MEMORY_DEEP_DREAMING_MAX_AGE_DAYS = exports.r = 30;
const DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_ENABLED = exports.l = true;
const DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_TRIGGER_BELOW_HEALTH = exports.p = .35;
const DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_LOOKBACK_DAYS = exports.u = 30;
const DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_MAX_CANDIDATES = exports.d = 20;
const DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_MIN_CONFIDENCE = exports.f = .9;
const DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_AUTO_WRITE_MIN_CONFIDENCE = exports.c = .97;
const DEFAULT_MEMORY_REM_DREAMING_CRON_EXPR = exports.O = "0 5 * * 0";
const DEFAULT_MEMORY_REM_DREAMING_LOOKBACK_DAYS = exports.A = 7;
const DEFAULT_MEMORY_REM_DREAMING_LIMIT = exports.k = 10;
const DEFAULT_MEMORY_REM_DREAMING_MIN_PATTERN_STRENGTH = exports.j = .75;
const DEFAULT_MEMORY_DREAMING_SPEED = exports.y = "balanced";
const DEFAULT_MEMORY_DREAMING_THINKING = exports.x = "medium";
const DEFAULT_MEMORY_DREAMING_BUDGET = exports.m = "medium";
const DEFAULT_MEMORY_LIGHT_DREAMING_SOURCES = [
"daily",
"sessions",
"recall"];

const DEFAULT_MEMORY_DEEP_DREAMING_SOURCES = [
"daily",
"memory",
"sessions",
"logs",
"recall"];

const DEFAULT_MEMORY_REM_DREAMING_SOURCES = [
"memory",
"daily",
"deep"];

function normalizeTrimmedString(value) {
  if (typeof value !== "string") return;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : void 0;
}
function normalizeNonNegativeInt(value, fallback) {
  const normalized = (0, _stringCoerceBje8XVt.d)(value);
  if (typeof value === "string" && !normalized) return fallback;
  const num = typeof value === "string" ? Number(normalized) : Number(value);
  if (!Number.isFinite(num)) return fallback;
  const floored = Math.floor(num);
  if (floored < 0) return fallback;
  return floored;
}
function normalizeOptionalPositiveInt(value) {
  if (value === void 0 || value === null) return;
  const normalized = (0, _stringCoerceBje8XVt.d)(value);
  if (typeof value === "string" && !normalized) return;
  const num = typeof value === "string" ? Number(normalized) : Number(value);
  if (!Number.isFinite(num)) return;
  const floored = Math.floor(num);
  if (floored <= 0) return;
  return floored;
}
function normalizeBoolean(value, fallback) {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") {
    const normalized = (0, _stringCoerceBje8XVt.a)(value);
    if (normalized === "true") return true;
    if (normalized === "false") return false;
  }
  return fallback;
}
function normalizeScore(value, fallback) {
  const normalized = (0, _stringCoerceBje8XVt.d)(value);
  if (typeof value === "string" && !normalized) return fallback;
  const num = typeof value === "string" ? Number(normalized) : Number(value);
  if (!Number.isFinite(num) || num < 0 || num > 1) return fallback;
  return num;
}
function normalizeSimilarity(value, fallback) {
  return normalizeScore(value, fallback);
}
function normalizeStringArray(value, allowed, fallback) {
  if (!Array.isArray(value)) return [...fallback];
  const allowedSet = new Set(allowed);
  const normalized = [];
  for (const entry of value) {
    const normalizedEntry = (0, _stringCoerceBje8XVt.s)(entry);
    if (!normalizedEntry || !allowedSet.has(normalizedEntry)) continue;
    if (!normalized.includes(normalizedEntry)) normalized.push(normalizedEntry);
  }
  return normalized.length > 0 ? normalized : [...fallback];
}
function normalizeStorageMode(value) {
  const normalized = (0, _stringCoerceBje8XVt.s)(value);
  if (normalized === "inline" || normalized === "separate" || normalized === "both") return normalized;
  return DEFAULT_MEMORY_DREAMING_STORAGE_MODE;
}
function normalizeSpeed(value) {
  const normalized = (0, _stringCoerceBje8XVt.s)(value);
  if (normalized === "fast" || normalized === "balanced" || normalized === "slow") return normalized;
}
function normalizeThinking(value) {
  const normalized = (0, _stringCoerceBje8XVt.s)(value);
  if (normalized === "low" || normalized === "medium" || normalized === "high") return normalized;
}
function normalizeBudget(value) {
  const normalized = (0, _stringCoerceBje8XVt.s)(value);
  if (normalized === "cheap" || normalized === "medium" || normalized === "expensive") return normalized;
}
function resolveExecutionConfig(value, fallback) {
  const record = (0, _recordCoerceBjNW89OI.n)(value);
  const maxOutputTokens = normalizeOptionalPositiveInt(record?.maxOutputTokens);
  const timeoutMs = normalizeOptionalPositiveInt(record?.timeoutMs);
  const temperatureRaw = record?.temperature;
  const temperature = typeof temperatureRaw === "number" && Number.isFinite(temperatureRaw) && temperatureRaw >= 0 ? Math.min(2, temperatureRaw) : void 0;
  const model = normalizeTrimmedString(record?.model) ?? fallback.model;
  return {
    speed: normalizeSpeed(record?.speed) ?? fallback.speed,
    thinking: normalizeThinking(record?.thinking) ?? fallback.thinking,
    budget: normalizeBudget(record?.budget) ?? fallback.budget,
    ...(model ? { model } : {}),
    ...(typeof maxOutputTokens === "number" ? { maxOutputTokens } : {}),
    ...(typeof temperature === "number" ? { temperature } : {}),
    ...(typeof timeoutMs === "number" ? { timeoutMs } : {})
  };
}
function normalizePathForComparison(input) {
  const normalized = _nodePath.default.resolve(input);
  return process.platform === "win32" ? (0, _stringCoerceBje8XVt.r)(normalized) : normalized;
}
function formatLocalIsoDay(epochMs) {
  const date = new Date(epochMs);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
function resolveMemoryDreamingPluginId(cfg) {
  const configuredSlot = normalizeTrimmedString((0, _recordCoerceBjNW89OI.n)((0, _recordCoerceBjNW89OI.n)((0, _recordCoerceBjNW89OI.n)(cfg)?.plugins)?.slots)?.memory);
  if (configuredSlot && (0, _stringCoerceBje8XVt.a)(configuredSlot) !== "none") return configuredSlot;
  return DEFAULT_MEMORY_DREAMING_PLUGIN_ID;
}
function resolveMemoryDreamingPluginConfig(cfg) {
  const entries = (0, _recordCoerceBjNW89OI.n)((0, _recordCoerceBjNW89OI.n)((0, _recordCoerceBjNW89OI.n)(cfg)?.plugins)?.entries);
  const pluginId = resolveMemoryDreamingPluginId(cfg);
  return (0, _recordCoerceBjNW89OI.n)((0, _recordCoerceBjNW89OI.n)(entries?.[pluginId])?.config) ?? void 0;
}
/** @deprecated Use resolveMemoryDreamingPluginConfig. */
const resolveMemoryCorePluginConfig = exports.U = resolveMemoryDreamingPluginConfig;
function resolveMemoryDreamingConfig(params) {
  const dreaming = (0, _recordCoerceBjNW89OI.n)(params.pluginConfig?.dreaming);
  const frequency = normalizeTrimmedString(dreaming?.frequency) ?? "0 3 * * *";
  const timezone = normalizeTrimmedString(dreaming?.timezone) ?? normalizeTrimmedString(params.cfg?.agents?.defaults?.userTimezone) ?? void 0;
  const storage = (0, _recordCoerceBjNW89OI.n)(dreaming?.storage);
  const execution = (0, _recordCoerceBjNW89OI.n)(dreaming?.execution);
  const phases = (0, _recordCoerceBjNW89OI.n)(dreaming?.phases);
  const topLevelModel = normalizeTrimmedString(dreaming?.model);
  const defaultExecution = resolveExecutionConfig(execution?.defaults, {
    speed: DEFAULT_MEMORY_DREAMING_SPEED,
    thinking: DEFAULT_MEMORY_DREAMING_THINKING,
    budget: DEFAULT_MEMORY_DREAMING_BUDGET,
    ...(topLevelModel ? { model: topLevelModel } : {})
  });
  const light = (0, _recordCoerceBjNW89OI.n)(phases?.light);
  const deep = (0, _recordCoerceBjNW89OI.n)(phases?.deep);
  const rem = (0, _recordCoerceBjNW89OI.n)(phases?.rem);
  const deepRecovery = (0, _recordCoerceBjNW89OI.n)(deep?.recovery);
  const maxAgeDays = normalizeOptionalPositiveInt(deep?.maxAgeDays);
  return {
    enabled: normalizeBoolean(dreaming?.enabled, false),
    frequency,
    ...(timezone ? { timezone } : {}),
    verboseLogging: normalizeBoolean(dreaming?.verboseLogging, false),
    storage: {
      mode: normalizeStorageMode(storage?.mode),
      separateReports: normalizeBoolean(storage?.separateReports, false)
    },
    execution: { defaults: defaultExecution },
    phases: {
      light: {
        enabled: normalizeBoolean(light?.enabled, true),
        cron: frequency,
        lookbackDays: normalizeNonNegativeInt(light?.lookbackDays, 2),
        limit: normalizeNonNegativeInt(light?.limit, 100),
        dedupeSimilarity: normalizeSimilarity(light?.dedupeSimilarity, DEFAULT_MEMORY_LIGHT_DREAMING_DEDUPE_SIMILARITY),
        sources: normalizeStringArray(light?.sources, [
        "daily",
        "sessions",
        "recall"],
        DEFAULT_MEMORY_LIGHT_DREAMING_SOURCES),
        execution: resolveExecutionConfig(light?.execution, {
          ...defaultExecution,
          speed: "fast",
          thinking: "low",
          budget: "cheap"
        })
      },
      deep: {
        enabled: normalizeBoolean(deep?.enabled, true),
        cron: frequency,
        limit: normalizeNonNegativeInt(deep?.limit, 10),
        minScore: normalizeScore(deep?.minScore, DEFAULT_MEMORY_DEEP_DREAMING_MIN_SCORE),
        minRecallCount: normalizeNonNegativeInt(deep?.minRecallCount, 3),
        minUniqueQueries: normalizeNonNegativeInt(deep?.minUniqueQueries, 3),
        recencyHalfLifeDays: normalizeNonNegativeInt(deep?.recencyHalfLifeDays, 14),
        ...(typeof maxAgeDays === "number" ? { maxAgeDays } : { maxAgeDays: 30 }),
        sources: normalizeStringArray(deep?.sources, [
        "daily",
        "memory",
        "sessions",
        "logs",
        "recall"],
        DEFAULT_MEMORY_DEEP_DREAMING_SOURCES),
        recovery: {
          enabled: normalizeBoolean(deepRecovery?.enabled, true),
          triggerBelowHealth: normalizeScore(deepRecovery?.triggerBelowHealth, DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_TRIGGER_BELOW_HEALTH),
          lookbackDays: normalizeNonNegativeInt(deepRecovery?.lookbackDays, 30),
          maxRecoveredCandidates: normalizeNonNegativeInt(deepRecovery?.maxRecoveredCandidates, 20),
          minRecoveryConfidence: normalizeScore(deepRecovery?.minRecoveryConfidence, DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_MIN_CONFIDENCE),
          autoWriteMinConfidence: normalizeScore(deepRecovery?.autoWriteMinConfidence, DEFAULT_MEMORY_DEEP_DREAMING_RECOVERY_AUTO_WRITE_MIN_CONFIDENCE)
        },
        execution: resolveExecutionConfig(deep?.execution, {
          ...defaultExecution,
          speed: "balanced",
          thinking: "high",
          budget: "medium"
        })
      },
      rem: {
        enabled: normalizeBoolean(rem?.enabled, true),
        cron: frequency,
        lookbackDays: normalizeNonNegativeInt(rem?.lookbackDays, 7),
        limit: normalizeNonNegativeInt(rem?.limit, 10),
        minPatternStrength: normalizeScore(rem?.minPatternStrength, DEFAULT_MEMORY_REM_DREAMING_MIN_PATTERN_STRENGTH),
        sources: normalizeStringArray(rem?.sources, [
        "memory",
        "daily",
        "deep"],
        DEFAULT_MEMORY_REM_DREAMING_SOURCES),
        execution: resolveExecutionConfig(rem?.execution, {
          ...defaultExecution,
          speed: "slow",
          thinking: "high",
          budget: "expensive"
        })
      }
    }
  };
}
function resolveMemoryDeepDreamingConfig(params) {
  const resolved = resolveMemoryDreamingConfig(params);
  return {
    ...resolved.phases.deep,
    enabled: resolved.enabled && resolved.phases.deep.enabled,
    ...(resolved.timezone ? { timezone: resolved.timezone } : {}),
    verboseLogging: resolved.verboseLogging,
    storage: resolved.storage
  };
}
function resolveMemoryLightDreamingConfig(params) {
  const resolved = resolveMemoryDreamingConfig(params);
  return {
    ...resolved.phases.light,
    enabled: resolved.enabled && resolved.phases.light.enabled,
    ...(resolved.timezone ? { timezone: resolved.timezone } : {}),
    verboseLogging: resolved.verboseLogging,
    storage: resolved.storage
  };
}
function resolveMemoryRemDreamingConfig(params) {
  const resolved = resolveMemoryDreamingConfig(params);
  return {
    ...resolved.phases.rem,
    enabled: resolved.enabled && resolved.phases.rem.enabled,
    ...(resolved.timezone ? { timezone: resolved.timezone } : {}),
    verboseLogging: resolved.verboseLogging,
    storage: resolved.storage
  };
}
function formatMemoryDreamingDay(epochMs, timezone) {
  if (!timezone) return formatLocalIsoDay(epochMs);
  try {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).formatToParts(new Date(epochMs));
    const values = new Map(parts.map((part) => [part.type, part.value]));
    const year = values.get("year");
    const month = values.get("month");
    const day = values.get("day");
    if (year && month && day) return `${year}-${month}-${day}`;
  } catch {}
  return formatLocalIsoDay(epochMs);
}
function isSameMemoryDreamingDay(firstEpochMs, secondEpochMs, timezone) {
  return formatMemoryDreamingDay(firstEpochMs, timezone) === formatMemoryDreamingDay(secondEpochMs, timezone);
}
function resolveMemoryDreamingWorkspaces(cfg, options = {}) {
  const configured = Array.isArray(cfg.agents?.list) ? cfg.agents.list : [];
  const agentIds = [];
  const seenAgents = /* @__PURE__ */new Set();
  for (const entry of configured) {
    if (!entry || typeof entry !== "object" || typeof entry.id !== "string") continue;
    const id = (0, _stringCoerceBje8XVt.s)(entry.id);
    if (!id || seenAgents.has(id)) continue;
    seenAgents.add(id);
    agentIds.push(id);
  }
  if (agentIds.length === 0) agentIds.push((0, _agentScopeB6RIBoEj.S)(cfg));
  const byWorkspace = /* @__PURE__ */new Map();
  const addWorkspace = (workspaceDirRaw, agentIdRaw) => {
    const workspaceDir = workspaceDirRaw?.trim();
    if (!workspaceDir) return;
    const agentId = (0, _stringCoerceBje8XVt.s)(agentIdRaw) || (0, _agentScopeB6RIBoEj.S)(cfg);
    const key = normalizePathForComparison(workspaceDir);
    const existing = byWorkspace.get(key);
    if (existing) {
      if (!existing.agentIds.includes(agentId)) existing.agentIds.push(agentId);
      return;
    }
    byWorkspace.set(key, {
      workspaceDir,
      agentIds: [agentId]
    });
  };
  for (const agentId of agentIds) addWorkspace((0, _agentScopeB6RIBoEj.x)(cfg, agentId), agentId);
  addWorkspace(options.primaryWorkspaceDir ?? void 0, options.primaryAgentId ?? (0, _agentScopeB6RIBoEj.S)(cfg));
  return [...byWorkspace.values()];
}
//#endregion /* v9-5749fd305c025c8a */
