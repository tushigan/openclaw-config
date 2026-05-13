"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Patch = Patch;
var _index = require("../clone/index.mjs");
var _index2 = require("../pointer/index.mjs"); // deno-fmt-ignore-file
function IsRoot(edits) {
  return edits.length > 0 && edits[0].path === '' && edits[0].type === 'update';
}
function IsEmpty(edits) {
  return edits.length === 0;
}
// ------------------------------------------------------------------
// Patch
// ------------------------------------------------------------------
/**
 * Applies a sequence of Edit commands to a current value, producing a new value that incorporates
 * all edits. This function returns unknown so callers should Check the return value before use.
 * This function mutates the provided value. If mutation is not wanted, you should Clone the value
 * before passing to this function.
 */
function Patch(current, edits) {
  if (IsRoot(edits))
  return (0, _index.Clone)(edits[0].value);
  if (IsEmpty(edits))
  return (0, _index.Clone)(current);
  const clone = (0, _index.Clone)(current);
  for (const edit of edits) {
    switch (edit.type) {
      case 'insert':{
          _index2.Pointer.Set(clone, edit.path, edit.value);
          break;
        }
      case 'update':{
          _index2.Pointer.Set(clone, edit.path, edit.value);
          break;
        }
      case 'delete':{
          _index2.Pointer.Delete(clone, edit.path);
          break;
        }
    }
  }
  return clone;
} /* v9-6cecbcfb32e29bf7 */
