"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = exports.n = void 0;var _zod = require("zod");
//#region src/config/zod-schema.installs.ts
const InstallSourceSchema = _zod.z.union([
_zod.z.literal("npm"),
_zod.z.literal("archive"),
_zod.z.literal("path"),
_zod.z.literal("clawhub"),
_zod.z.literal("git")]
);
const PluginInstallSourceSchema = _zod.z.union([InstallSourceSchema, _zod.z.literal("marketplace")]);
const InstallRecordShape = exports.t = {
  source: InstallSourceSchema,
  spec: _zod.z.string().optional(),
  sourcePath: _zod.z.string().optional(),
  installPath: _zod.z.string().optional(),
  version: _zod.z.string().optional(),
  resolvedName: _zod.z.string().optional(),
  resolvedVersion: _zod.z.string().optional(),
  resolvedSpec: _zod.z.string().optional(),
  integrity: _zod.z.string().optional(),
  shasum: _zod.z.string().optional(),
  resolvedAt: _zod.z.string().optional(),
  installedAt: _zod.z.string().optional(),
  clawhubUrl: _zod.z.string().optional(),
  clawhubPackage: _zod.z.string().optional(),
  clawhubFamily: _zod.z.union([_zod.z.literal("code-plugin"), _zod.z.literal("bundle-plugin")]).optional(),
  clawhubChannel: _zod.z.union([
  _zod.z.literal("official"),
  _zod.z.literal("community"),
  _zod.z.literal("private")]
  ).optional(),
  artifactKind: _zod.z.union([_zod.z.literal("legacy-zip"), _zod.z.literal("npm-pack")]).optional(),
  artifactFormat: _zod.z.union([_zod.z.literal("zip"), _zod.z.literal("tgz")]).optional(),
  npmIntegrity: _zod.z.string().optional(),
  npmShasum: _zod.z.string().optional(),
  npmTarballName: _zod.z.string().optional(),
  clawpackSha256: _zod.z.string().optional(),
  clawpackSpecVersion: _zod.z.number().int().nonnegative().optional(),
  clawpackManifestSha256: _zod.z.string().optional(),
  clawpackSize: _zod.z.number().int().nonnegative().optional(),
  gitUrl: _zod.z.string().optional(),
  gitRef: _zod.z.string().optional(),
  gitCommit: _zod.z.string().optional()
};
const PluginInstallRecordShape = exports.n = {
  ...InstallRecordShape,
  source: PluginInstallSourceSchema,
  marketplaceName: _zod.z.string().optional(),
  marketplaceSource: _zod.z.string().optional(),
  marketplacePlugin: _zod.z.string().optional()
};
//#endregion /* v9-9c0a3db3a02ee508 */
