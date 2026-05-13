"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDateTime = IsDateTime;var _date = require("./date.mjs");
var _time = require("./time.mjs");
/**
 * Returns true if the value is a ISO8601 DateTime string
 * @source ajv-formats
 * @example `2020-12-12T20:20:40+00:00`
 */
function IsDateTime(value, strictTimeZone = true) {
  const dateTime = value.split(/T/i);
  return dateTime.length === 2 && (0, _date.IsDate)(dateTime[0]) && (0, _time.IsTime)(dateTime[1], strictTimeZone);
} /* v9-04af4f151a77e0ff */
