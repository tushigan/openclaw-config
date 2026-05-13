"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.appendAssistantMessageDiagnostic = appendAssistantMessageDiagnostic;exports.createAssistantMessageDiagnostic = createAssistantMessageDiagnostic;exports.extractDiagnosticError = extractDiagnosticError;exports.formatThrownValue = formatThrownValue;function formatThrownValue(value) {
  if (value instanceof Error)
  return value.message || value.name;
  if (typeof value === "string")
  return value;
  return String(value);
}
function extractDiagnosticError(error) {
  if (!(error instanceof Error))
  return { name: "ThrownValue", message: formatThrownValue(error) };
  const code = error.code;
  return {
    name: error.name || undefined,
    message: error.message || error.name,
    stack: error.stack,
    code: typeof code === "string" || typeof code === "number" ? code : undefined
  };
}
function createAssistantMessageDiagnostic(type, error, details) {
  return { type, timestamp: Date.now(), error: extractDiagnosticError(error), details };
}
function appendAssistantMessageDiagnostic(message, diagnostic) {
  message.diagnostics = [...(message.diagnostics ?? []), diagnostic];
} /* v9-7ca1f685723e6905 */
