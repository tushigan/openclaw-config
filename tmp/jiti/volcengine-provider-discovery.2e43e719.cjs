"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _providerCatalogCL7JOWUf = require("../../provider-catalog-CL7JOWUf.js");
//#region extensions/volcengine/provider-discovery.ts
const volcengineProviderDiscovery = exports.default = [{
  id: "volcengine",
  label: "Volcengine",
  docsPath: "/providers/models",
  auth: [],
  staticCatalog: {
    order: "simple",
    run: async () => ({ provider: (0, _providerCatalogCL7JOWUf.n)() })
  }
}, {
  id: "volcengine-plan",
  label: "Volcengine Plan",
  docsPath: "/providers/models",
  auth: [],
  staticCatalog: {
    order: "simple",
    run: async () => ({ provider: (0, _providerCatalogCL7JOWUf.t)() })
  }
}];
//#endregion /* v9-1b596be2cf3ffd35 */
