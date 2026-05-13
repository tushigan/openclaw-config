"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.RepairError = void 0;class RepairError extends Error {
  constructor(context, type, value, message) {
    super(message);
    this.context = context;
    this.type = type;
    this.value = value;
  }
}exports.RepairError = RepairError; /* v9-e60579220e4fdd2b */
