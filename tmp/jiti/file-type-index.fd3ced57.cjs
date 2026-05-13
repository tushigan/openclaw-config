"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FileTypeParser = void 0;Object.defineProperty(exports, "fileTypeFromBlob", { enumerable: true, get: function () {return _core.fileTypeFromBlob;} });Object.defineProperty(exports, "fileTypeFromBuffer", { enumerable: true, get: function () {return _core.fileTypeFromBuffer;} });exports.fileTypeFromFile = fileTypeFromFile;exports.fileTypeFromStream = fileTypeFromStream;Object.defineProperty(exports, "fileTypeFromTokenizer", { enumerable: true, get: function () {return _core.fileTypeFromTokenizer;} });exports.fileTypeStream = fileTypeStream;Object.defineProperty(exports, "supportedExtensions", { enumerable: true, get: function () {return _core.supportedExtensions;} });Object.defineProperty(exports, "supportedMimeTypes", { enumerable: true, get: function () {return _core.supportedMimeTypes;} });



var _web = require("node:stream/web");
var _nodeStream = require("node:stream");
var _promises = _interopRequireDefault(require("node:fs/promises"));
var _nodeFs = require("node:fs");
var strtok3 = _interopRequireWildcard(require("strtok3"));
var _core = require("./core.js");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };} /**
Node.js specific entry point.
*/



function isTokenizerStreamBoundsError(error) {
  if (
  !(error instanceof RangeError) ||
  error.message !== 'offset is out of bounds' ||
  typeof error.stack !== 'string')
  {
    return false;
  }

  // Some malformed or non-byte Node.js streams can surface this tokenizer-internal range error.
  // Note: This stack-trace check is fragile and may break if strtok3 restructures its internals.
  return /strtok3[/\\]lib[/\\]stream[/\\]/.test(error.stack);
}

class FileTypeParser extends _core.FileTypeParser {
  async fromStream(stream) {
    this.options.signal?.throwIfAborted();
    const tokenizer = await (stream instanceof _web.ReadableStream ? this.createTokenizerFromWebStream(stream) : strtok3.fromStream(stream, this.getTokenizerOptions()));
    try {
      return await super.fromTokenizer(tokenizer);
    } catch (error) {
      if (isTokenizerStreamBoundsError(error)) {
        return;
      }

      throw error;
    } finally {
      // TODO: Remove this when `strtok3.fromStream()` closes the underlying Readable instead of only aborting tokenizer reads.
      if (
      stream instanceof _nodeStream.Readable &&
      !stream.destroyed)
      {
        stream.destroy();
      }
    }
  }

  async fromFile(path) {
    this.options.signal?.throwIfAborted();
    // TODO: Remove this when `strtok3.fromFile()` safely rejects non-regular filesystem objects without a pathname race.
    const fileHandle = await _promises.default.open(path, _nodeFs.constants.O_RDONLY | _nodeFs.constants.O_NONBLOCK);
    const fileStat = await fileHandle.stat();
    if (!fileStat.isFile()) {
      await fileHandle.close();
      return;
    }

    const tokenizer = new strtok3.FileTokenizer(fileHandle, {
      ...this.getTokenizerOptions(),
      fileInfo: {
        path,
        size: fileStat.size
      }
    });
    return super.fromTokenizer(tokenizer);
  }

  async toDetectionStream(readableStream, options = {}) {
    if (!(readableStream instanceof _nodeStream.Readable)) {
      return super.toDetectionStream(readableStream, options);
    }

    const { sampleSize = _core.reasonableDetectionSizeInBytes } = options;
    const { signal } = this.options;
    const normalizedSampleSize = (0, _core.normalizeSampleSize)(sampleSize);

    signal?.throwIfAborted();

    return new Promise((resolve, reject) => {
      let isSettled = false;

      const cleanup = () => {
        readableStream.off('error', onError);
        readableStream.off('readable', onReadable);
        signal?.removeEventListener('abort', onAbort);
      };

      const settle = (callback, value) => {
        if (isSettled) {
          return;
        }

        isSettled = true;
        cleanup();
        callback(value);
      };

      const onError = (error) => {
        settle(reject, error);
      };

      const onAbort = () => {
        if (!readableStream.destroyed) {
          readableStream.destroy();
        }

        settle(reject, signal.reason);
      };

      const onReadable = () => {
        (async () => {
          try {
            const pass = new _nodeStream.PassThrough();
            const outputStream = _nodeStream.pipeline ? (0, _nodeStream.pipeline)(readableStream, pass, () => {}) : readableStream.pipe(pass);
            const chunk = readableStream.read(normalizedSampleSize) ?? readableStream.read() ?? new Uint8Array(0);
            try {
              pass.fileType = await this.fromBuffer(chunk);
            } catch (error) {
              if (error instanceof strtok3.EndOfStreamError) {
                pass.fileType = undefined;
              } else {
                settle(reject, error);
              }
            }

            settle(resolve, outputStream);
          } catch (error) {
            settle(reject, error);
          }
        })();
      };

      readableStream.on('error', onError);
      readableStream.once('readable', onReadable);
      signal?.addEventListener('abort', onAbort, { once: true });
    });
  }
}exports.FileTypeParser = FileTypeParser;

async function fileTypeFromFile(path, options) {
  return new FileTypeParser(options).fromFile(path, options);
}

async function fileTypeFromStream(stream, options) {
  return new FileTypeParser(options).fromStream(stream);
}

async function fileTypeStream(readableStream, options = {}) {
  return new FileTypeParser(options).toDetectionStream(readableStream, options);
} /* v9-b310920d93f238ba */
