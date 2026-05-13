"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _providerCatalogBm8lDH2s = require("../../provider-catalog-Bm8lDH2s.js");
//#region extensions/byteplus/provider-discovery.ts
const bytePlusProviderDiscovery = exports.default = [{
  id: "byteplus",
  label: "BytePlus",
  docsPath: "/providers/models",
  auth: [],
  staticCatalog: {
    order: "simple",
    run: async () => ({ provider: (0, _providerCatalogBm8lDH2s.n)() })
  }
}, {
  id: "byteplus-plan",
  label: "BytePlus Plan",
  docsPath: "/providers/models",
  auth: [],
  staticCatalog: {
    order: "simple",
    run: async () => ({ provider: (0, _providerCatalogBm8lDH2s.t)() })
  }
}];
//#endregion /* v9-65599ff1d6d5d7f0 */
