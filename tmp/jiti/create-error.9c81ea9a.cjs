"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.CreateError = void 0; // deno-fmt-ignore-file
class CreateError extends Error {
  constructor(type, message) {
    super(message);
    this.type = type;
  }
}exports.CreateError = CreateError; /* v9-1df17acbd444b822 */
