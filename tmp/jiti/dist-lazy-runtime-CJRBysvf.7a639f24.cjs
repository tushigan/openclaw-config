"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = createLazyRuntimeSurface;exports.i = createLazyRuntimeNamedExport;exports.n = createLazyRuntimeMethodBinder;exports.r = createLazyRuntimeModule;exports.t = createLazyRuntimeMethod; //#region src/shared/lazy-runtime.ts
function createLazyRuntimeSurface(importer, select) {
  let cached = null;
  return () => {
    cached ??= importer().then(select);
    return cached;
  };
}
/** Cache the raw dynamically imported runtime module behind a stable loader. */
function createLazyRuntimeModule(importer) {
  return createLazyRuntimeSurface(importer, (module) => module);
}
/** Cache a single named runtime export without repeating a custom selector closure per caller. */
function createLazyRuntimeNamedExport(importer, key) {
  return createLazyRuntimeSurface(importer, (module) => module[key]);
}
function createLazyRuntimeMethod(load, select) {
  const invoke = async (...args) => {
    return await select(await load())(...args);
  };
  return invoke;
}
function createLazyRuntimeMethodBinder(load) {
  return function (select) {
    return createLazyRuntimeMethod(load, select);
  };
}
//#endregion /* v9-c6b990b286607e62 */
