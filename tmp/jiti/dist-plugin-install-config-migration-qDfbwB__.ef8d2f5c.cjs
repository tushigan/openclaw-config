"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = stripShippedPluginInstallConfigRecords;exports.t = extractShippedPluginInstallConfigRecords;var _zodSchemaInstallsBrZxLEMx = require("./zod-schema.installs-BrZxLEMx.js");
var _zod = require("zod");
//#region src/config/plugin-install-config-migration.ts
const PluginInstallRecordsSchema = _zod.z.record(_zod.z.string(), _zod.z.object(_zodSchemaInstallsBrZxLEMx.n).passthrough());
function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function pruneEmptyPluginsObject(plugins) {
  const { installs: _installs, ...rest } = plugins;
  return Object.keys(rest).length === 0 ? void 0 : rest;
}
function extractShippedPluginInstallConfigRecords(config) {
  if (!isRecord(config) || !isRecord(config.plugins)) return {};
  const parsed = PluginInstallRecordsSchema.safeParse(config.plugins.installs);
  return parsed.success ? structuredClone(parsed.data) : {};
}
function stripShippedPluginInstallConfigRecords(config) {
  if (!isRecord(config) || !isRecord(config.plugins) || !("installs" in config.plugins)) return config;
  const plugins = pruneEmptyPluginsObject(config.plugins);
  const { plugins: _plugins, ...rest } = config;
  return plugins === void 0 ? rest : {
    ...rest,
    plugins
  };
}
//#endregion /* v9-0efef81345bb01be */
