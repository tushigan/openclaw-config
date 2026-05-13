"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Build = Build;exports.BuildResult = void 0;

var _index = require("../system/arguments/index.mjs");
var _index2 = require("../system/environment/index.mjs");
var _index3 = require("../system/hashing/index.mjs");
var _index4 = require("../guard/index.mjs");
var _index5 = require("../format/index.mjs");
var Engine = _interopRequireWildcard(require("./engine/index.mjs"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// deno-lint-ignore-file
// ------------------------------------------------------------------
// CreateCode
// ------------------------------------------------------------------
function CreateCode(build) {const functions = build.Functions().join(';\n');
  const statements = build.UseUnevaluated() ?
  ['const context = new CheckContext({}, {})', `return ${build.Call()}`] :
  [`return ${build.Call()}`];
  return `${functions}; return (value) => { ${statements.join('; ')} }`;
}
// ------------------------------------------------------------------
// CreateEvaluatedCheck
// ------------------------------------------------------------------
function CreateEvaluatedCheck(build, code) {
  const factory = _index2.Environment.Evaluate('CheckContext', 'Guard', 'Format', 'Hashing', build.External().identifier, code);
  return factory(Engine.CheckContext, _index4.Guard, _index5.Format, _index3.Hashing, build.External().variables);
}
// ------------------------------------------------------------------
// CreateDynamicCheck
// ------------------------------------------------------------------
function CreateDynamicCheck(build) {
  const stack = new Engine.Stack(build.Context(), build.Schema());
  const context = new Engine.CheckContext();
  return (value) => Engine.CheckSchema(stack, context, build.Schema(), value);
}
// ------------------------------------------------------------------
// CreateCheck
// ------------------------------------------------------------------
function CreateCheck(build, code) {
  return _index2.Environment.CanEvaluate() ?
  CreateEvaluatedCheck(build, code) :
  CreateDynamicCheck(build);
}
// ------------------------------------------------------------------
// BuildResult
// ------------------------------------------------------------------
class BuildResult {
  constructor(context, schema, external, functions, call, useUnevaluated) {
    this.context = context;
    this.schema = schema;
    this.external = external;
    this.functions = functions;
    this.call = call;
    this.useUnevaluated = useUnevaluated;
  }
  /** Returns the Context used for this build */
  Context() {
    return this.context;
  }
  /** Returns the Schema used for this build */
  Schema() {
    return this.schema;
  }
  /** Returns true if this build requires a Unevaluated context */
  UseUnevaluated() {
    return this.useUnevaluated;
  }
  /** Returns external variables */
  External() {
    return this.external;
  }
  /** Returns check functions */
  Functions() {
    return this.functions;
  }
  /** Return entry function call. */
  Call() {
    return this.call;
  }
  /** Evaluates the build into a validation function */
  Evaluate() {
    const Code = CreateCode(this);
    const Check = CreateCheck(this, Code);
    return { IsAccelerated: _index2.Environment.CanEvaluate(), Code, Check };
  }
}
/** Builds a schema into a optimized runtime validator */exports.BuildResult = BuildResult;
function Build(...args) {
  const [context, schema] = _index.Arguments.Match(args, {
    2: (context, schema) => [context, schema],
    1: (schema) => [{}, schema]
  });
  Engine.ResetExternal();
  Engine.ResetFunctions();
  const stack = new Engine.Stack(context, schema);
  const build = new Engine.BuildContext(Engine.HasUnevaluated(context, schema));
  const call = Engine.CreateFunction(stack, build, schema, 'value');
  const functions = Engine.GetFunctions();
  const externals = Engine.GetExternal();
  return new BuildResult(context, schema, externals, functions, call, build.UseUnevaluated());
} /* v9-385840fb2b7c0c49 */
