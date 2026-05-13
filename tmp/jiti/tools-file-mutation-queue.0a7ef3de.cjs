"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.withFileMutationQueue = withFileMutationQueue;var _nodeFs = require("node:fs");
var _nodePath = require("node:path");
const fileMutationQueues = new Map();
function getMutationQueueKey(filePath) {
  const resolvedPath = (0, _nodePath.resolve)(filePath);
  try {
    return _nodeFs.realpathSync.native(resolvedPath);
  }
  catch {
    return resolvedPath;
  }
}
/**
 * Serialize file mutation operations targeting the same file.
 * Operations for different files still run in parallel.
 */
async function withFileMutationQueue(filePath, fn) {
  const key = getMutationQueueKey(filePath);
  const currentQueue = fileMutationQueues.get(key) ?? Promise.resolve();
  let releaseNext;
  const nextQueue = new Promise((resolveQueue) => {
    releaseNext = resolveQueue;
  });
  const chainedQueue = currentQueue.then(() => nextQueue);
  fileMutationQueues.set(key, chainedQueue);
  await currentQueue;
  try {
    return await fn();
  } finally
  {
    releaseNext();
    if (fileMutationQueues.get(key) === chainedQueue) {
      fileMutationQueues.delete(key);
    }
  }
} /* v9-ca488f5705839f9d */
