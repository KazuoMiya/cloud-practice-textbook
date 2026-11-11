/* Apply only a validated theme and route before the first paint. No external services. */
(function () {
  'use strict';
  var root = document.documentElement;
  try {
    var state = window.CloudBookState.read(localStorage.getItem('cloudbook.v1'), [], []);
    if (state.theme !== 'auto') root.setAttribute('data-theme', state.theme);
  } catch (e) { /* Storage can be disabled without preventing reading. */ }
  try {
    /* A link to a chapter shows that chapter as soon as it is parsed, not the guide first.
       route() only returns a key from the list the build wrote into the page, so the
       attribute never carries text taken from the URL. app.js removes it once it routes. */
    var keys = (root.getAttribute('data-chapters') || '').split(' ');
    var route = window.CloudBookState.route(location.hash, keys);
    if (keys.length > 1 && route.key !== keys[0]) root.setAttribute('data-route', route.key);
  } catch (e) { /* app.js still routes after the page has loaded. */ }
}());
