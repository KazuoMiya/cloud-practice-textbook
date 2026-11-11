const test = require('node:test');
const assert = require('node:assert/strict');
const state = require('../theme/state.js');
const keys = ['guide', 'what', 's6'];
const checks = ['s6-c1'];

test('valid chapter and section fragments retain navigation targets', () => {
  assert.deepEqual(state.route('#s6-3', keys), {key: 's6', target: 's6-3'});
  assert.equal(state.route('#%77hat', keys).key, 'what');
});
test('prototype names, malformed encodings and nonexistent routes show the guide', () => {
  for (const hash of ['#constructor', '#__proto__', '#toString', '#%E0%A4%A', '#%', '#missing', '#s6-x', '#<img>']) {
    assert.deepEqual(state.route(hash, keys), {key: 'guide', target: null}, hash);
  }
});
test('corrupt storage and wrong top-level types do not disable progress', () => {
  for (const raw of ['{', 'null', '[]', '42', 'true', '"text"', null, 'x'.repeat(1000001)]) {
    const clean = state.read(raw, keys, checks);
    clean.read.what = 1;
    clean.chk['s6-c1'] = 1;
    assert.equal(clean.read.what, 1);
    assert.equal(clean.theme, 'auto');
    assert.equal(clean.last, null);
  }
});
test('known progress survives while injected and wrongly typed fields are ignored', () => {
  const clean = state.read('{"read":{"what":1,"s6":true,"guide":"yes","constructor":1,"__proto__":{"polluted":1}},"chk":{"s6-c1":true,"evil":1},"last":"s6","theme":"dark"}', keys, checks);
  assert.deepEqual(Object.keys(clean.read), ['what', 's6']);
  assert.deepEqual(Object.keys(clean.chk), ['s6-c1']);
  assert.equal(Object.getPrototypeOf(clean.read), null);
  assert.equal({}.polluted, undefined);
  assert.equal(clean.theme, 'dark');
  assert.equal(clean.last, 's6');
});
test('wrong nested types and invalid theme/resume never become application state', () => {
  for (const value of [null, 'text', 123, true, [], ['what']]) {
    const clean = state.read(JSON.stringify({read: value, chk: value, last: 'constructor', theme: 'constructor'}), keys, checks);
    assert.deepEqual(Object.keys(clean.read), []);
    assert.deepEqual(Object.keys(clean.chk), []);
    assert.equal(clean.last, null);
    assert.equal(clean.theme, 'auto');
  }
});
