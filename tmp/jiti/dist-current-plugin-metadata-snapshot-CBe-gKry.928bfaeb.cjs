"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = getCurrentPluginMetadataSnapshot;exports.r = setCurrentPluginMetadataSnapshot;exports.t = clearCurrentPluginMetadataSnapshot;var _pluginMetadataSnapshotMEvRUosy = require("./plugin-metadata-snapshot-mEvRUosy.js");
var _installedPluginIndexStoreDH9sPamj = require("./installed-plugin-index-store-DH9sPamj.js");
//#region src/plugins/current-plugin-metadata-snapshot.ts
function resolvePluginMetadataControlPlaneFingerprint(config, options = {}) {
  return (0, _pluginMetadataSnapshotMEvRUosy.a)({
    config,
    ...options
  });
}
function setCurrentPluginMetadataSnapshot(snapshot, options = {}) {
  (0, _installedPluginIndexStoreDH9sPamj.l)(snapshot, snapshot ? resolvePluginMetadataControlPlaneFingerprint(options.config, {
    env: options.env,
    index: snapshot.index,
    policyHash: snapshot.policyHash,
    workspaceDir: options.workspaceDir ?? snapshot.workspaceDir
  }) : void 0);
}
function clearCurrentPluginMetadataSnapshot() {
  (0, _installedPluginIndexStoreDH9sPamj.s)();
}
function getCurrentPluginMetadataSnapshot(params = {}) {
  const { snapshot: rawSnapshot, configFingerprint } = (0, _installedPluginIndexStoreDH9sPamj.c)();
  const snapshot = rawSnapshot;
  if (!snapshot) return;
  if (params.config && snapshot.policyHash !== (0, _installedPluginIndexStoreDH9sPamj._)(params.config)) return;
  const requestedWorkspaceDir = params.workspaceDir ?? (params.allowWorkspaceScopedSnapshot === true ? snapshot.workspaceDir : void 0);
  if (params.config) {
    const requestedConfigFingerprint = resolvePluginMetadataControlPlaneFingerprint(params.config, {
      env: params.env,
      index: snapshot.index,
      policyHash: snapshot.policyHash,
      workspaceDir: requestedWorkspaceDir
    });
    if (configFingerprint && configFingerprint !== requestedConfigFingerprint) return;
    if (snapshot.configFingerprint && snapshot.configFingerprint !== requestedConfigFingerprint) return;
  }
  if (snapshot.workspaceDir !== void 0 && requestedWorkspaceDir === void 0) return;
  if (requestedWorkspaceDir !== void 0 && (snapshot.workspaceDir ?? "") !== (requestedWorkspaceDir ?? "")) return;
  return snapshot;
}
//#endregion /* v9-cb1160f203b495c3 */
