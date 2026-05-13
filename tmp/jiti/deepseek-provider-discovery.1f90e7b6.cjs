"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _providerCatalogI0tuZ7QZ = require("../../provider-catalog-i0tuZ7QZ.js");
//#region extensions/deepseek/provider-discovery.ts
const deepSeekProviderDiscovery = exports.default = {
  id: "deepseek",
  label: "DeepSeek",
  docsPath: "/providers/deepseek",
  auth: [],
  staticCatalog: {
    order: "simple",
    run: async () => ({ provider: (0, _providerCatalogI0tuZ7QZ.t)() })
  }
};
//#endregion /* v9-3e41467d945fed27 */
