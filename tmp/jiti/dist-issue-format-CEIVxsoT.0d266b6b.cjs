"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = normalizeConfigIssuePath;exports.i = normalizeConfigIssue;exports.n = formatConfigIssueLines;exports.o = normalizeConfigIssues;exports.r = formatConfigIssueSummary;exports.t = formatConfigIssueLine;var _safeTextBe5ocph = require("./safe-text-Be-5ocph.js");
//#region src/config/issue-format.ts
function normalizeConfigIssuePath(path) {
  if (typeof path !== "string") return "<root>";
  const trimmed = path.trim();
  return trimmed ? trimmed : "<root>";
}
function normalizeConfigIssue(issue) {
  const hasAllowedValues = Array.isArray(issue.allowedValues) && issue.allowedValues.length > 0;
  return {
    path: normalizeConfigIssuePath(issue.path),
    message: issue.message,
    ...(hasAllowedValues ? { allowedValues: issue.allowedValues } : {}),
    ...(hasAllowedValues && typeof issue.allowedValuesHiddenCount === "number" && issue.allowedValuesHiddenCount > 0 ? { allowedValuesHiddenCount: issue.allowedValuesHiddenCount } : {})
  };
}
function normalizeConfigIssues(issues) {
  return issues.map((issue) => normalizeConfigIssue(issue));
}
function resolveIssuePathForLine(path, opts) {
  if (opts?.normalizeRoot) return normalizeConfigIssuePath(path);
  return typeof path === "string" ? path : "";
}
function formatConfigIssueLine(issue, marker = "-", opts) {
  return `${marker ? `${marker} ` : ""}${(0, _safeTextBe5ocph.t)(resolveIssuePathForLine(issue.path, opts))}: ${(0, _safeTextBe5ocph.t)(issue.message)}`;
}
function formatConfigIssueLines(issues, marker = "-", opts) {
  return issues.map((issue) => formatConfigIssueLine(issue, marker, opts));
}
function formatConfigIssueSummary(issues, opts = {}) {
  if (issues.length === 0) return null;
  const maxIssueCandidate = Math.floor(opts.maxIssues ?? 5);
  const maxIssues = Number.isFinite(maxIssueCandidate) ? Math.max(1, maxIssueCandidate) : 5;
  const visibleIssues = issues.slice(0, maxIssues);
  const lines = formatConfigIssueLines(visibleIssues, "", { normalizeRoot: opts.normalizeRoot ?? true });
  const hiddenIssueCount = issues.length - visibleIssues.length;
  if (hiddenIssueCount <= 0) return lines.join("; ");
  return `${lines.join("; ")}; and ${hiddenIssueCount} more`;
}
//#endregion /* v9-ebcf82a6fc128648 */
