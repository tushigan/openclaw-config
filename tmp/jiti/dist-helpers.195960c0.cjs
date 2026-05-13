"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.json = json;exports.req = req;exports.toBuffer = toBuffer;var http = _interopRequireWildcard(require("http"));
var https = _interopRequireWildcard(require("https"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
async function toBuffer(stream) {
  let length = 0;
  const chunks = [];
  for await (const chunk of stream) {
    length += chunk.length;
    chunks.push(chunk);
  }
  return Buffer.concat(chunks, length);
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function json(stream) {
  const buf = await toBuffer(stream);
  const str = buf.toString('utf8');
  try {
    return JSON.parse(str);
  }
  catch (_err) {
    const err = _err;
    err.message += ` (input: ${str})`;
    throw err;
  }
}
function req(url, opts = {}) {
  const href = typeof url === 'string' ? url : url.href;
  const req = (href.startsWith('https:') ? https : http).request(url, opts);
  const promise = new Promise((resolve, reject) => {
    req.
    once('response', resolve).
    once('error', reject).
    end();
  });
  req.then = promise.then.bind(promise);
  return req;
} /* v9-0d279c092a2a77fe */
