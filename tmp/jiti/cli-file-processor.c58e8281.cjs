"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.processFileArguments = processFileArguments;


var _promises = require("node:fs/promises");
var _chalk = _interopRequireDefault(require("chalk"));
var _path = require("path");
var _pathUtils = require("../core/tools/path-utils.js");
var _imageResize = require("../utils/image-resize.js");
var _mime = require("../utils/mime.js");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };} /**
 * Process @file CLI arguments into text content and image attachments
 */ /** Process @file arguments into text content and image attachments */async function processFileArguments(fileArgs, options) {
  const autoResizeImages = options?.autoResizeImages ?? true;
  let text = "";
  const images = [];
  for (const fileArg of fileArgs) {
    // Expand and resolve path (handles ~ expansion and macOS screenshot Unicode spaces)
    const absolutePath = (0, _path.resolve)((0, _pathUtils.resolveReadPath)(fileArg, process.cwd()));
    // Check if file exists
    try {
      await (0, _promises.access)(absolutePath);
    }
    catch {
      console.error(_chalk.default.red(`Error: File not found: ${absolutePath}`));
      process.exit(1);
    }
    // Check if file is empty
    const stats = await (0, _promises.stat)(absolutePath);
    if (stats.size === 0) {
      // Skip empty files
      continue;
    }
    const mimeType = await (0, _mime.detectSupportedImageMimeTypeFromFile)(absolutePath);
    if (mimeType) {
      // Handle image file
      const content = await (0, _promises.readFile)(absolutePath);
      const base64Content = content.toString("base64");
      let attachment;
      let dimensionNote;
      if (autoResizeImages) {
        const resized = await (0, _imageResize.resizeImage)({ type: "image", data: base64Content, mimeType });
        if (!resized) {
          text += `<file name="${absolutePath}">[Image omitted: could not be resized below the inline image size limit.]</file>\n`;
          continue;
        }
        dimensionNote = (0, _imageResize.formatDimensionNote)(resized);
        attachment = {
          type: "image",
          mimeType: resized.mimeType,
          data: resized.data
        };
      } else
      {
        attachment = {
          type: "image",
          mimeType,
          data: base64Content
        };
      }
      images.push(attachment);
      // Add text reference to image with optional dimension note
      if (dimensionNote) {
        text += `<file name="${absolutePath}">${dimensionNote}</file>\n`;
      } else
      {
        text += `<file name="${absolutePath}"></file>\n`;
      }
    } else
    {
      // Handle text file
      try {
        const content = await (0, _promises.readFile)(absolutePath, "utf-8");
        text += `<file name="${absolutePath}">\n${content}\n</file>\n`;
      }
      catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error(_chalk.default.red(`Error: Could not read file ${absolutePath}: ${message}`));
        process.exit(1);
      }
    }
  }
  return { text, images };
} /* v9-7c727eab7afae564 */
