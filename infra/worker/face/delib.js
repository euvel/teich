// Teich v0.6's certified deliberation, ported line for line from v06/build/delib_cert.py so a visitor's browser can
// re-decide its ties. Same fixed operation order; only + - * /, Math.sqrt, Math.floor and % on non-negative values,
// each correctly rounded or exact in IEEE-754 doubles, as in Python. Tested bit-exact against Python (face/test_delib).
"use strict";

// exact parse of a float.hex() string ("0x1.9e3779b97f4a8p-1"): every partial sum fits in 53 bits
function hexf(s) {
  let neg = s[0] === "-";
  if (neg) s = s.slice(1);
  const pe = s.slice(2).split("p"), mf = pe[0].split(".");
  let v = parseInt(mf[0], 16);
  const f = mf[1] || "";
  for (let j = 0; j < f.length; j++) v += parseInt(f[j], 16) / Math.pow(16, j + 1);
  v = v * Math.pow(2, parseInt(pe[1], 10));
  return neg ? -v : v;
}

function makeDelib(C) {
  const HALF_PI = hexf(C.half_pi);
  const INV_FACT = C.inv_fact.map(hexf);
  const K = {};
  for (const k of Object.keys(C.k)) {
    const v = C.k[k];
    K[k] = { walls: v.walls, cos_w: hexf(v.cos_w), r2: hexf(v.r2),
             centre: v.centre.map((p) => [hexf(p[0]), hexf(p[1])]), C: v.C.map((p) => [hexf(p[0]), hexf(p[1])]),
             gap: v.gap_centre.map((p) => [hexf(p[0]), hexf(p[1])]) };
  }
  const N_MAX = 400, MAX_REREAD = 8;

  function cosSin(t) {
    const t2 = t * t;
    let c = INV_FACT[24];
    for (let m = 11; m >= 0; m--) c = INV_FACT[2 * m] - t2 * c;
    let s = INV_FACT[25];
    for (let m = 11; m >= 0; m--) s = INV_FACT[2 * m + 1] - t2 * s;
    return [c, s * t];
  }

  function xiOf(u) {
    const v = 4.0 * u;
    let q = Math.floor(v);
    const r = v - q;
    const cs = cosSin(r * HALF_PI), c = cs[0], s = cs[1];
    q = q % 4;
    if (q === 0) return [c, s];
    if (q === 1) return [-s, c];
    if (q === 2) return [-c, -s];
    return [s, -c];
  }

  // -> {choice, steps, rereads, x, y, undecided, path: [[x, y], ...]} (path = every point it visited, for drawing)
  function deliberate(k, u) {
    const G = K[k], nw = G.walls, cw = G.cos_w, r2 = G.r2;
    let rereads = 0, path = [];
    for (;;) {
      let xy = xiOf(u), x = xy[0], y = xy[1];
      path.push([x, y]);
      let reread = false;
      for (let step = 0; step <= N_MAX; step++) {
        let wall = -1;
        for (let i = 0; i < nw; i++) {
          const a = G.centre[i][0], b = G.centre[i][1];
          if (x * a + y * b >= cw) { wall = i; break; }
        }
        if (wall < 0) {
          let best = null, bj = -1;
          for (let j = 0; j < nw; j++) {
            const a = G.gap[j][0], b = G.gap[j][1];
            const d = x * a + y * b;
            if (best === null || d > best) { best = d; bj = j; }
          }
          if (k === 2 && bj === 2) { reread = true; break; }
          return { choice: bj, steps: step, rereads, x, y, undecided: false, path };
        }
        if (step === N_MAX) return { choice: 0, steps: step, rereads, x, y, undecided: true, path };
        const cx = G.C[wall][0], cy = G.C[wall][1];
        const dx = x - cx, dy = y - cy;
        const n2 = dx * dx + dy * dy;
        x = cx + r2 * dx / n2; y = cy + r2 * dy / n2;
        const nrm = Math.sqrt(x * x + y * y);
        x = x / nrm; y = y / nrm;
        path.push([x, y]);
      }
      if (!reread) break;
      rereads += 1;
      if (rereads > MAX_REREAD) return { choice: 0, steps: 0, rereads, x: path[path.length - 1][0], y: path[path.length - 1][1], undecided: true, path };
      u = (1000.0 * u + 0.618) % 1.0;
    }
  }

  // think@2: the region chosen from life counts and the logged u (hex)
  function think2(lifeCounts, uHex) {
    const lo = Math.min.apply(null, lifeCounts);
    const tied = [];
    lifeCounts.forEach((n, r) => { if (n === lo) tied.push(r); });
    if (tied.length === 1) return { region: tied[0], tied, d: null };
    const d = deliberate(tied.length, hexf(uHex));
    return { region: tied[d.choice], tied, d };
  }

  return { hexf, xiOf, deliberate, think2, K };
}

if (typeof module !== "undefined") module.exports = { makeDelib, hexf };
