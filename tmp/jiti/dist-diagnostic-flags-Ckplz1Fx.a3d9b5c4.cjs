"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = matchesDiagnosticFlag;exports.r = resolveDiagnosticFlags;exports.t = isDiagnosticFlagEnabled;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
//#region src/infra/diagnostic-flags.ts
const DIAGNOSTICS_ENV = "OPENCLAW_DIAGNOSTICS";
function parseEnvFlags(raw) {
  if (!raw) return {
    flags: [],
    disablesAll: false
  };
  const trimmed = raw.trim();
  const lowered = (0, _stringCoerceBje8XVt.a)(trimmed);
  if (!lowered) return {
    flags: [],
    disablesAll: false
  };
  if ([
  "0",
  "false",
  "off",
  "none"].
  includes(lowered)) return {
    flags: [],
    disablesAll: true
  };
  if ([
  "1",
  "true",
  "all",
  "*"].
  includes(lowered)) return {
    flags: ["*"],
    disablesAll: false
  };
  return {
    flags: trimmed.split(/[,\s]+/).map((value) => (0, _stringCoerceBje8XVt.a)(value)).filter(Boolean),
    disablesAll: false
  };
}
function uniqueFlags(flags) {
  const seen = /* @__PURE__ */new Set();
  const out = [];
  for (const flag of flags) {
    const normalized = (0, _stringCoerceBje8XVt.a)(flag);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    out.push(normalized);
  }
  return out;
}
function resolveDiagnosticFlags(cfg, env = process.env) {
  const configFlags = Array.isArray(cfg?.diagnostics?.flags) ? cfg?.diagnostics?.flags : [];
  const envFlags = parseEnvFlags(env[DIAGNOSTICS_ENV]);
  if (envFlags.disablesAll) return [];
  return uniqueFlags([...configFlags, ...envFlags.flags]);
}
function matchesDiagnosticFlag(flag, enabledFlags) {
  const target = (0, _stringCoerceBje8XVt.a)(flag);
  if (!target) return false;
  for (const raw of enabledFlags) {
    const enabled = (0, _stringCoerceBje8XVt.a)(raw);
    if (!enabled) continue;
    if (enabled === "*" || enabled === "all") return true;
    if (enabled.endsWith(".*")) {
      const prefix = enabled.slice(0, -2);
      if (target === prefix || target.startsWith(`${prefix}.`)) return true;
    }
    if (enabled.endsWith("*")) {
      const prefix = enabled.slice(0, -1);
      if (target.startsWith(prefix)) return true;
    }
    if (enabled === target) return true;
  }
  return false;
}
function isDiagnosticFlagEnabled(flag, cfg, env = process.env) {
  return matchesDiagnosticFlag(flag, resolveDiagnosticFlags(cfg, env));
}
//#endregion /* v9-608331bebc5fc1b8 */
