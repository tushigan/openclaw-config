"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = normalizePluginHttpPath;exports.t = findOverlappingPluginHttpRoute;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _securityPathCQRsMpXY = require("./security-path-CQRsMpXY.js");
//#region src/plugins/http-path.ts
function normalizePluginHttpPath(path, fallback) {
  const trimmed = (0, _stringCoerceBje8XVt.c)(path);
  if (!trimmed) {
    const fallbackTrimmed = (0, _stringCoerceBje8XVt.c)(fallback);
    if (!fallbackTrimmed) return null;
    return fallbackTrimmed.startsWith("/") ? fallbackTrimmed : `/${fallbackTrimmed}`;
  }
  return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
}
//#endregion
//#region src/plugins/http-route-overlap.ts
function prefixMatchPath(pathname, prefix) {
  return pathname === prefix || pathname.startsWith(`${prefix}/`) || pathname.startsWith(`${prefix}%`);
}
function doPluginHttpRoutesOverlap(a, b) {
  const aPath = (0, _securityPathCQRsMpXY.r)(a.path);
  const bPath = (0, _securityPathCQRsMpXY.r)(b.path);
  if (a.match === "exact" && b.match === "exact") return aPath === bPath;
  if (a.match === "prefix" && b.match === "prefix") return prefixMatchPath(aPath, bPath) || prefixMatchPath(bPath, aPath);
  const prefixRoute = a.match === "prefix" ? a : b;
  return prefixMatchPath((0, _securityPathCQRsMpXY.r)((a.match === "exact" ? a : b).path), (0, _securityPathCQRsMpXY.r)(prefixRoute.path));
}
function findOverlappingPluginHttpRoute(routes, candidate) {
  return routes.find((route) => doPluginHttpRoutesOverlap(route, candidate));
}
//#endregion /* v9-977d66e68275612a */
