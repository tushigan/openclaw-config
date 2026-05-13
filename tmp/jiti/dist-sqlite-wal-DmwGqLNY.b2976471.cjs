"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = requireNodeSqlite;exports.t = configureSqliteWalMaintenance;var _errorsQN8rySzW = require("./errors-QN8rySzW.js");
var _warningFilterCeEhlMRK = require("./warning-filter-CeEhlMRK.js");
var _nodeModule = require("node:module");
//#region src/infra/node-sqlite.ts
const _require = (0, _nodeModule.createRequire)("file:///opt/homebrew/lib/node_modules/openclaw/dist/sqlite-wal-DmwGqLNY.js");
function requireNodeSqlite() {
  (0, _warningFilterCeEhlMRK.t)();
  try {
    return _require("node:sqlite");
  } catch (err) {
    const message = (0, _errorsQN8rySzW.i)(err);
    throw new Error(`SQLite support is unavailable in this Node runtime (missing node:sqlite). ${message}`, { cause: err });
  }
}
function normalizeNonNegativeInteger(value, label) {
  if (!Number.isInteger(value) || value < 0) throw new Error(`${label} must be a non-negative integer`);
  return value;
}
function configureSqliteWalMaintenance(db, options = {}) {
  const autoCheckpointPages = normalizeNonNegativeInteger(options.autoCheckpointPages ?? 1e3, "autoCheckpointPages");
  const checkpointIntervalMs = normalizeNonNegativeInteger(options.checkpointIntervalMs ?? 18e5, "checkpointIntervalMs");
  const checkpointMode = options.checkpointMode ?? "TRUNCATE";
  db.exec("PRAGMA journal_mode = WAL;");
  db.exec(`PRAGMA wal_autocheckpoint = ${autoCheckpointPages};`);
  const checkpoint = () => {
    try {
      db.exec(`PRAGMA wal_checkpoint(${checkpointMode});`);
      return true;
    } catch (error) {
      options.onCheckpointError?.(error);
      return false;
    }
  };
  let timer = null;
  if (checkpointIntervalMs > 0) {
    timer = setInterval(checkpoint, checkpointIntervalMs);
    timer.unref?.();
  }
  return {
    checkpoint,
    close: () => {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
      return checkpoint();
    }
  };
}
//#endregion /* v9-64f6e5c8f889e064 */
