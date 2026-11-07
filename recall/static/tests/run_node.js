// Run with: node recall/static/tests/run_node.js
const store = {};
global.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } };
const L = require("../learning.js");
const run = require("./learning.tests.js");
let fail = 0;
run(L, (name, ok, info) => { console.log((ok ? "PASS " : "FAIL ") + name + (ok ? "" : "  " + JSON.stringify(info))); if (!ok) fail++; });
process.exit(fail ? 1 : 0);
