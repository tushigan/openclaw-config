"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Clear = Clear;exports.Entries = Entries;exports.Get = Get;exports.Has = Has;exports.Reset = Reset;exports.Set = Set;exports.Test = Test;var _date_time = require("./date_time.mjs");
var _date = require("./date.mjs");
var _duration = require("./duration.mjs");
var _email = require("./email.mjs");
var _hostname = require("./hostname.mjs");
var _idn_email = require("./idn_email.mjs");
var _idn_hostname = require("./idn_hostname.mjs");
var _ipv = require("./ipv4.mjs");
var _ipv2 = require("./ipv6.mjs");
var _iri_reference = require("./iri_reference.mjs");
var _iri = require("./iri.mjs");
var _json_pointer_uri_fragment = require("./json_pointer_uri_fragment.mjs");
var _json_pointer = require("./json_pointer.mjs");
var _regex = require("./regex.mjs");
var _relative_json_pointer = require("./relative_json_pointer.mjs");
var _time = require("./time.mjs");
var _uri_reference = require("./uri_reference.mjs");
var _uri_template = require("./uri_template.mjs");
var _uri = require("./uri.mjs");
var _url = require("./url.mjs");
var _uuid = require("./uuid.mjs");
// ------------------------------------------------------------------
// Formats
// ------------------------------------------------------------------
const formats = new Map();
// ------------------------------------------------------------------
// Clear
// ------------------------------------------------------------------
/** Clears all entries */
function Clear() {
  formats.clear();
}
// ------------------------------------------------------------------
// Entries
// ------------------------------------------------------------------
/** Returns format entries in this registry */
function Entries() {
  return [...formats.entries()];
}
// ------------------------------------------------------------------
// Set
// ------------------------------------------------------------------
/** Sets a format */
function Set(format, check) {
  formats.set(format, check);
}
// ------------------------------------------------------------------
// Has
// ------------------------------------------------------------------
/** Returns true if the registry has this format */
function Has(format) {
  return formats.has(format);
}
// ------------------------------------------------------------------
// Get
// ------------------------------------------------------------------
/** Gets a format or undefined if not exists */
function Get(format) {
  return formats.get(format);
}
// ------------------------------------------------------------------
// Test
// ------------------------------------------------------------------
/** Tests a value against a format, if the format is not registered, true */
function Test(format, value) {
  return formats.get(format)?.(value) ?? true;
}
// ------------------------------------------------------------------
// Reset
// ------------------------------------------------------------------
/** Resets all formats to defaults */
function Reset() {
  Clear();
  formats.set('date-time', _date_time.IsDateTime);
  formats.set('date', _date.IsDate);
  formats.set('duration', _duration.IsDuration);
  formats.set('email', _email.IsEmail);
  formats.set('hostname', _hostname.IsHostname);
  formats.set('idn-email', _idn_email.IsIdnEmail);
  formats.set('idn-hostname', _idn_hostname.IsIdnHostname);
  formats.set('ipv4', _ipv.IsIPv4);
  formats.set('ipv6', _ipv2.IsIPv6);
  formats.set('iri-reference', _iri_reference.IsIriReference);
  formats.set('iri', _iri.IsIri);
  formats.set('json-pointer-uri-fragment', _json_pointer_uri_fragment.IsJsonPointerUriFragment);
  formats.set('json-pointer', _json_pointer.IsJsonPointer);
  formats.set('regex', _regex.IsRegex);
  formats.set('relative-json-pointer', _relative_json_pointer.IsRelativeJsonPointer);
  formats.set('time', _time.IsTime);
  formats.set('uri-reference', _uri_reference.IsUriReference);
  formats.set('uri-template', _uri_template.IsUriTemplate);
  formats.set('uri', _uri.IsUri);
  formats.set('url', _url.IsUrl);
  formats.set('uuid', _uuid.IsUuid);
}
Reset(); /* v9-7f1415132c9a217a */
