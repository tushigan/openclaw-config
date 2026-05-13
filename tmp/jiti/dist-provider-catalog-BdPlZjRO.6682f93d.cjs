"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = buildTokenHubProvider;var _modelsBr6jZqeg = require("./models-Br6jZqeg.js");
//#region extensions/tencent/provider-catalog.ts
function buildTokenHubProvider() {
  return {
    baseUrl: _modelsBr6jZqeg.t,
    api: "openai-completions",
    models: _modelsBr6jZqeg.n.map(_modelsBr6jZqeg.i)
  };
}
//#endregion /* v9-1a89ded51452a67a */
