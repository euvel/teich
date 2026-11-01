// delib.js must agree with Python's delib_cert bit for bit (choice, steps, rereads, final x and y, undecided)
//   node test_delib.js VECTORS.json CONSTANTS.json
const fs = require("fs");
const { makeDelib, hexf } = require("../delib.js");
const V = JSON.parse(fs.readFileSync(process.argv[2]));
const D = makeDelib(JSON.parse(fs.readFileSync(process.argv[3])));
let bad = 0, n = 0;
for (const [k, u, c, steps, rr, xh, yh, und] of V.vectors) {
  const r = D.deliberate(k, hexf(u)); n++;
  if (r.choice !== c || r.steps !== steps || r.rereads !== rr || r.x !== hexf(xh) || r.y !== hexf(yh) || r.undecided !== und) {
    if (bad++ < 5) console.log("MISMATCH", k, u, { py: [c, steps, rr, xh, yh, und], js: r });
  }
}
let badc = 0;
for (const ch of V.choices) if (D.think2(ch.lc, ch.u).region !== ch.act) badc++;
// hex parsing must be exact (round trip through a few awkward values)
const probes = ["0x1.0000000000000p+0", "0x1.fffffffffffffp-1", "-0x1.921fb54442d18p+0", "0x0.0p+0", "0x1.2ce3334440000p-1"];
const hexok = probes.every((h) => hexf(h) === (h === "0x0.0p+0" ? 0 : Number(eval(h.replace(/0x([01])\.([0-9a-f]+)p([+-]?\d+)/, (m, a, b, e) => `(${parseInt(a + b, 16)} / 2**${4 * b.length}) * 2**${e}`)))));
console.log(`deliberate: ${n - bad}/${n} bit-exact · think@2 choices: ${V.choices.length - badc}/${V.choices.length} · hex parse ${hexok ? "exact" : "WRONG"} (lab nights ${V.lab_nights})`);
process.exit(bad || badc || !hexok ? 1 : 0);
