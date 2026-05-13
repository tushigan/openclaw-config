"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = restoreDetachedTaskLifecycleRuntimeRegistration;exports.i = registerDetachedTaskLifecycleRuntime;exports.n = getDetachedTaskLifecycleRuntimeRegistration;exports.r = getRegisteredDetachedTaskLifecycleRuntime;exports.t = clearDetachedTaskLifecycleRuntimeRegistration; //#region src/tasks/detached-task-runtime-state.ts
let detachedTaskLifecycleRuntimeRegistration;
function registerDetachedTaskLifecycleRuntime(pluginId, runtime) {
  detachedTaskLifecycleRuntimeRegistration = {
    pluginId,
    runtime
  };
}
function getDetachedTaskLifecycleRuntimeRegistration() {
  if (!detachedTaskLifecycleRuntimeRegistration) return;
  return {
    pluginId: detachedTaskLifecycleRuntimeRegistration.pluginId,
    runtime: detachedTaskLifecycleRuntimeRegistration.runtime
  };
}
function getRegisteredDetachedTaskLifecycleRuntime() {
  return detachedTaskLifecycleRuntimeRegistration?.runtime;
}
function restoreDetachedTaskLifecycleRuntimeRegistration(registration) {
  detachedTaskLifecycleRuntimeRegistration = registration ? {
    pluginId: registration.pluginId,
    runtime: registration.runtime
  } : void 0;
}
function clearDetachedTaskLifecycleRuntimeRegistration() {
  detachedTaskLifecycleRuntimeRegistration = void 0;
}
//#endregion /* v9-c9e42875200ab9d3 */
