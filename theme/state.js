/* Treat URL fragments and saved progress as untrusted input. Also tested with Node. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CloudBookState = api;
}(typeof window === 'undefined' ? this : window, function () {
  'use strict';
  var own = function (obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); };
  function object(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
  function flags(value, allowed) {
    var result = Object.create(null);
    if (!object(value)) return result;
    allowed.forEach(function (key) {
      if (own(value, key) && (value[key] === true || value[key] === 1)) result[key] = 1;
    });
    return result;
  }
  function read(raw, keys, checks) {
    var value = {};
    try { if (typeof raw === 'string' && raw.length <= 1000000) value = JSON.parse(raw); } catch (e) { /* reset corrupt data */ }
    if (!object(value)) value = {};
    return {
      read: flags(value.read, keys), chk: flags(value.chk, checks),
      last: typeof value.last === 'string' && keys.indexOf(value.last) >= 0 ? value.last : null,
      theme: ['auto', 'light', 'dark'].indexOf(value.theme) >= 0 ? value.theme : 'auto'
    };
  }
  function route(hash, keys) {
    var fragment = '';
    try { fragment = decodeURIComponent(String(hash).replace(/^#/, '')); } catch (e) { /* use first chapter */ }
    var match = fragment.match(/^([a-z0-9]+)(-\d+)?$/);
    return match && keys.indexOf(match[1]) >= 0
      ? { key: match[1], target: match[2] ? fragment : null }
      : { key: keys[0], target: null };
  }
  return { read: read, route: route };
}));
