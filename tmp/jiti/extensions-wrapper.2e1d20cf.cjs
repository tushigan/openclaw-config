"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.wrapRegisteredTool = wrapRegisteredTool;exports.wrapRegisteredTools = wrapRegisteredTools;





var _toolDefinitionWrapper = require("../tools/tool-definition-wrapper.js"); /**
 * Tool wrappers for extension-registered tools.
 *
 * These wrappers only adapt tool execution so extension tools receive the runner context.
 * Tool call and tool result interception is handled by AgentSession via agent-core hooks.
 */ /**
 * Wrap a RegisteredTool into an AgentTool.
 * Uses the runner's createContext() for consistent context across tools and event handlers.
 */function wrapRegisteredTool(registeredTool, runner) {return (0, _toolDefinitionWrapper.wrapToolDefinition)(registeredTool.definition, () => runner.createContext());} /**
 * Wrap all registered tools into AgentTools.
 * Uses the runner's createContext() for consistent context across tools and event handlers.
 */
function wrapRegisteredTools(registeredTools, runner) {
  return (0, _toolDefinitionWrapper.wrapToolDefinitions)(registeredTools.map((registeredTool) => registeredTool.definition), () => runner.createContext());
} /* v9-c7e562f45251ce79 */
