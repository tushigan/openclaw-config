"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.detectSupportedImageMimeTypeFromFile = detectSupportedImageMimeTypeFromFile;var _promises = require("node:fs/promises");
var _fileType = require("file-type");
const IMAGE_MIME_TYPES = new Set(["image/jpeg", "image/png", "image/gif", "image/webp"]);
const FILE_TYPE_SNIFF_BYTES = 4100;
async function detectSupportedImageMimeTypeFromFile(filePath) {
  const fileHandle = await (0, _promises.open)(filePath, "r");
  try {
    const buffer = Buffer.alloc(FILE_TYPE_SNIFF_BYTES);
    const { bytesRead } = await fileHandle.read(buffer, 0, FILE_TYPE_SNIFF_BYTES, 0);
    if (bytesRead === 0) {
      return null;
    }
    const fileType = await (0, _fileType.fileTypeFromBuffer)(buffer.subarray(0, bytesRead));
    if (!fileType) {
      return null;
    }
    if (!IMAGE_MIME_TYPES.has(fileType.mime)) {
      return null;
    }
    return fileType.mime;
  } finally
  {
    await fileHandle.close();
  }
} /* v9-80e8e850b17bc20f */
