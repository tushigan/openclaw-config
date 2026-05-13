"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Stack = void 0;






var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _index2 = require("../../guard/index.mjs");
var _index3 = require("../resolve/index.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
var __classPrivateFieldGet = this && this.__classPrivateFieldGet || function (receiver, state, kind, f) {if (kind === "a" && !f) throw new TypeError("Private accessor was defined without a getter");if (typeof state === "function" ? receiver !== state || !f : !state.has(receiver)) throw new TypeError("Cannot read private member from an object whose class did not declare it");return kind === "m" ? f : kind === "a" ? f.call(receiver) : f ? f.value : state.get(receiver);};var _Stack_instances, _Stack_PushResourceAnchors, _Stack_PopResourceAnchors, _Stack_FromContext, _Stack_FromRef;class Stack {
  constructor(context, schema) {
    _Stack_instances.add(this);
    this.context = context;
    this.schema = schema;
    this.ids = [];
    this.anchors = [];
    this.recursiveAnchors = [];
    this.dynamicAnchors = [];
  }
  // ----------------------------------------------------------------
  // Base
  // ----------------------------------------------------------------
  BaseURL() {
    return this.ids.reduce((result, schema) => new URL(schema.$id, result), new URL('http://unknown'));
  }
  Base() {
    return this.ids[this.ids.length - 1] ?? this.schema;
  }
  // ----------------------------------------------------------------
  // Stack
  // ----------------------------------------------------------------
  Push(schema) {
    if (!Schema.IsSchemaObject(schema))
    return;
    if (Schema.IsId(schema)) {
      this.ids.push(schema);
      __classPrivateFieldGet(this, _Stack_instances, "m", _Stack_PushResourceAnchors).call(this, schema);
    }
    if (Schema.IsAnchor(schema))
    this.anchors.push(schema);
    if (Schema.IsRecursiveAnchorTrue(schema))
    this.recursiveAnchors.push(schema);
    if (Schema.IsDynamicAnchor(schema))
    this.dynamicAnchors.push(schema);
  }
  Pop(schema) {
    if (!Schema.IsSchemaObject(schema))
    return;
    if (Schema.IsId(schema)) {
      this.ids.pop();
      __classPrivateFieldGet(this, _Stack_instances, "m", _Stack_PopResourceAnchors).call(this, schema);
    }
    if (Schema.IsAnchor(schema))
    this.anchors.pop();
    if (Schema.IsRecursiveAnchorTrue(schema))
    this.recursiveAnchors.pop();
    if (Schema.IsDynamicAnchor(schema))
    this.dynamicAnchors.pop();
  }
  Ref(ref) {
    return __classPrivateFieldGet(this, _Stack_instances, "m", _Stack_FromContext).call(this, ref) ?? __classPrivateFieldGet(this, _Stack_instances, "m", _Stack_FromRef).call(this, ref);
  }
  // ----------------------------------------------------------------
  // RecursiveRef
  // ----------------------------------------------------------------
  RecursiveRef(recursiveRef) {
    return Schema.IsRecursiveAnchorTrue(this.Base()) ?
    _index3.Resolve.Ref(this.recursiveAnchors[0], recursiveRef.$recursiveRef) :
    _index3.Resolve.Ref(this.Base(), recursiveRef.$recursiveRef);
  }
  // ----------------------------------------------------------------
  // DynamicRef
  // ----------------------------------------------------------------
  DynamicRef(dynamicRef) {
    const root = this.schema;
    return _index3.Resolve.DynamicRef(root, this.Base(), dynamicRef, this.dynamicAnchors);
  }
}exports.Stack = Stack;
_Stack_instances = new WeakSet(), _Stack_PushResourceAnchors = function _Stack_PushResourceAnchors(schema, isRoot = true) {
  if (!Schema.IsSchemaObject(schema))
  return;
  const current = schema;
  if (!isRoot && Schema.IsId(current))
  return;
  if (!isRoot && Schema.IsDynamicAnchor(current))
  this.dynamicAnchors.push(current);
  for (const key of _index2.Guard.Keys(current))
  __classPrivateFieldGet(this, _Stack_instances, "m", _Stack_PushResourceAnchors).call(this, current[key], false);
}, _Stack_PopResourceAnchors = function _Stack_PopResourceAnchors(schema, isRoot = true) {
  if (!Schema.IsSchemaObject(schema))
  return;
  const current = schema;
  if (!isRoot && Schema.IsId(current))
  return;
  if (!isRoot && Schema.IsDynamicAnchor(current))
  this.dynamicAnchors.pop();
  for (const key of _index2.Guard.Keys(current))
  __classPrivateFieldGet(this, _Stack_instances, "m", _Stack_PopResourceAnchors).call(this, current[key], false);
}, _Stack_FromContext = function _Stack_FromContext(ref) {
  return _index2.Guard.HasPropertyKey(this.context, ref.$ref) ? this.context[ref.$ref] : undefined;
}, _Stack_FromRef = function _Stack_FromRef(ref) {
  const root = this.schema;
  return !ref.$ref.startsWith('#') ?
  _index3.Resolve.Ref(root, ref.$ref) :
  _index3.Resolve.Ref(this.Base(), ref.$ref);
}; /* v9-8e723415c4a06622 */
