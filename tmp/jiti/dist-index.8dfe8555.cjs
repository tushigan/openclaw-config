"use strict";Object.defineProperty(exports, "__esModule", { value: true });var _exportNames = { Agent: true };exports.Agent = void 0;var net = _interopRequireWildcard(require("net"));
var http = _interopRequireWildcard(require("http"));
var _https = require("https");
var _helpers = require("./helpers.js");Object.keys(_helpers).forEach(function (key) {if (key === "default" || key === "__esModule") return;if (Object.prototype.hasOwnProperty.call(_exportNames, key)) return;if (key in exports && exports[key] === _helpers[key]) return;Object.defineProperty(exports, key, { enumerable: true, get: function () {return _helpers[key];} });});function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
const INTERNAL = Symbol('AgentBaseInternalState');
class Agent extends http.Agent {
  constructor(opts) {
    super(opts);
    this[INTERNAL] = {};
  }
  /**
   * Determine whether this is an `http` or `https` request.
   */
  isSecureEndpoint(options) {
    if (options) {
      // First check the `secureEndpoint` property explicitly, since this
      // means that a parent `Agent` is "passing through" to this instance.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if (typeof options.secureEndpoint === 'boolean') {
        return options.secureEndpoint;
      }
      // If no explicit `secure` endpoint, check if `protocol` property is
      // set. This will usually be the case since using a full string URL
      // or `URL` instance should be the most common usage.
      if (typeof options.protocol === 'string') {
        return options.protocol === 'https:';
      }
    }
    // Finally, if no `protocol` property was set, then fall back to
    // checking the stack trace of the current call stack, and try to
    // detect the "https" module.
    const { stack } = new Error();
    if (typeof stack !== 'string')
    return false;
    return stack.
    split('\n').
    some((l) => l.indexOf('(https.js:') !== -1 ||
    l.indexOf('node:https:') !== -1);
  }
  // In order to support async signatures in `connect()` and Node's native
  // connection pooling in `http.Agent`, the array of sockets for each origin
  // has to be updated synchronously. This is so the length of the array is
  // accurate when `addRequest()` is next called. We achieve this by creating a
  // fake socket and adding it to `sockets[origin]` and incrementing
  // `totalSocketCount`.
  incrementSockets(name) {
    // If `maxSockets` and `maxTotalSockets` are both Infinity then there is no
    // need to create a fake socket because Node.js native connection pooling
    // will never be invoked.
    if (this.maxSockets === Infinity && this.maxTotalSockets === Infinity) {
      return null;
    }
    // All instances of `sockets` are expected TypeScript errors. The
    // alternative is to add it as a private property of this class but that
    // will break TypeScript subclassing.
    if (!this.sockets[name]) {
      // @ts-expect-error `sockets` is readonly in `@types/node`
      this.sockets[name] = [];
    }
    const fakeSocket = new net.Socket({ writable: false });
    this.sockets[name].push(fakeSocket);
    // @ts-expect-error `totalSocketCount` isn't defined in `@types/node`
    this.totalSocketCount++;
    return fakeSocket;
  }
  decrementSockets(name, socket) {
    if (!this.sockets[name] || socket === null) {
      return;
    }
    const sockets = this.sockets[name];
    const index = sockets.indexOf(socket);
    if (index !== -1) {
      sockets.splice(index, 1);
      // @ts-expect-error  `totalSocketCount` isn't defined in `@types/node`
      this.totalSocketCount--;
      if (sockets.length === 0) {
        // @ts-expect-error `sockets` is readonly in `@types/node`
        delete this.sockets[name];
      }
    }
  }
  // In order to properly update the socket pool, we need to call `getName()` on
  // the core `https.Agent` if it is a secureEndpoint.
  getName(options) {
    const secureEndpoint = this.isSecureEndpoint(options);
    if (secureEndpoint) {
      return _https.Agent.prototype.getName.call(this, options);
    }
    return super.getName(options);
  }
  createSocket(req, options, cb) {
    const connectOpts = {
      ...options,
      secureEndpoint: this.isSecureEndpoint(options)
    };
    const name = this.getName(connectOpts);
    const fakeSocket = this.incrementSockets(name);
    Promise.resolve().
    then(() => this.connect(req, connectOpts)).
    then((socket) => {
      this.decrementSockets(name, fakeSocket);
      if (typeof socket.
      addRequest === 'function') {
        try {
          return socket.addRequest(req, connectOpts);
        }
        catch (err) {
          return cb(err);
        }
      }
      this[INTERNAL].currentSocket = socket;
      // @ts-expect-error `createSocket()` isn't defined in `@types/node`
      super.createSocket(req, options, cb);
    }, (err) => {
      this.decrementSockets(name, fakeSocket);
      cb(err);
    });
  }
  createConnection() {
    const socket = this[INTERNAL].currentSocket;
    this[INTERNAL].currentSocket = undefined;
    if (!socket) {
      throw new Error('No socket was returned in the `connect()` function');
    }
    return socket;
  }
  get defaultPort() {
    return this[INTERNAL].defaultPort ?? (
    this.protocol === 'https:' ? 443 : 80);
  }
  set defaultPort(v) {
    if (this[INTERNAL]) {
      this[INTERNAL].defaultPort = v;
    }
  }
  get protocol() {
    return this[INTERNAL].protocol ?? (
    this.isSecureEndpoint() ? 'https:' : 'http:');
  }
  set protocol(v) {
    if (this[INTERNAL]) {
      this[INTERNAL].protocol = v;
    }
  }
}exports.Agent = Agent; /* v9-94d54973dfd2bd27 */
