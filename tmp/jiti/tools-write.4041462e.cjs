"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.createWriteTool = createWriteTool;exports.createWriteToolDefinition = createWriteToolDefinition;var _piTui = require("@mariozechner/pi-tui");
var _promises = require("fs/promises");
var _path = require("path");
var _typebox = require("typebox");
var _keybindingHints = require("../../modes/interactive/components/keybinding-hints.js");
var _theme = require("../../modes/interactive/theme/theme.js");
var _fileMutationQueue = require("./file-mutation-queue.js");
var _pathUtils = require("./path-utils.js");
var _renderUtils = require("./render-utils.js");
var _toolDefinitionWrapper = require("./tool-definition-wrapper.js");
const writeSchema = _typebox.Type.Object({
  path: _typebox.Type.String({ description: "Path to the file to write (relative or absolute)" }),
  content: _typebox.Type.String({ description: "Content to write to the file" })
});
const defaultWriteOperations = {
  writeFile: (path, content) => (0, _promises.writeFile)(path, content, "utf-8"),
  mkdir: (dir) => (0, _promises.mkdir)(dir, { recursive: true }).then(() => {})
};
class WriteCallRenderComponent extends _piTui.Text {
  cache;
  constructor() {
    super("", 0, 0);
  }
}
const WRITE_PARTIAL_FULL_HIGHLIGHT_LINES = 50;
function highlightSingleLine(line, lang) {
  const highlighted = (0, _theme.highlightCode)(line, lang);
  return highlighted[0] ?? "";
}
function refreshWriteHighlightPrefix(cache) {
  const prefixCount = Math.min(WRITE_PARTIAL_FULL_HIGHLIGHT_LINES, cache.normalizedLines.length);
  if (prefixCount === 0)
  return;
  const prefixSource = cache.normalizedLines.slice(0, prefixCount).join("\n");
  const prefixHighlighted = (0, _theme.highlightCode)(prefixSource, cache.lang);
  for (let i = 0; i < prefixCount; i++) {
    cache.highlightedLines[i] =
    prefixHighlighted[i] ?? highlightSingleLine(cache.normalizedLines[i] ?? "", cache.lang);
  }
}
function rebuildWriteHighlightCacheFull(rawPath, fileContent) {
  const lang = rawPath ? (0, _theme.getLanguageFromPath)(rawPath) : undefined;
  if (!lang)
  return undefined;
  const displayContent = (0, _renderUtils.normalizeDisplayText)(fileContent);
  const normalized = (0, _renderUtils.replaceTabs)(displayContent);
  return {
    rawPath,
    lang,
    rawContent: fileContent,
    normalizedLines: normalized.split("\n"),
    highlightedLines: (0, _theme.highlightCode)(normalized, lang)
  };
}
function updateWriteHighlightCacheIncremental(cache, rawPath, fileContent) {
  const lang = rawPath ? (0, _theme.getLanguageFromPath)(rawPath) : undefined;
  if (!lang)
  return undefined;
  if (!cache)
  return rebuildWriteHighlightCacheFull(rawPath, fileContent);
  if (cache.lang !== lang || cache.rawPath !== rawPath)
  return rebuildWriteHighlightCacheFull(rawPath, fileContent);
  if (!fileContent.startsWith(cache.rawContent))
  return rebuildWriteHighlightCacheFull(rawPath, fileContent);
  if (fileContent.length === cache.rawContent.length)
  return cache;
  const deltaRaw = fileContent.slice(cache.rawContent.length);
  const deltaDisplay = (0, _renderUtils.normalizeDisplayText)(deltaRaw);
  const deltaNormalized = (0, _renderUtils.replaceTabs)(deltaDisplay);
  cache.rawContent = fileContent;
  if (cache.normalizedLines.length === 0) {
    cache.normalizedLines.push("");
    cache.highlightedLines.push("");
  }
  const segments = deltaNormalized.split("\n");
  const lastIndex = cache.normalizedLines.length - 1;
  cache.normalizedLines[lastIndex] += segments[0];
  cache.highlightedLines[lastIndex] = highlightSingleLine(cache.normalizedLines[lastIndex], cache.lang);
  for (let i = 1; i < segments.length; i++) {
    cache.normalizedLines.push(segments[i]);
    cache.highlightedLines.push(highlightSingleLine(segments[i], cache.lang));
  }
  refreshWriteHighlightPrefix(cache);
  return cache;
}
function trimTrailingEmptyLines(lines) {
  let end = lines.length;
  while (end > 0 && lines[end - 1] === "") {
    end--;
  }
  return lines.slice(0, end);
}
function formatWriteCall(args, options, theme, cache) {
  const rawPath = (0, _renderUtils.str)(args?.file_path ?? args?.path);
  const fileContent = (0, _renderUtils.str)(args?.content);
  const path = rawPath !== null ? (0, _renderUtils.shortenPath)(rawPath) : null;
  const invalidArg = (0, _renderUtils.invalidArgText)(theme);
  let text = `${theme.fg("toolTitle", theme.bold("write"))} ${path === null ? invalidArg : path ? theme.fg("accent", path) : theme.fg("toolOutput", "...")}`;
  if (fileContent === null) {
    text += `\n\n${theme.fg("error", "[invalid content arg - expected string]")}`;
  } else
  if (fileContent) {
    const lang = rawPath ? (0, _theme.getLanguageFromPath)(rawPath) : undefined;
    const renderedLines = lang ?
    cache?.highlightedLines ?? (0, _theme.highlightCode)((0, _renderUtils.replaceTabs)((0, _renderUtils.normalizeDisplayText)(fileContent)), lang) :
    (0, _renderUtils.normalizeDisplayText)(fileContent).split("\n");
    const lines = trimTrailingEmptyLines(renderedLines);
    const totalLines = lines.length;
    const maxLines = options.expanded ? lines.length : 10;
    const displayLines = lines.slice(0, maxLines);
    const remaining = lines.length - maxLines;
    text += `\n\n${displayLines.map((line) => lang ? line : theme.fg("toolOutput", (0, _renderUtils.replaceTabs)(line))).join("\n")}`;
    if (remaining > 0) {
      text += `${theme.fg("muted", `\n... (${remaining} more lines, ${totalLines} total,`)} ${(0, _keybindingHints.keyHint)("app.tools.expand", "to expand")})`;
    }
  }
  return text;
}
function formatWriteResult(result, theme) {
  if (!result.isError) {
    return undefined;
  }
  const output = result.content.
  filter((c) => c.type === "text").
  map((c) => c.text || "").
  join("\n");
  if (!output) {
    return undefined;
  }
  return `\n${theme.fg("error", output)}`;
}
function createWriteToolDefinition(cwd, options) {
  const ops = options?.operations ?? defaultWriteOperations;
  return {
    name: "write",
    label: "write",
    description: "Write content to a file. Creates the file if it doesn't exist, overwrites if it does. Automatically creates parent directories.",
    promptSnippet: "Create or overwrite files",
    promptGuidelines: ["Use write only for new files or complete rewrites."],
    parameters: writeSchema,
    async execute(_toolCallId, { path, content }, signal, _onUpdate, _ctx) {
      const absolutePath = (0, _pathUtils.resolveToCwd)(path, cwd);
      const dir = (0, _path.dirname)(absolutePath);
      return (0, _fileMutationQueue.withFileMutationQueue)(absolutePath, () => new Promise((resolve, reject) => {
        if (signal?.aborted) {
          reject(new Error("Operation aborted"));
          return;
        }
        let aborted = false;
        const onAbort = () => {
          aborted = true;
          reject(new Error("Operation aborted"));
        };
        signal?.addEventListener("abort", onAbort, { once: true });
        (async () => {
          try {
            // Create parent directories if needed.
            await ops.mkdir(dir);
            if (aborted)
            return;
            // Write the file contents.
            await ops.writeFile(absolutePath, content);
            if (aborted)
            return;
            signal?.removeEventListener("abort", onAbort);
            resolve({
              content: [
              { type: "text", text: `Successfully wrote ${content.length} bytes to ${path}` }],

              details: undefined
            });
          }
          catch (error) {
            signal?.removeEventListener("abort", onAbort);
            if (!aborted)
            reject(error);
          }
        })();
      }));
    },
    renderCall(args, theme, context) {
      const renderArgs = args;
      const rawPath = (0, _renderUtils.str)(renderArgs?.file_path ?? renderArgs?.path);
      const fileContent = (0, _renderUtils.str)(renderArgs?.content);
      const component = context.lastComponent ?? new WriteCallRenderComponent();
      if (fileContent !== null) {
        component.cache = context.argsComplete ?
        rebuildWriteHighlightCacheFull(rawPath, fileContent) :
        updateWriteHighlightCacheIncremental(component.cache, rawPath, fileContent);
      } else
      {
        component.cache = undefined;
      }
      component.setText(formatWriteCall(renderArgs, { expanded: context.expanded, isPartial: context.isPartial }, theme, component.cache));
      return component;
    },
    renderResult(result, _options, theme, context) {
      const output = formatWriteResult({ ...result, isError: context.isError }, theme);
      if (!output) {
        const component = context.lastComponent ?? new _piTui.Container();
        component.clear();
        return component;
      }
      const text = context.lastComponent ?? new _piTui.Text("", 0, 0);
      text.setText(output);
      return text;
    }
  };
}
function createWriteTool(cwd, options) {
  return (0, _toolDefinitionWrapper.wrapToolDefinition)(createWriteToolDefinition(cwd, options));
} /* v9-24fed401ce32be03 */
