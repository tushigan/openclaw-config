"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = asRecord;exports.i = asOptionalRecord;exports.n = asNullableRecord;exports.o = readStringField;exports.r = asOptionalObjectRecord;exports.t = asNullableObjectRecord; //#region src/shared/record-coerce.ts
function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
function asRecord(value) {
  return typeof value === "object" && value !== null ? value : {};
}
function readStringField(record, key) {
  const value = record?.[key];
  return typeof value === "string" ? value : void 0;
}
function asOptionalRecord(value) {
  return isRecord(value) ? value : void 0;
}
function asNullableRecord(value) {
  return isRecord(value) ? value : null;
}
function asOptionalObjectRecord(value) {
  return value && typeof value === "object" ? value : void 0;
}
function asNullableObjectRecord(value) {
  return value && typeof value === "object" ? value : null;
}
//#endregion /* v9-669e89f38dd53adb */
