"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.DynamicRef = DynamicRef;exports.Ref = Ref;
var _index = require("../../guard/index.mjs");
var _index2 = require("../pointer/index.mjs");
var Schema = _interopRequireWildcard(require("../types/index.mjs"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Match: Id
// ------------------------------------------------------------------
function MatchId(schema, base, ref) {
  if (schema.$id === ref.hash)
  return schema;
  const absoluteId = new URL(schema.$id, base.href);
  const absoluteRef = new URL(ref.href, base.href);
  if (_index.Guard.IsEqual(absoluteId.pathname, absoluteRef.pathname)) {
    return ref.hash.startsWith('#') ? MatchHash(schema, base, ref) : schema;
  }
  return undefined;
}
// ------------------------------------------------------------------
// Match: Anchor
// ------------------------------------------------------------------
function MatchAnchor(schema, base, ref) {
  const absoluteAnchor = new URL(`#${schema.$anchor}`, base.href);
  const absoluteRef = new URL(ref.href, base.href);
  return _index.Guard.IsEqual(absoluteAnchor.href, absoluteRef.href) ? schema : undefined;
}
// ------------------------------------------------------------------
// Match: DynamicAnchor
// ------------------------------------------------------------------
function MatchDynamicAnchor(schema, base, ref) {
  const absoluteAnchor = new URL(`#${schema.$dynamicAnchor}`, base.href);
  const absoluteRef = new URL(ref.href, base.href);
  return _index.Guard.IsEqual(absoluteAnchor.href, absoluteRef.href) ? schema : undefined;
}
// ------------------------------------------------------------------
// Match: Hash
//
// Resolves JSON Pointer fragments only. Plain anchor-style fragments
// (no leading '/') are handled exclusively by MatchAnchor and
// MatchDynamicAnchor to prevent accidentally resolving an anchor name
// as a pointer into the schema tree.
//
// ------------------------------------------------------------------
function MatchHash(schema, _base, ref) {
  if (ref.href.endsWith('#'))
  return schema;
  if (!ref.hash.startsWith('#'))
  return undefined;
  const fragment = decodeURIComponent(ref.hash.slice(1));
  if (!fragment.startsWith('/'))
  return undefined;
  return _index2.Pointer.Get(schema, fragment);
}
// ------------------------------------------------------------------
// Match
// ------------------------------------------------------------------
function Match(schema, base, ref) {
  if (Schema.IsId(schema)) {
    const result = MatchId(schema, base, ref);
    if (!_index.Guard.IsUndefined(result))
    return result;
  }
  if (Schema.IsAnchor(schema)) {
    const result = MatchAnchor(schema, base, ref);
    if (!_index.Guard.IsUndefined(result))
    return result;
  }
  if (Schema.IsDynamicAnchor(schema)) {
    const result = MatchDynamicAnchor(schema, base, ref);
    if (!_index.Guard.IsUndefined(result))
    return result;
  }
  return MatchHash(schema, base, ref);
}
// ------------------------------------------------------------------
// FromArray
// ------------------------------------------------------------------
function FromArray(schema, base, ref) {
  return schema.reduce((result, item) => {
    const match = FromValue(item, base, ref);
    return !_index.Guard.IsUndefined(match) ? match : result;
  }, undefined);
}
// ------------------------------------------------------------------
// FromObject
// ------------------------------------------------------------------
function FromObject(schema, base, ref) {
  return _index.Guard.Keys(schema).reduce((result, key) => {
    const match = FromValue(schema[key], base, ref);
    return !_index.Guard.IsUndefined(match) ? match : result;
  }, undefined);
}
// ------------------------------------------------------------------
// FromValue
// ------------------------------------------------------------------
function FromValue(schema, base, ref) {
  const nextBase = Schema.IsSchemaObject(schema) && Schema.IsId(schema) ?
  new URL(schema.$id, base.href) :
  base;
  if (Schema.IsSchemaObject(schema)) {
    const result = Match(schema, nextBase, ref);
    if (!_index.Guard.IsUndefined(result))
    return result;
  }
  if (_index.Guard.IsArray(schema))
  return FromArray(schema, nextBase, ref);
  if (_index.Guard.IsObject(schema))
  return FromObject(schema, nextBase, ref);
  return undefined;
}
// ------------------------------------------------------------------
// Ref
// ------------------------------------------------------------------
function Ref(schema, ref) {
  const defaultBase = new URL('http://unknown/');
  const initialBase = Schema.IsId(schema) ? new URL(schema.$id, defaultBase.href) : defaultBase;
  const initialRef = new URL(ref, initialBase.href);
  return FromValue(schema, initialBase, initialRef);
}
// ------------------------------------------------------------------
// DynamicRef
// ------------------------------------------------------------------
function DynamicRef(root, base, dynamicRef, dynamicAnchors) {
  // Resolve the static target using either the local base (for fragment‑only references)
  // or the document root (for absolute URI references).
  const fragmentTarget = dynamicRef.$dynamicRef.startsWith('#') ?
  Ref(base, dynamicRef.$dynamicRef) :
  Ref(root, dynamicRef.$dynamicRef);
  if (_index.Guard.IsUndefined(fragmentTarget))
  return undefined;
  // Dynamic override only applies if the resolved target itself declares a $dynamicAnchor.
  // If it does not, return the static target unchanged.
  if (!Schema.IsSchemaObject(fragmentTarget) || !Schema.IsDynamicAnchor(fragmentTarget))
  return fragmentTarget;
  // Extract the fragment portion of the reference. According to the test suite,
  // only plain fragment names (e.g., "#foo") trigger the dynamic scope; JSON 
  // Pointer fragments (e.g., "#/definitions/foo") bypass dynamic resolution.
  const fragment = new URL(dynamicRef.$dynamicRef, 'http://unknown/').hash;
  if (fragment.startsWith('#/'))
  return fragmentTarget;
  // Search the live dynamic anchor stack for a schema whose $dynamicAnchor matches the
  // target's $dynamicAnchor. The stack reflects the current evaluation path, and
  // find() returns the outermost (first encountered) match, which is the correct
  // lexical scope per the specification.
  const anchorTarget = dynamicAnchors.find((anchor) => anchor.$dynamicAnchor === fragmentTarget.$dynamicAnchor);
  return anchorTarget ?? fragmentTarget;
} /* v9-2f8f4fe6c6ae5165 */
