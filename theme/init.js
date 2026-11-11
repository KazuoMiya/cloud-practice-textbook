/* Apply only a validated theme before the stylesheet paints. No external services. */
(function () {
  'use strict';
  try {
    var state = window.CloudBookState.read(localStorage.getItem('cloudbook.v1'), [], []);
    if (state.theme !== 'auto') document.documentElement.setAttribute('data-theme', state.theme);
  } catch (e) { /* Storage can be disabled without preventing reading. */ }
}());
