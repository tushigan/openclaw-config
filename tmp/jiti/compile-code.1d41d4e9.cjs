"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Code = Code;
var _index = require("../system/arguments/index.mjs");
var _index2 = require("../schema/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Comments and Formatting
// ------------------------------------------------------------------
function TsIgnore() {
  return `// @ts-ignore`;
}
function Separator() {
  return ``;
}
// ------------------------------------------------------------------
// ImportSection
// ------------------------------------------------------------------
function ImportSection(build) {
  const context = build.UseUnevaluated() ? [`import { CheckContext } from "typebox/schema"`] : [];
  const hashing = `import { Hashing } from "typebox/system"`;
  const format = `import { Format } from "typebox/format"`;
  const guard = `import { Guard } from "typebox/guard"`;
  return [...context, hashing, format, guard];
}
// ------------------------------------------------------------------
// ExternalSection
// ------------------------------------------------------------------
function ExternalSection(build) {
  const { identifier } = build.External();
  return [
  Separator(),
  TsIgnore(),
  `let ${identifier} = []`,
  Separator(),
  TsIgnore(),
  `export function SetExternal(external) { ${identifier} = external.variables }`];

}
// ------------------------------------------------------------------
// FunctionSection
// ------------------------------------------------------------------
function FunctionSection(build) {
  return build.Functions().map((func) => [Separator(), TsIgnore(), `${func};`].join('\n'));
}
// ------------------------------------------------------------------
// ExportSection
// ------------------------------------------------------------------
function ExportSection(build) {
  const body = build.UseUnevaluated() ?
  `const context = new CheckContext({}, {}); return ${build.Call()}` :
  `return ${build.Call()}`;
  return [
  Separator(),
  TsIgnore(),
  `export function Check(value) { ${body} }`];

}
/** Creates a standalone ESM validation module for the given type. */
function Code(...args) {
  const [context, type] = _index.Arguments.Match(args, {
    2: (context, type) => [context, type],
    1: (type) => [{}, type]
  });
  const build = (0, _index2.Build)(context, type);
  const code = [...ImportSection(build), ...ExternalSection(build), ...FunctionSection(build), ...ExportSection(build)].join('\n');
  return { External: build.External(), Code: code };
} /* v9-27d3d7cfaeb783d3 */
