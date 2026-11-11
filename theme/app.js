(function () {
  'use strict';
  var root = document.documentElement;
  var arts = Array.prototype.slice.call(document.querySelectorAll('article.ch'));
  if (!arts.length) return;
  root.classList.add('js');
  var keys = arts.map(function (a) { return a.id; });
  var byKey = Object.create(null);
  arts.forEach(function (a) { byKey[a.id] = a; });
  var KEY = 'cloudbook.v1';
  var checks = Array.prototype.map.call(document.querySelectorAll('input[data-ck]'), function (i) { return i.getAttribute('data-ck'); });
  var store = window.CloudBookState.read(null, keys, checks);
  try {
    var raw = localStorage.getItem(KEY);
    store = window.CloudBookState.read(raw, keys, checks);
  } catch (e) { /* storage unavailable: the book still works, progress is just not kept */ }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { /* ignore */ } }

  var side = document.getElementById('side'), menu = document.getElementById('menu');
  var bartitle = document.getElementById('bartitle'), toc = document.getElementById('toc');
  var hits = document.getElementById('hits'), search = document.getElementById('search');
  var current = null;

  function parseHash() {
    return window.CloudBookState.route(location.hash, keys);
  }
  function closeSide() { side.classList.remove('open'); if (menu) menu.setAttribute('aria-expanded', 'false'); }

  function show() {
    var p = parseHash();
    var changed = p.key !== current;
    if (changed) {
      arts.forEach(function (a) { a.hidden = a.id !== p.key; });
      root.removeAttribute('data-route');
      current = p.key;
      Array.prototype.forEach.call(toc.querySelectorAll('a'), function (a) {
        var on = a.getAttribute('data-toc') === p.key;
        a.classList.toggle('on', on);
        if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
      });
      var a = byKey[p.key];
      bartitle.textContent = (a.getAttribute('data-label') + ' ' + a.getAttribute('data-title')).trim();
      if (p.key !== keys[0]) { store.last = p.key; save(); }
      var on = toc.querySelector('a.on');
      if (on && on.scrollIntoView && window.matchMedia('(min-width: 60.01rem)').matches) on.scrollIntoView({ block: 'nearest' });
    }
    closeSide();
    var el = p.target ? document.getElementById(p.target) : null;
    if (el && byKey[p.key].contains(el)) el.scrollIntoView(); else if (changed) window.scrollTo(0, 0);
  }

  function paint() {
    var n = 0;
    keys.forEach(function (k) {
      var read = !!store.read[k];
      if (read) n++;
      var t = toc.querySelector('a[data-toc="' + k + '"]');
      if (t) t.classList.toggle('read', read);
      var b = document.querySelector('button[data-done="' + k + '"]');
      if (b) { b.setAttribute('aria-pressed', read ? 'true' : 'false'); b.textContent = read ? '読了済み（押すと取り消し）' : 'この章を読了にする'; }
    });
    document.getElementById('progtxt').textContent = '読了 ' + n + ' / ' + keys.length + ' 章';
    document.getElementById('progfill').value = n;
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest ? ev.target.closest('button[data-done]') : null;
    if (b) {
      var k = b.getAttribute('data-done');
      if (keys.indexOf(k) < 0) return;
      if (store.read[k]) delete store.read[k]; else store.read[k] = 1;
      save(); paint();
      return;
    }
    if (menu && (ev.target === menu)) {
      var open = !side.classList.contains('open');
      side.classList.toggle('open', open);
      menu.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) side.scrollTop = 0;
      return;
    }
    if (side.classList.contains('open') && !side.contains(ev.target)) closeSide();
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') closeSide(); });

  document.addEventListener('change', function (ev) {
    var t = ev.target;
    if (t && t.getAttribute && t.getAttribute('data-ck')) {
      if (checks.indexOf(t.getAttribute('data-ck')) < 0) return;
      if (t.checked) store.chk[t.getAttribute('data-ck')] = 1; else delete store.chk[t.getAttribute('data-ck')];
      save();
    }
  });
  Array.prototype.forEach.call(document.querySelectorAll('input[data-ck]'), function (i) {
    if (store.chk[i.getAttribute('data-ck')]) i.checked = true;
  });

  // ---- search: index is built from the page on first use ----
  var index = null;
  function build() {
    index = [];
    arts.forEach(function (a) {
      var label = a.getAttribute('data-label'), title = a.getAttribute('data-title');
      var body = a.querySelector('.body');
      var cur = { id: a.id, ch: (label + ' ' + title).trim(), sec: '', text: '' };
      Array.prototype.forEach.call(body.children, function (el) {
        if (el.tagName === 'H2') {
          if (cur.text) index.push(cur);
          var hn = el.querySelector('.hn'), no = hn ? hn.textContent : '';
          cur = { id: el.id, ch: (label + ' ' + title).trim(), sec: (no ? no + ' ' : '') + el.textContent.slice(no.length), text: '' };
        } else {
          cur.text += ' ' + el.textContent;
        }
      });
      if (cur.text) index.push(cur);
    });
    index.forEach(function (e) { e.text = e.text.replace(/\s+/g, ' '); e.low = (e.sec + ' ' + e.text).toLowerCase(); });
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function doSearch() {
    var q = search.value.trim().toLowerCase();
    if (q.length < 2) { hits.hidden = true; toc.hidden = false; hits.innerHTML = ''; return; }
    if (!index) build();
    var out = [], more = 0;
    index.forEach(function (e) {
      var i = e.low.indexOf(q);
      if (i < 0) return;
      if (out.length >= 40) { more++; return; }
      var j = e.text.toLowerCase().indexOf(q), snip;
      if (j < 0) snip = esc(e.text.slice(0, 60));
      else {
        var s = Math.max(0, j - 24);
        snip = (s ? '…' : '') + esc(e.text.slice(s, j)) + '<mark>' + esc(e.text.slice(j, j + q.length)) + '</mark>' + esc(e.text.slice(j + q.length, j + q.length + 40)) + '…';
      }
      out.push('<li><a href="#' + e.id + '"><b>' + esc(e.ch) + (e.sec ? '　' + esc(e.sec) : '') + '</b><span>' + snip + '</span></a></li>');
    });
    hits.innerHTML = out.length ? out.join('') + (more ? '<li class="none">ほか ' + more + ' 件。語を足して絞り込んでください</li>' : '')
      : '<li class="none">見つかりませんでした</li>';
    hits.hidden = false; toc.hidden = true;
  }
  if (search) search.addEventListener('input', doSearch);

  // ---- theme switch (only present on the standalone site) ----
  var tbtn = document.getElementById('theme');
  if (tbtn) {
    var modes = ['auto', 'light', 'dark'];
    var labels = { auto: '表示：端末に合わせる', light: '表示：ライト', dark: '表示：ダーク' };
    var applyTheme = function () {
      if (store.theme === 'light' || store.theme === 'dark') root.setAttribute('data-theme', store.theme);
      else { store.theme = 'auto'; root.removeAttribute('data-theme'); }
      tbtn.textContent = labels[store.theme];
    };
    tbtn.addEventListener('click', function () {
      store.theme = modes[(modes.indexOf(store.theme) + 1) % modes.length];
      save(); applyTheme();
    });
    applyTheme();
  }

  var resume = document.getElementById('resume');
  if (resume && store.last && byKey[store.last]) {
    var la = byKey[store.last];
    resume.innerHTML = '前回の続き：<a href="#' + store.last + '">' + esc(la.getAttribute('data-label') + ' ' + la.getAttribute('data-title')) + '</a>';
    resume.hidden = false;
  }
  window.addEventListener('hashchange', show);
  paint();
  show();
})();
