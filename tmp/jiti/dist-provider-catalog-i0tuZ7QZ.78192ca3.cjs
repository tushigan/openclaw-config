"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = buildDeepSeekProvider;var _modelsEu9X1uJm = require("./models-eu9X1uJm.js");
//#region extensions/deepseek/provider-catalog.ts
function buildDeepSeekProvider() {
  return {
    baseUrl: _modelsEu9X1uJm.t,
    api: "openai-completions",
    models: _modelsEu9X1uJm.n.map(_modelsEu9X1uJm.r)
  };
}
//#endregion /* v9-972b3da73c63bf09 */
