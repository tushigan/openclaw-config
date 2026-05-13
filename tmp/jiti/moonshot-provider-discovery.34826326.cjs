"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _providerCatalogYVk46TqZ = require("../../provider-catalog-yVk46TqZ.js");
//#region extensions/moonshot/provider-discovery.ts
const moonshotProviderDiscovery = exports.default = {
  id: "moonshot",
  label: "Moonshot",
  docsPath: "/providers/moonshot",
  auth: [],
  staticCatalog: {
    order: "simple",
    run: async () => ({ provider: (0, _providerCatalogYVk46TqZ.a)() })
  }
};
//#endregion /* v9-25e25ba1c3127791 */
