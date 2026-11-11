const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const state = require('../theme/state.js');
const source = fs.readFileSync(path.join(__dirname, '../theme/init.js'), 'utf8');
const chapters = 'guide what s6 ha';

function run(hash, {stored = null, dataChapters = chapters, storageThrows = false} = {}) {
  const attrs = {'data-chapters': dataChapters};
  const root = {
    getAttribute: (name) => (name in attrs ? attrs[name] : null),
    setAttribute: (name, value) => { attrs[name] = String(value); },
  };
  const context = {
    window: {CloudBookState: state},
    document: {documentElement: root},
    location: {hash},
    localStorage: {getItem: () => { if (storageThrows) throw new Error('blocked'); return stored; }},
  };
  vm.runInNewContext(source, context);
  return attrs;
}

test('a link to a chapter or a section marks that chapter before the first paint', () => {
  assert.equal(run('#ha')['data-route'], 'ha');
  assert.equal(run('#s6-3')['data-route'], 's6');
});
test('the guide, an empty hash and anything unknown leave the page as built', () => {
  for (const hash of ['', '#', '#guide', '#missing', '#constructor', '#__proto__', '#%E0%A4%A', '#<img src=x onerror=alert(1)>', '#ha"]{}', '#HA']) {
    assert.equal('data-route' in run(hash), false, hash);
  }
});
test('the route attribute is always one of the chapter keys written by the build', () => {
  for (const hash of ['#ha', '#%68a', '#s6-999', '#what']) {
    assert.ok(chapters.split(' ').includes(run(hash)['data-route']), hash);
  }
});
test('routing still works when storage is blocked, and a saved theme is still applied', () => {
  assert.equal(run('#ha', {storageThrows: true})['data-route'], 'ha');
  const attrs = run('#ha', {stored: JSON.stringify({theme: 'dark'})});
  assert.equal(attrs['data-theme'], 'dark');
  assert.equal(attrs['data-route'], 'ha');
});
test('a page without the chapter list is left alone', () => {
  assert.equal('data-route' in run('#ha', {dataChapters: ''}), false);
});
