"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.UnionPrioritySort = UnionPrioritySort;
var _index = require("../../guard/index.mjs");
var _index2 = require("../../type/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// DeterministicCompare
//
// Provides a deterministic tie-break for schemas. This is used when
// schemas are structurally disjoint or mutually inclusive. While
// JSON serialization incurs a performance overhead, it serves as a
// reliable mechanism to ensure stable ordering and preserves the
// alphabetical alignment of named constants.
//
// ------------------------------------------------------------------
function DeterministicCompare(left, right) {
  return JSON.stringify(left).localeCompare(JSON.stringify(right));
}
// ------------------------------------------------------------------
// UnionPrioritySort
//
// Performs a deterministic sort on Union members. By default, this
// function ensures that narrow (more specific) types precede broader
// types in the resulting array. The order can be reversed by setting
// the order property to -1 which will reverse unions from broader
// to more narrow.
//
// ------------------------------------------------------------------
/** Deterministically sorts schemas by structural relationship (narrow to broad) */
function UnionPrioritySort(types, order = 1) {
  return types.sort((left, right) => {
    const result = (0, _index2.Compare)(left, right);
    return (_index.Guard.IsEqual(result, 'disjoint') ? DeterministicCompare(left, right) :
    _index.Guard.IsEqual(result, 'right-inside') ? 1 :
    _index.Guard.IsEqual(result, 'left-inside') ? -1 :
    DeterministicCompare(left, right)) * order;
  });
} /* v9-c37be95188569e6f */
