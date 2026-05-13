"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = mutateConfigFile;exports.r = replaceConfigFile;exports.t = void 0;var _errorsQN8rySzW = require("./errors-QN8rySzW.js");
var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _scanPathsBDLZwwV = require("./scan-paths-BDLZww-v.js");
var _ioE69J4lLI = require("./io-E69J4lLI.js");
var _includesCjiK0ofJ = require("./includes-CjiK0ofJ.js");
var _runtimeSnapshotDFDX1J4B = require("./runtime-snapshot-DFDX1J4B.js");
var _nodePath = _interopRequireDefault(require("node:path"));
var _promises = _interopRequireDefault(require("node:fs/promises"));
var _nodeCrypto = _interopRequireDefault(require("node:crypto"));
var _nodeUtil = require("node:util");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/config/mutate.ts
var ConfigMutationConflictError = class extends Error {
  constructor(message, params) {
    super(message);
    this.name = "ConfigMutationConflictError";
    this.currentHash = params.currentHash;
  }
};exports.t = ConfigMutationConflictError;
function assertBaseHashMatches(snapshot, expectedHash) {
  const currentHash = (0, _ioE69J4lLI.y)(snapshot) ?? null;
  if (expectedHash !== void 0 && expectedHash !== currentHash) throw new ConfigMutationConflictError("config changed since last load", { currentHash });
  return currentHash;
}
function getChangedTopLevelKeys(base, next) {
  if (!(0, _utilsD5swhEXt.c)(base) || !(0, _utilsD5swhEXt.c)(next)) return (0, _nodeUtil.isDeepStrictEqual)(base, next) ? [] : ["<root>"];
  return [...new Set([...Object.keys(base), ...Object.keys(next)])].filter((key) => !(0, _nodeUtil.isDeepStrictEqual)(base[key], next[key]));
}
function getSingleTopLevelIncludeTarget(params) {
  if (!(0, _utilsD5swhEXt.c)(params.snapshot.parsed)) return null;
  const authoredSection = params.snapshot.parsed[params.key];
  if (!(0, _utilsD5swhEXt.c)(authoredSection)) return null;
  const keys = Object.keys(authoredSection);
  const includeValue = authoredSection[_includesCjiK0ofJ.r];
  if (keys.length !== 1 || typeof includeValue !== "string") return null;
  const rootDir = _nodePath.default.dirname(params.snapshot.path);
  const resolved = _nodePath.default.normalize(_nodePath.default.isAbsolute(includeValue) ? includeValue : _nodePath.default.resolve(rootDir, includeValue));
  if (!(0, _scanPathsBDLZwwV.n)(rootDir, resolved)) return null;
  return resolved;
}
async function writeJsonFileAtomic(filePath, value) {
  const dir = _nodePath.default.dirname(filePath);
  const tmp = _nodePath.default.join(dir, `${_nodePath.default.basename(filePath)}.${process.pid}.${_nodeCrypto.default.randomUUID()}.tmp`);
  try {
    await _promises.default.mkdir(dir, { recursive: true });
    await _promises.default.writeFile(tmp, `${JSON.stringify(value, null, 2)}\n`, {
      encoding: "utf-8",
      mode: 384
    });
    await _promises.default.access(filePath).then(async () => await (0, _ioE69J4lLI.W)(filePath, _promises.default), () => void 0);
    await _promises.default.rename(tmp, filePath);
    await _promises.default.chmod(filePath, 384).catch(() => {});
  } catch (err) {
    await _promises.default.unlink(tmp).catch(() => {});
    throw err;
  }
}
async function tryWriteSingleTopLevelIncludeMutation(params) {
  const nextConfig = (0, _ioE69J4lLI.R)(params.nextConfig, (0, _ioE69J4lLI.z)(params.writeOptions?.unsetPaths));
  const changedKeys = getChangedTopLevelKeys(params.snapshot.sourceConfig, nextConfig);
  if (changedKeys.length !== 1 || changedKeys[0] === "<root>") return false;
  const key = changedKeys[0];
  const includePath = getSingleTopLevelIncludeTarget({
    snapshot: params.snapshot,
    key
  });
  if (!includePath || !(0, _utilsD5swhEXt.c)(nextConfig) || !(key in nextConfig)) return false;
  const nextConfigRecord = nextConfig;
  if (params.writeOptions?.skipPluginValidation) return false;
  const validated = (0, _ioE69J4lLI.T)(nextConfig);
  if (!validated.ok) throw (0, _ioE69J4lLI.H)(params.snapshot.path, (0, _ioE69J4lLI.U)(validated.issues));
  const runtimeConfigSnapshot = (0, _runtimeSnapshotDFDX1J4B.i)();
  const runtimeConfigSourceSnapshot = (0, _runtimeSnapshotDFDX1J4B.s)();
  const hadRuntimeSnapshot = Boolean(runtimeConfigSnapshot);
  const hadBothSnapshots = Boolean(runtimeConfigSnapshot && runtimeConfigSourceSnapshot);
  await writeJsonFileAtomic(includePath, nextConfigRecord[key]);
  if (params.writeOptions?.skipRuntimeSnapshotRefresh && !hadRuntimeSnapshot && !(0, _runtimeSnapshotDFDX1J4B.o)()) return true;
  const refreshedSnapshot = (await (params.io?.readConfigFileSnapshotForWrite ?? _ioE69J4lLI.d)()).snapshot;
  const persistedHash = (0, _ioE69J4lLI.y)(refreshedSnapshot);
  if (!refreshedSnapshot.valid) throw (0, _ioE69J4lLI.H)(params.snapshot.path, (0, _ioE69J4lLI.U)(refreshedSnapshot.issues));
  if (!persistedHash) throw new Error(`Config was written to ${params.snapshot.path}, but no persisted hash was available.`);
  const notifyCommittedWrite = () => {
    const currentRuntimeConfig = (0, _runtimeSnapshotDFDX1J4B.i)();
    if (!currentRuntimeConfig) return;
    (0, _runtimeSnapshotDFDX1J4B.u)((0, _runtimeSnapshotDFDX1J4B.n)({
      configPath: params.snapshot.path,
      sourceConfig: refreshedSnapshot.sourceConfig,
      runtimeConfig: currentRuntimeConfig,
      persistedHash,
      afterWrite: params.afterWrite ?? params.writeOptions?.afterWrite
    }));
  };
  await (0, _runtimeSnapshotDFDX1J4B.r)({
    nextSourceConfig: refreshedSnapshot.sourceConfig,
    hadRuntimeSnapshot,
    hadBothSnapshots,
    loadFreshConfig: () => refreshedSnapshot.runtimeConfig,
    notifyCommittedWrite,
    formatRefreshError: (error) => (0, _errorsQN8rySzW.i)(error),
    createRefreshError: (detail, cause) => new Error(`Config was written to ${params.snapshot.path}, but runtime snapshot refresh failed: ${detail}`, { cause })
  });
  return true;
}
async function replaceConfigFile(params) {
  const { snapshot, writeOptions } = params.snapshot && params.writeOptions ? {
    snapshot: params.snapshot,
    writeOptions: params.writeOptions
  } : await (params.io?.readConfigFileSnapshotForWrite ?? _ioE69J4lLI.d)();
  const previousHash = assertBaseHashMatches(snapshot, params.baseHash);
  const afterWrite = (0, _runtimeSnapshotDFDX1J4B.p)(params.afterWrite ?? params.writeOptions?.afterWrite);
  if (!(await tryWriteSingleTopLevelIncludeMutation({
    snapshot,
    nextConfig: params.nextConfig,
    afterWrite,
    writeOptions: params.writeOptions ?? writeOptions,
    io: params.io
  }))) await (params.io?.writeConfigFile ?? _ioE69J4lLI.b)(params.nextConfig, {
    baseSnapshot: snapshot,
    ...writeOptions,
    ...params.writeOptions,
    afterWrite
  });
  return {
    path: snapshot.path,
    previousHash,
    snapshot,
    nextConfig: params.nextConfig,
    afterWrite,
    followUp: (0, _runtimeSnapshotDFDX1J4B.m)(afterWrite)
  };
}
async function mutateConfigFile(params) {
  const { snapshot, writeOptions } = await (params.io?.readConfigFileSnapshotForWrite ?? _ioE69J4lLI.d)();
  const previousHash = assertBaseHashMatches(snapshot, params.baseHash);
  const baseConfig = params.base === "runtime" ? snapshot.runtimeConfig : snapshot.sourceConfig;
  const draft = structuredClone(baseConfig);
  const result = await params.mutate(draft, {
    snapshot,
    previousHash
  });
  const afterWrite = (0, _runtimeSnapshotDFDX1J4B.p)(params.afterWrite ?? params.writeOptions?.afterWrite);
  if (!(await tryWriteSingleTopLevelIncludeMutation({
    snapshot,
    nextConfig: draft,
    afterWrite,
    writeOptions: {
      ...writeOptions,
      ...params.writeOptions
    },
    io: params.io
  }))) await (params.io?.writeConfigFile ?? _ioE69J4lLI.b)(draft, {
    ...writeOptions,
    ...params.writeOptions,
    afterWrite
  });
  return {
    path: snapshot.path,
    previousHash,
    snapshot,
    nextConfig: draft,
    result,
    afterWrite,
    followUp: (0, _runtimeSnapshotDFDX1J4B.m)(afterWrite)
  };
}
//#endregion /* v9-e30705971f5c909a */
