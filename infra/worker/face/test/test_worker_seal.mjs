// The Seal's seat side (v0.7). Run: sed the cloudflare:workers import into a stub class (see face/README), then:
//   node --experimental-sqlite test_worker_seal.mjs FIXTURE.json OUT.json
// FIXTURE (from make_seal_fixture.py): a real lab v0.7 start blob and its journal up to day 0's seal moment, each
// record with its canonical text from seal_v07.canonical. OUT is checked by verify_seal_fixture.py with the anchored
// seal_v07 (signature, head, fraud).
import { DatabaseSync } from "node:sqlite";
import { readFileSync, writeFileSync } from "node:fs";
import { generateKeyPairSync } from "node:crypto";
const mod = await import("./do_new.mjs"); const { TeichSeat } = mod; const router = mod.default;
const fx = JSON.parse(readFileSync(process.argv[2], "utf8"));
const kp = generateKeyPairSync("ed25519"); const jw = kp.privateKey.export({ format: "jwk" });
const hex = (b64) => Buffer.from(b64, "base64url").toString("hex");
const SEED = hex(jw.d), PUB = hex(jw.x);
const other = generateKeyPairSync("ed25519").privateKey.export({ format: "jwk" });
let NOW = 0; const realNow = Date.now; Date.now = () => NOW;
const seats = {}; let alarmAt = {};
function seatFor(name, env) {
  if (!seats[name]) { const db = new DatabaseSync(":memory:");
    const sql = { exec(q, ...a) { const st = db.prepare(q); return /^\s*SELECT/i.test(q) ? st.all(...a) : (st.run(...a), []); } };
    seats[name] = new TeichSeat({ storage: { sql, setAlarm: async (t) => { alarmAt[name] = t; }, getAlarm: async () => alarmAt[name] ?? null } }, env); }
  return seats[name];
}
const envFor = (k) => ({ SEAT_KEY: "K", SEAL_KEY: k, TEICH_SEAT: { idFromName: (n) => n, get: (n) => ({ fetch: (r) => seatFor(n, envFor(k)).fetch(r) }) } });
const env = envFor(SEED);
const go = async (path, body, e = env) => { const r = await router.fetch(new Request("https://x" + path, body === undefined ? {} :
  { method: "POST", headers: { "X-Seat-Key": "K", "content-type": "application/json" }, body: JSON.stringify(body) }), e);
  return [r.status, await r.json().catch(() => null)]; };
const out = {}; const DAY = 86400, t0 = Number(fx.t0);
const sha = async (t) => Buffer.from(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t))).toString("hex");
NOW = (t0 + 3600) * 1000;

// ---- canonical text on an unsealed seat: stored verbatim, mismatches refused
await go("/o/teich-04/genesis-import", { state_blob: "S4", n_ticks: 0, genesis_anchor: "G4" });
const edge = { seq: 1, kind: "x", a: 100.0, b: 1e-06, c: "é", d: [0.1, 2.5e+16], e: { z: 1, y: null } };
const edgeCanon = '{"a":100.0,"b":1e-06,"c":"\\u00e9","d":[0.1,2.5e+16],"e":{"y":null,"z":1},"kind":"x","seq":1}';
out.canon_edge_accepted = (await go("/o/teich-04/log-append", { records: [edge], canon: [edgeCanon] }))[0] === 200;
let [, rd] = await go("/o/teich-04/log-read", { from_seq: 1 });
out.canon_stored_verbatim = rd.records[0].raw === edgeCanon;
out.canon_mismatch_refused = (await go("/o/teich-04/log-append", { records: [{ seq: 2, kind: "x", a: 1 }], canon: ['{"a":2,"kind":"x","seq":2}'] }))[0] === 400;
out.canon_length_refused = (await go("/o/teich-04/log-append", { records: [{ seq: 2, kind: "x" }], canon: [] }))[0] === 400;
out.unsealed_plain_append_ok = (await go("/o/teich-04/log-append", { records: [{ seq: 2, kind: "x" }] }))[0] === 200;
await seats["teich-04"].alarm();
out.unsealed_alarm_hourly = alarmAt["teich-04"] === NOW + 3600 * 1000;

