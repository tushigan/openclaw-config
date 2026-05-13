"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.flushRawStdout = flushRawStdout;exports.isStdoutTakenOver = isStdoutTakenOver;exports.restoreStdout = restoreStdout;exports.takeOverStdout = takeOverStdout;exports.writeRawStdout = writeRawStdout;let stdoutTakeoverState;
function takeOverStdout() {
  if (stdoutTakeoverState) {
    return;
  }
  const rawStdoutWrite = process.stdout.write.bind(process.stdout);
  const rawStderrWrite = process.stderr.write.bind(process.stderr);
  const originalStdoutWrite = process.stdout.write;
  process.stdout.write = (chunk, encodingOrCallback, callback) => {
    if (typeof encodingOrCallback === "function") {
      return rawStderrWrite(String(chunk), encodingOrCallback);
    }
    return rawStderrWrite(String(chunk), callback);
  };
  stdoutTakeoverState = {
    rawStdoutWrite,
    rawStderrWrite,
    originalStdoutWrite
  };
}
function restoreStdout() {
  if (!stdoutTakeoverState) {
    return;
  }
  process.stdout.write = stdoutTakeoverState.originalStdoutWrite;
  stdoutTakeoverState = undefined;
}
function isStdoutTakenOver() {
  return stdoutTakeoverState !== undefined;
}
function writeRawStdout(text) {
  if (stdoutTakeoverState) {
    stdoutTakeoverState.rawStdoutWrite(text);
    return;
  }
  process.stdout.write(text);
}
async function flushRawStdout() {
  if (stdoutTakeoverState) {
    await new Promise((resolve, reject) => {
      stdoutTakeoverState?.rawStdoutWrite("", (err) => {
        if (err)
        reject(err);else

        resolve();
      });
    });
    return;
  }
  await new Promise((resolve, reject) => {
    process.stdout.write("", (err) => {
      if (err)
      reject(err);else

      resolve();
    });
  });
} /* v9-c8a954b2e3cc5b17 */
