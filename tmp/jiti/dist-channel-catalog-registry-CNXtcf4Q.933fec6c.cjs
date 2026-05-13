"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = listChannelCatalogEntries;var _discoveryCVL9KJt = require("./discovery-CVL9-KJt.js");
//#region src/plugins/channel-catalog-registry.ts
function listChannelCatalogEntries(params = {}) {
  return (0, _discoveryCVL9KJt.t)({
    workspaceDir: params.workspaceDir,
    env: params.env
  }).candidates.flatMap((candidate) => {
    if (params.origin && candidate.origin !== params.origin) return [];
    const channel = candidate.packageManifest?.channel;
    if (!channel?.id) return [];
    const manifest = (0, _discoveryCVL9KJt.w)(candidate.rootDir, candidate.origin !== "bundled");
    if (!manifest.ok) return [];
    return [{
      pluginId: manifest.manifest.id,
      origin: candidate.origin,
      packageName: candidate.packageName,
      workspaceDir: candidate.workspaceDir,
      rootDir: candidate.rootDir,
      channel,
      ...(candidate.packageManifest?.install ? { install: candidate.packageManifest.install } : {})
    }];
  });
}
//#endregion /* v9-4fe2dcf72285fc11 */