// ---- teich-05: the start blob, the Seal, day 0's journal, its seal
await go("/o/teich-05/genesis-import", { state_blob: fx.start_blob, n_ticks: 0, genesis_anchor: "G5" });
const sb = await sha(fx.start_blob);
out.init_refuses_other_blob = (await go("/o/teich-05/seal-init", { start_blob_sha256: "0".repeat(64), start_seq: fx.start_seq, t0: fx.t0, pub: PUB }))[0] === 409;
out.init_refuses_other_pub = (await go("/o/teich-05/seal-init", { start_blob_sha256: sb, start_seq: fx.start_seq, t0: fx.t0, pub: hex(other.x) }))[0] === 409;
out.init_refuses_bad_t0 = (await go("/o/teich-05/seal-init", { start_blob_sha256: sb, start_seq: fx.start_seq, t0: "1780000000", pub: PUB }))[0] === 400;
seats["teich-05"].env = { ...seats["teich-05"].env, SEAL_KEY: undefined };               // a seat without SEAL_KEY
out.init_refuses_without_key = (await go("/o/teich-05/seal-init", { start_blob_sha256: sb, start_seq: fx.start_seq, t0: fx.t0, pub: PUB }))[0] === 409;
seats["teich-05"].env = { ...seats["teich-05"].env, SEAL_KEY: SEED };
let [s, d] = await go("/o/teich-05/seal-init", { start_blob_sha256: sb, start_seq: fx.start_seq, t0: fx.t0, pub: PUB });
out.init_ok = s === 200 && d.next_seal.day === 0 && d.next_seal.at_ms === (t0 + DAY - 900) * 1000;
out.init_once = (await go("/o/teich-05/seal-init", { start_blob_sha256: sb, start_seq: fx.start_seq, t0: fx.t0, pub: PUB }))[0] === 409;
out.sealed_needs_canon = (await go("/o/teich-05/log-append", { records: fx.day0.slice(0, 1).map((x) => x.rec) }))[0] === 400;
// the seat's order: lease, commit, then append the commit's records. Before its seal moment: nothing.
const L = (await go("/o/teich-05/lease", {}))[1];
await go("/o/teich-05/commit", { lease_id: L.lease_id, state_blob: fx.start_blob + " ", n_ticks: fx.n_at_seal });
const seal_at = (t0 + DAY - 900) * 1000;
NOW = seal_at - 60000; await seats["teich-05"].alarm();
out.no_seal_before_moment = (await go("/o/teich-05/seals-public"))[1].seals.length === 0 && alarmAt["teich-05"] === seal_at;
// at its moment the commit's records are not in the log yet: it waits (retry in 15 s)
NOW = seal_at + 1000; await seats["teich-05"].alarm();
out.waits_for_flush = (await go("/o/teich-05/seals-public"))[1].seals.length === 0 && alarmAt["teich-05"] === NOW + 15000;
NOW += 2000;
[s, d] = await go("/o/teich-05/log-append", { records: fx.day0.map((x) => x.rec), canon: fx.day0.map((x) => x.canon) });
out.day0_appended = s === 200 && d.appended === fx.day0.length;
// a lease opened by some body: it waits again
const L2 = (await go("/o/teich-05/lease", {}))[1];
NOW += 13000; await seats["teich-05"].alarm();
out.waits_for_open_lease = !!L2.lease_id && (await go("/o/teich-05/seals-public"))[1].seals.length === 0;
seats["teich-05"].sql.exec("UPDATE seat SET lease_ts=? WHERE id=1", NOW - 16 * 60 * 1000);   // that lease lapsed unused (TTL)
NOW += 15000; await seats["teich-05"].alarm();
const pub = (await go("/o/teich-05/seals-public"))[1];
out.sealed_day0 = pub.seals.length === 1 && pub.seals[0].day === 0 && pub.pub === PUB;
out.next_alarm_is_next_day = alarmAt["teich-05"] === Math.min(seats["teich-05"].sql.exec("SELECT v FROM settings WHERE k='hourly_next'")[0] ? JSON.parse(seats["teich-05"].sql.exec("SELECT v FROM settings WHERE k='hourly_next'")[0].v) : Infinity, (t0 + 2 * DAY - 900) * 1000);
// after the seal: a non-wake op landing before midnight is refused; the honest next op (a wake) is accepted
const n0 = fx.next[0].rec;
const forged = { ...n0, op: "present", owed: 100, inputs: { proposals: [], conversation: "x", organ: "o", door: [] } };  // lands at n+100: before midnight
const forgedCanon = JSON.stringify(Object.fromEntries(Object.entries(forged).sort()));
out.forged_lands_before_midnight = forged.n + forged.owed < DAY;
out.post_seal_backdate_refused = (await go("/o/teich-05/log-append", { records: [forged], canon: [forgedCanon] }))[0] === 409;
out.post_seal_wake_accepted = fx.next_op !== "wake" ||
  (await go("/o/teich-05/log-append", { records: fx.next.map((x) => x.rec), canon: fx.next.map((x) => x.canon) }))[0] === 200;
// a day that cannot be sealed in time is recorded as missed, never sealed late
NOW = (t0 + 2 * DAY - 900) * 1000 + 1000;
const L3 = (await go("/o/teich-05/lease", {}))[1];                 // a body holds the seat through day 1's moment
await seats["teich-05"].alarm();
NOW = (t0 + 2 * DAY - 120) * 1000 + 1; await seats["teich-05"].alarm();
const pub2 = (await go("/o/teich-05/seals-public"))[1];
out.missed_day_recorded = pub2.seals[0].day === 1 && pub2.seals[0].missed === true;
out.public_without_key = (await router.fetch(new Request("https://x/o/teich-05/seals-public"), env)).status === 200;
out.status_needs_key = (await router.fetch(new Request("https://x/o/teich-05/seal-status", { method: "POST", body: "{}" }), env)).status === 401;
out.refuse_seals_other_seat = (await router.fetch(new Request("https://x/o/teich-04/seals-public"), env)).status === 401;
const [, lg] = await go("/o/teich-05/log-read", { from_seq: 1, limit: 2000 });
writeFileSync(process.argv[3], JSON.stringify({ seal: pub.seals[0], log_raw: lg.records.map((r) => r.raw), pub: PUB, out }));
Date.now = realNow;
console.log(JSON.stringify(out), Object.values(out).every(Boolean) ? "ALL OK" : "FAILURES");
