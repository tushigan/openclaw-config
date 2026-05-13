"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDuration = IsDuration;const Duration = /^P((\d+Y(\d+M(\d+D)?)?|\d+M(\d+D)?|\d+D)(T(\d+H(\d+M(\d+S)?)?|\d+M(\d+S)?|\d+S))?|T(\d+H(\d+M(\d+S)?)?|\d+M(\d+S)?|\d+S)|\d+W)$/;
/**
 * Returns true if the value is a valid ISO-8601 duration.
 * @specification https://tools.ietf.org/html/rfc3339
 */
function IsDuration(value) {
  return Duration.test(value);
} /* v9-264c873dd711c9a0 */
