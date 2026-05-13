"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _providerCatalogBdPlZjRO = require("../../provider-catalog-BdPlZjRO.js");
//#region extensions/tencent/provider-discovery.ts
const tencentProviderDiscovery = exports.default = {
  id: "tencent-tokenhub",
  label: "Tencent TokenHub",
  docsPath: "/providers/models",
  auth: [],
  staticCatalog: {
    order: "simple",
    run: async () => ({ provider: (0, _providerCatalogBdPlZjRO.t)() })
  }
};
//#endregion /* v9-1fb81aafe45d1587 */
