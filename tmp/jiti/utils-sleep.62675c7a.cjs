"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.sleep = sleep; /**
 * Sleep helper that respects abort signal.
 */
function sleep(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new Error("Aborted"));
      return;
    }
    const timeout = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(timeout);
      reject(new Error("Aborted"));
    });
  });
} /* v9-0005724124baec80 */
