"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resetFatalErrorHooksForTest;exports.r = runFatalErrorHooks;exports.t = registerFatalErrorHook; //#region src/infra/fatal-error-hooks.ts
const hooks = /* @__PURE__ */new Set();
function formatHookFailure(error) {
  return `fatal-error hook failed: ${error instanceof Error && error.name ? error.name : "unknown"}`;
}
function registerFatalErrorHook(hook) {
  hooks.add(hook);
  return () => {
    hooks.delete(hook);
  };
}
function runFatalErrorHooks(context) {
  const messages = [];
  for (const hook of hooks) try {
    const message = hook(context);
    if (typeof message === "string" && message.trim()) messages.push(message);
  } catch (err) {
    messages.push(formatHookFailure(err));
  }
  return messages;
}
function resetFatalErrorHooksForTest() {
  hooks.clear();
}
//#endregion /* v9-6a08e4831e45c431 */
