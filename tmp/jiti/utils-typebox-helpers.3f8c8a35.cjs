"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.StringEnum = StringEnum;var _typebox = require("typebox");
/**
 * Creates a string enum schema compatible with Google's API and other providers
 * that don't support anyOf/const patterns.
 *
 * @example
 * const OperationSchema = StringEnum(["add", "subtract", "multiply", "divide"], {
 *   description: "The operation to perform"
 * });
 *
 * type Operation = Static<typeof OperationSchema>; // "add" | "subtract" | "multiply" | "divide"
 */
function StringEnum(values, options) {
  return _typebox.Type.Unsafe({
    type: "string",
    enum: values,
    ...(options?.description && { description: options.description }),
    ...(options?.default && { default: options.default })
  });
} /* v9-eb09388be8dc5cdd */
