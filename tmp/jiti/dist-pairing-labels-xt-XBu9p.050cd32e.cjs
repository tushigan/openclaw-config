"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolvePairingIdLabel;var _pairingStoreC3tDeLw = require("./pairing-store-C3tDe-Lw.js");
//#region src/pairing/pairing-labels.ts
function resolvePairingIdLabel(channel) {
  return (0, _pairingStoreC3tDeLw.f)(channel)?.idLabel ?? "userId";
}
//#endregion /* v9-fb9f952064e3faee */
