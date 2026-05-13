"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.expandPromptTemplate = expandPromptTemplate;exports.loadPromptTemplates = loadPromptTemplates;exports.parseCommandArgs = parseCommandArgs;exports.substituteArgs = substituteArgs;var _fs = require("fs");
var _os = require("os");
var _path = require("path");
var _config = require("../config.js");
var _frontmatter = require("../utils/frontmatter.js");
var _sourceInfo = require("./source-info.js");
/**
 * Parse command arguments respecting quoted strings (bash-style)
 * Returns array of arguments
 */
function parseCommandArgs(argsString) {
  const args = [];
  let current = "";
  let inQuote = null;
  for (let i = 0; i < argsString.length; i++) {
    const char = argsString[i];
    if (inQuote) {
      if (char === inQuote) {
        inQuote = null;
      } else
      {
        current += char;
      }
    } else
    if (char === '"' || char === "'") {
      inQuote = char;
    } else
    if (char === " " || char === "\t") {
      if (current) {
        args.push(current);
        current = "";
      }
    } else
    {
      current += char;
    }
  }
  if (current) {
    args.push(current);
  }
  return args;
}
/**
 * Substitute argument placeholders in template content
 * Supports:
 * - $1, $2, ... for positional args
 * - $@ and $ARGUMENTS for all args
 * - ${@:N} for args from Nth onwards (bash-style slicing)
 * - ${@:N:L} for L args starting from Nth
 *
 * Note: Replacement happens on the template string only. Argument values
 * containing patterns like $1, $@, or $ARGUMENTS are NOT recursively substituted.
 */
function substituteArgs(content, args) {
  let result = content;
  // Replace $1, $2, etc. with positional args FIRST (before wildcards)
  // This prevents wildcard replacement values containing $<digit> patterns from being re-substituted
  result = result.replace(/\$(\d+)/g, (_, num) => {
    const index = parseInt(num, 10) - 1;
    return args[index] ?? "";
  });
  // Replace ${@:start} or ${@:start:length} with sliced args (bash-style)
  // Process BEFORE simple $@ to avoid conflicts
  result = result.replace(/\$\{@:(\d+)(?::(\d+))?\}/g, (_, startStr, lengthStr) => {
    let start = parseInt(startStr, 10) - 1; // Convert to 0-indexed (user provides 1-indexed)
    // Treat 0 as 1 (bash convention: args start at 1)
    if (start < 0)
    start = 0;
    if (lengthStr) {
      const length = parseInt(lengthStr, 10);
      return args.slice(start, start + length).join(" ");
    }
    return args.slice(start).join(" ");
  });
  // Pre-compute all args joined (optimization)
  const allArgs = args.join(" ");
  // Replace $ARGUMENTS with all args joined (new syntax, aligns with Claude, Codex, OpenCode)
  result = result.replace(/\$ARGUMENTS/g, allArgs);
  // Replace $@ with all args joined (existing syntax)
  result = result.replace(/\$@/g, allArgs);
  return result;
}
function loadTemplateFromFile(filePath, sourceInfo) {
  try {
    const rawContent = (0, _fs.readFileSync)(filePath, "utf-8");
    const { frontmatter, body } = (0, _frontmatter.parseFrontmatter)(rawContent);
    const name = (0, _path.basename)(filePath).replace(/\.md$/, "");
    // Get description from frontmatter or first non-empty line
    let description = frontmatter.description || "";
    if (!description) {
      const firstLine = body.split("\n").find((line) => line.trim());
      if (firstLine) {
        // Truncate if too long
        description = firstLine.slice(0, 60);
        if (firstLine.length > 60)
        description += "...";
      }
    }
    return {
      name,
      description,
      ...(frontmatter["argument-hint"] && { argumentHint: frontmatter["argument-hint"] }),
      content: body,
      sourceInfo,
      filePath
    };
  }
  catch {
    return null;
  }
}
/**
 * Scan a directory for .md files (non-recursive) and load them as prompt templates.
 */
