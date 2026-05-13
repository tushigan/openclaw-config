"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = buildBytePlusProvider;exports.t = buildBytePlusCodingProvider;var _providerCatalogSharedCYN2NIkQ = require("./provider-catalog-shared-CYN2NIkQ.js");
var _openclawPluginBxKuapBE = require("./openclaw.plugin-BxKuapBE.js");
//#region extensions/byteplus/provider-catalog.ts
function buildBytePlusProvider() {
  return (0, _providerCatalogSharedCYN2NIkQ.n)({
    providerId: "byteplus",
    catalog: _openclawPluginBxKuapBE.t.providers.byteplus
  });
}
function buildBytePlusCodingProvider() {
  return (0, _providerCatalogSharedCYN2NIkQ.n)({
    providerId: "byteplus-plan",
    catalog: _openclawPluginBxKuapBE.t.providers["byteplus-plan"]
  });
}
//#endregion /* v9-4bc569895d9793a0 */
