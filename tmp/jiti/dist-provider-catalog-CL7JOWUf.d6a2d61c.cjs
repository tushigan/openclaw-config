"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = buildDoubaoProvider;exports.t = buildDoubaoCodingProvider;var _providerCatalogSharedCYN2NIkQ = require("./provider-catalog-shared-CYN2NIkQ.js");
var _openclawPluginCF4gqfCz = require("./openclaw.plugin-CF4gqfCz.js");
//#region extensions/volcengine/provider-catalog.ts
function buildDoubaoProvider() {
  return (0, _providerCatalogSharedCYN2NIkQ.n)({
    providerId: "volcengine",
    catalog: _openclawPluginCF4gqfCz.t.providers.volcengine
  });
}
function buildDoubaoCodingProvider() {
  return (0, _providerCatalogSharedCYN2NIkQ.n)({
    providerId: "volcengine-plan",
    catalog: _openclawPluginCF4gqfCz.t.providers["volcengine-plan"]
  });
}
//#endregion /* v9-da233992a55f89ae */
