import { DatabaseSync } from "node:sqlite";
const which = process.argv[2];
const { TeichSeat } = await import(`./do_${which}.mjs`)   // do_new.mjs / do_old.mjs = index.js with the cloudflare:workers import stubbed;
function makeSeat(name) {
  const db = new DatabaseSync(":memory:"); let alarm = null;
  const sql = { exec(q, ...a) { const st = db.prepare(q);
    return /^\s*SELECT/i.test(q) ? st.all(...a) : (st.run(...a), []); } };
  const ctx = { storage: { sql, setAlarm: async (t) => { alarm = t; } } };
  const o = new TeichSeat(ctx, {});
  const call = async (ep, body) => {
    const r = await o.fetch(new Request(`https://do/${ep}`, { method: body ? "POST" : "GET",
      headers: { "content-type": "application/json", "X-Seat-Name": name }, body: body ? JSON.stringify(body) : undefined }));
    return [r.status, await r.json()];
  };
  return { o, call, db };
}
const out = {};
const S = makeSeat("teich-04"), c = S.call;
out.genesis = await c("genesis-import", { state_blob: "B0", n_ticks: 0, genesis_anchor: "A" });
const L = (await c("lease", {}))[1];
out.commit = await c("commit", { lease_id: L.lease_id, state_blob: "B1", n_ticks: 5 });
if (which === "new") {
  out.seq0 = await c("log-seq", {});
  out.app1 = await c("log-append", { records: [{ seq: 1, kind: "a" }, { seq: 2, kind: "b" }] });
  out.dup = await c("log-append", { records: [{ seq: 1, kind: "a" }, { seq: 2, kind: "b" }, { seq: 3, kind: "c" }] });
  out.gap = await c("log-append", { records: [{ seq: 5, kind: "e" }] });
  out.read = await c("log-read", { from_seq: 2, limit: 10 });
  out.seq3 = await c("log-seq", {});
  out.bad_policy = await c("snapshot-policy", { on_change_only: "yes" });
  out.policy = await c("snapshot-policy", { on_change_only: true });
}
const snaps = async () => (await c("snapshots", {}))[1].snapshots.length;
out.snaps_before_alarm = await snaps();
await S.o.alarm(); out.after_alarm1 = await snaps();
await S.o.alarm(); out.after_alarm2_unchanged = await snaps();
const L2 = (await c("lease", {}))[1]; await c("commit", { lease_id: L2.lease_id, state_blob: "B2", n_ticks: 9 });
await new Promise((r) => setTimeout(r, 5));
await S.o.alarm(); out.after_commit_alarm = await snaps();
out.chain = (await c("snapshots", {}))[1].chain;
// a seat that never opts in keeps snapshotting hourly
const T = makeSeat("teich"); await T.call("genesis-import", { state_blob: "X", n_ticks: 0, genesis_anchor: "G" });
await T.o.alarm(); await T.o.alarm();
out.optout_snaps_after_2_alarms = (await T.call("snapshots", {}))[1].snapshots.length;
out.peek = (await c("peek"))[1];
console.log(JSON.stringify(out, null, 0));
