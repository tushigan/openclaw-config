"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.cleanupSessionResources = cleanupSessionResources;exports.registerSessionResourceCleanup = registerSessionResourceCleanup;const sessionResourceCleanups = new Set();
function registerSessionResourceCleanup(cleanup) {
  sessionResourceCleanups.add(cleanup);
  return () => {
    sessionResourceCleanups.delete(cleanup);
  };
}
function cleanupSessionResources(sessionId) {
  const errors = [];
  for (const cleanup of sessionResourceCleanups) {
    try {
      cleanup(sessionId);
    }
    catch (error) {
      errors.push(error);
    }
  }
  if (errors.length > 0) {
    throw new AggregateError(errors, "Failed to cleanup session resources");
  }
} /* v9-8def432aed6cf4c9 */
