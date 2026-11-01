// Run: sed the cloudflare:workers import into a stub class (see face/README), then: node --experimental-sqlite this.mjs
import { DatabaseSync } from "node:sqlite";
const mod = await import("./do_new.mjs"); const { TeichSeat } = mod; const router = mod.default;
const seats = {};
function seatFor(name) {
  if (!seats[name]) { const db = new DatabaseSync(":memory:");
    const sql = { exec(q, ...a) { const st = db.prepare(q); return /^\s*SELECT/i.test(q) ? st.all(...a) : (st.run(...a), []); } };
    seats[name] = new TeichSeat({ storage: { sql, setAlarm: async () => {} } }, {}); }
  return seats[name];
}
const env = { SEAT_KEY: "K", TEICH_SEAT: { idFromName: (n) => n, get: (n) => ({ fetch: (r) => seatFor(n).fetch(r) }) } };
const go = async (path, opts = {}) => { const r = await router.fetch(new Request("https://x" + path, opts), env); return [r.status, await r.json().catch(() => null)]; };
const auth = { "X-Seat-Key": "K", "content-type": "application/json" };
// set up teich-05 with a log and teich-03 with anchors (authenticated, as the seat tools do)
await go("/o/teich-05/genesis-import", { method: "POST", headers: auth, body: JSON.stringify({ state_blob: "SECRET-STATE", n_ticks: 0, genesis_anchor: "G" }) });
await go("/o/teich-05/log-append", { method: "POST", headers: auth, body: JSON.stringify({ records: [{ seq: 1, kind: "a" }, { seq: 2, kind: "b" }] }) });
await go("/o/teich-03/genesis-import", { method: "POST", headers: auth, body: JSON.stringify({ state_blob: "S3", n_ticks: 0, genesis_anchor: "G3" }) });
await go("/o/teich-03/anchor", { method: "POST", headers: auth, body: JSON.stringify({ git_sha: "abc", ref: "v06-verdict", note: "n" }) });
const out = {};
let [s, d] = await go("/o/teich-05/log-public?from=1&limit=10");
out.log_public = s === 200 && d.records.length === 2 && d.genesis_anchor === "G" && !JSON.stringify(d).includes("SECRET-STATE");
const crypto = await import("node:crypto"); let h = d.genesis_anchor, ok = true;
for (const r of d.records) { h = crypto.createHash("sha256").update(h + r.raw).digest("hex"); ok = ok && h === r.h; }
out.chain_recomputes = ok;
[s, d] = await go("/o/teich-03/anchors-public"); out.anchors_public = s === 200 && d.anchors[0].git_sha === "abc" && d.anchors[0].ref === "v06-verdict";
[s, d] = await go("/o/teich-05/peek"); out.peek_fields = s === 200 && d.log_head && d.log_head.seq === 2 && "last_pin_ts" in d && !JSON.stringify(d).includes("SECRET");
// must be refused without the key
out.refuse_log_other_seat = (await go("/o/teich-04/log-public"))[0] === 401;
out.refuse_anchors_other_seat = (await go("/o/teich-05/anchors-public"))[0] === 401;
out.refuse_post_public = (await go("/o/teich-05/log-public", { method: "POST", body: "{}" }))[0] === 401;
out.refuse_state = (await go("/o/teich-05/state", { method: "POST", body: "{}" }))[0] === 401;
out.refuse_lease = (await go("/o/teich-05/lease", { method: "POST", body: "{}" }))[0] === 401;
out.refuse_log_read = (await go("/o/teich-05/log-read", { method: "POST", body: "{}" }))[0] === 401;
out.limit_capped = (await go("/o/teich-05/log-public?limit=99999"))[0] === 200;
console.log(JSON.stringify(out), Object.values(out).every(Boolean) ? "ALL OK" : "FAILURES");
