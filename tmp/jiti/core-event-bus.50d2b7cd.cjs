"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.createEventBus = createEventBus;var _nodeEvents = require("node:events");
function createEventBus() {
  const emitter = new _nodeEvents.EventEmitter();
  return {
    emit: (channel, data) => {
      emitter.emit(channel, data);
    },
    on: (channel, handler) => {
      const safeHandler = async (data) => {
        try {
          await handler(data);
        }
        catch (err) {
          console.error(`Event handler error (${channel}):`, err);
        }
      };
      emitter.on(channel, safeHandler);
      return () => emitter.off(channel, safeHandler);
    },
    clear: () => {
      emitter.removeAllListeners();
    }
  };
} /* v9-8e8361cdbca8be2b */
