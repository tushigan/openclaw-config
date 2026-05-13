"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.EventStream = exports.AssistantMessageEventStream = void 0;exports.createAssistantMessageEventStream = createAssistantMessageEventStream; // Generic event stream class for async iteration
class EventStream {
  isComplete;
  extractResult;
  queue = [];
  waiting = [];
  done = false;
  finalResultPromise;
  resolveFinalResult;
  constructor(isComplete, extractResult) {
    this.isComplete = isComplete;
    this.extractResult = extractResult;
    this.finalResultPromise = new Promise((resolve) => {
      this.resolveFinalResult = resolve;
    });
  }
  push(event) {
    if (this.done)
    return;
    if (this.isComplete(event)) {
      this.done = true;
      this.resolveFinalResult(this.extractResult(event));
    }
    // Deliver to waiting consumer or queue it
    const waiter = this.waiting.shift();
    if (waiter) {
      waiter({ value: event, done: false });
    } else
    {
      this.queue.push(event);
    }
  }
  end(result) {
    this.done = true;
    if (result !== undefined) {
      this.resolveFinalResult(result);
    }
    // Notify all waiting consumers that we're done
    while (this.waiting.length > 0) {
      const waiter = this.waiting.shift();
      waiter({ value: undefined, done: true });
    }
  }
  async *[Symbol.asyncIterator]() {
    while (true) {
      if (this.queue.length > 0) {
        yield this.queue.shift();
      } else
      if (this.done) {
        return;
      } else
      {
        const result = await new Promise((resolve) => this.waiting.push(resolve));
        if (result.done)
        return;
        yield result.value;
      }
    }
  }
  result() {
    return this.finalResultPromise;
  }
}exports.EventStream = EventStream;
class AssistantMessageEventStream extends EventStream {
  constructor() {
    super((event) => event.type === "done" || event.type === "error", (event) => {
      if (event.type === "done") {
        return event.message;
      } else
      if (event.type === "error") {
        return event.error;
      }
      throw new Error("Unexpected event type for final result");
    });
  }
}
/** Factory function for AssistantMessageEventStream (for use in extensions) */exports.AssistantMessageEventStream = AssistantMessageEventStream;
function createAssistantMessageEventStream() {
  return new AssistantMessageEventStream();
} /* v9-72f10d1cc69c52c9 */
