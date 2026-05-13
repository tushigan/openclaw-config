"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.CreateVariable = CreateVariable;exports.GetExternal = GetExternal;exports.ResetExternal = ResetExternal; // deno-fmt-ignore-file
const state = {
  identifier: 'External',
  variables: []
};
// ------------------------------------------------------------------
// CreateVariable
// ------------------------------------------------------------------
function CreateVariable(value) {
  const call = `External[${state.variables.length}]`;
  state.variables.push(value);
  return call;
}
// ------------------------------------------------------------------
// ResetExternal
// ------------------------------------------------------------------
function ResetExternal() {
  state.variables = [];
}
// ------------------------------------------------------------------
// GetExternals
// ------------------------------------------------------------------
function GetExternal() {
  return { ...state };
} /* v9-a6d983c9fcecc4aa */
