"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.defineTool = defineTool;exports.isBashToolResult = isBashToolResult;exports.isEditToolResult = isEditToolResult;exports.isFindToolResult = isFindToolResult;exports.isGrepToolResult = isGrepToolResult;exports.isLsToolResult = isLsToolResult;exports.isReadToolResult = isReadToolResult;exports.isToolCallEventType = isToolCallEventType;exports.isWriteToolResult = isWriteToolResult; /**
 * Extension system types.
 *
 * Extensions are TypeScript modules that can:
 * - Subscribe to agent lifecycle events
 * - Register LLM-callable tools
 * - Register commands, keyboard shortcuts, and CLI flags
 * - Interact with the user via UI primitives
 */
/**
 * Preserve parameter inference for standalone tool definitions.
 *
 * Use this when assigning a tool to a variable or passing it through arrays such
 * as `customTools`, where contextual typing would otherwise widen params to
 * `unknown`.
 */
function defineTool(tool) {
  return tool;
}
// Type guards for ToolResultEvent
function isBashToolResult(e) {
  return e.toolName === "bash";
}
function isReadToolResult(e) {
  return e.toolName === "read";
}
function isEditToolResult(e) {
  return e.toolName === "edit";
}
function isWriteToolResult(e) {
  return e.toolName === "write";
}
function isGrepToolResult(e) {
  return e.toolName === "grep";
}
function isFindToolResult(e) {
  return e.toolName === "find";
}
function isLsToolResult(e) {
  return e.toolName === "ls";
}
function isToolCallEventType(toolName, event) {
  return event.toolName === toolName;
} /* v9-6d55baed801cac93 */