function loadTemplatesFromDir(dir, getSourceInfo) {
  const templates = [];
  if (!(0, _fs.existsSync)(dir)) {
    return templates;
  }
  try {
    const entries = (0, _fs.readdirSync)(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = (0, _path.join)(dir, entry.name);
      // For symlinks, check if they point to a file
      let isFile = entry.isFile();
      if (entry.isSymbolicLink()) {
        try {
          const stats = (0, _fs.statSync)(fullPath);
          isFile = stats.isFile();
        }
        catch {
          // Broken symlink, skip it
          continue;
        }
      }
      if (isFile && entry.name.endsWith(".md")) {
        const template = loadTemplateFromFile(fullPath, getSourceInfo(fullPath));
        if (template) {
          templates.push(template);
        }
      }
    }
  }
  catch {
    return templates;
  }
  return templates;
}
function normalizePath(input) {
  const trimmed = input.trim();
  if (trimmed === "~")
  return (0, _os.homedir)();
  if (trimmed.startsWith("~/"))
  return (0, _path.join)((0, _os.homedir)(), trimmed.slice(2));
  if (trimmed.startsWith("~"))
  return (0, _path.join)((0, _os.homedir)(), trimmed.slice(1));
  return trimmed;
}
function resolvePromptPath(p, cwd) {
  const normalized = normalizePath(p);
  return (0, _path.isAbsolute)(normalized) ? normalized : (0, _path.resolve)(cwd, normalized);
}
/**
 * Load all prompt templates from:
 * 1. Global: agentDir/prompts/
 * 2. Project: cwd/{CONFIG_DIR_NAME}/prompts/
 * 3. Explicit prompt paths
 */
function loadPromptTemplates(options) {
  const resolvedCwd = options.cwd;
  const resolvedAgentDir = options.agentDir;
  const promptPaths = options.promptPaths;
  const includeDefaults = options.includeDefaults;
  const templates = [];
  const globalPromptsDir = options.agentDir ? (0, _path.join)(options.agentDir, "prompts") : resolvedAgentDir;
  const projectPromptsDir = (0, _path.resolve)(resolvedCwd, _config.CONFIG_DIR_NAME, "prompts");
  const isUnderPath = (target, root) => {
    const normalizedRoot = (0, _path.resolve)(root);
    if (target === normalizedRoot) {
      return true;
    }
    const prefix = normalizedRoot.endsWith(_path.sep) ? normalizedRoot : `${normalizedRoot}${_path.sep}`;
    return target.startsWith(prefix);
  };
  const getSourceInfo = (resolvedPath) => {
    if (isUnderPath(resolvedPath, globalPromptsDir)) {
      return (0, _sourceInfo.createSyntheticSourceInfo)(resolvedPath, {
        source: "local",
        scope: "user",
        baseDir: globalPromptsDir
      });
    }
    if (isUnderPath(resolvedPath, projectPromptsDir)) {
      return (0, _sourceInfo.createSyntheticSourceInfo)(resolvedPath, {
        source: "local",
        scope: "project",
        baseDir: projectPromptsDir
      });
    }
    return (0, _sourceInfo.createSyntheticSourceInfo)(resolvedPath, {
      source: "local",
      baseDir: (0, _fs.statSync)(resolvedPath).isDirectory() ? resolvedPath : (0, _path.dirname)(resolvedPath)
    });
  };
  if (includeDefaults) {
    templates.push(...loadTemplatesFromDir(globalPromptsDir, getSourceInfo));
    templates.push(...loadTemplatesFromDir(projectPromptsDir, getSourceInfo));
  }
  // 3. Load explicit prompt paths
  for (const rawPath of promptPaths) {
    const resolvedPath = resolvePromptPath(rawPath, resolvedCwd);
    if (!(0, _fs.existsSync)(resolvedPath)) {
      continue;
    }
    try {
      const stats = (0, _fs.statSync)(resolvedPath);
      if (stats.isDirectory()) {
        templates.push(...loadTemplatesFromDir(resolvedPath, getSourceInfo));
      } else
      if (stats.isFile() && resolvedPath.endsWith(".md")) {
        const template = loadTemplateFromFile(resolvedPath, getSourceInfo(resolvedPath));
        if (template) {
          templates.push(template);
        }
      }
    }
    catch {

      // Ignore read failures
    }}
  return templates;
}
/**
 * Expand a prompt template if it matches a template name.
 * Returns the expanded content or the original text if not a template.
 */
function expandPromptTemplate(text, templates) {
  if (!text.startsWith("/"))
  return text;
  const spaceIndex = text.indexOf(" ");
  const templateName = spaceIndex === -1 ? text.slice(1) : text.slice(1, spaceIndex);
  const argsString = spaceIndex === -1 ? "" : text.slice(spaceIndex + 1);
  const template = templates.find((t) => t.name === templateName);
  if (template) {
    const args = parseCommandArgs(argsString);
    return substituteArgs(template.content, args);
  }
  return text;
} /* v9-ba45c2bf7d8af841 */
