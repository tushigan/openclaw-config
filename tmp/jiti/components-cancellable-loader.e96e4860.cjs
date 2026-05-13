"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.CancellableLoader = void 0;var _keybindings = require("../keybindings.js");
var _loader = require("./loader.js");
/**
 * Loader that can be cancelled with Escape.
 * Extends Loader with an AbortSignal for cancelling async operations.
 *
 * @example
 * const loader = new CancellableLoader(tui, cyan, dim, "Working...");
 * loader.onAbort = () => done(null);
 * doWork(loader.signal).then(done);
 */
class CancellableLoader extends _loader.Loader {
  abortController = new AbortController();
  /** Called when user presses Escape */
  onAbort;
  /** AbortSignal that is aborted when user presses Escape */
  get signal() {
    return this.abortController.signal;
  }
  /** Whether the loader was aborted */
  get aborted() {
    return this.abortController.signal.aborted;
  }
  handleInput(data) {
    const kb = (0, _keybindings.getKeybindings)();
    if (kb.matches(data, "tui.select.cancel")) {
      this.abortController.abort();
      this.onAbort?.();
    }
  }
  dispose() {
    this.stop();
  }
}exports.CancellableLoader = CancellableLoader; /* v9-c202cfeefd2f0a4c */
