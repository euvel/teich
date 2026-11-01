// Run: sed the cloudflare:workers import into a stub class (see face/README), then: node --experimental-sqlite this.mjs
import { DatabaseSync } from "node:sqlite";
const { TeichSeat } = await import("./do_new.mjs");
const db = new DatabaseSync(":memory:");
const sql = { exec(q, ...a) { const st = db.prepare(q); return /^\s*SELECT/i.test(q) ? st.all(...a) : (st.run(...a), []); } };
const env = { PINATA_JWT: "x", SNAPSHOT_KEY: "11".repeat(32) };
const o = new TeichSeat({ storage: { sql, setAlarm: async () => {} } }, env);
const call = async (ep, body, name = "teich-05") => (await o.fetch(new Request(`https://do/${ep}`, { method: body ? "POST" : "GET",
  headers: { "content-type": "application/json", "X-Seat-Name": name }, body: body ? JSON.stringify(body) : undefined }))).json();
// fake Pinata
let mode = "ok", pinned = [], unpinned = [];
const day = (d) => `2026-10-${String(d).padStart(2, "0")}T00:00:00.000Z`;
const rows = [];
for (let d = 1; d <= 35; d++) rows.push({ ipfs_pin_hash: `Qs${d}`, date_pinned: day(d % 31 + 1).replace("10-", d > 30 ? "11-" : "10-"), metadata: { keyvalues: { seat: "teich-05" } } });
rows.push({ ipfs_pin_hash: "QOTHER", date_pinned: day(1), metadata: { keyvalues: { seat: "teich-03" } } });
rows.push({ ipfs_pin_hash: "QARCHIVE", date_pinned: day(1), metadata: { name: "teich-seat-snapshot-1", keyvalues: null } });
globalThis.fetch = async (url, init = {}) => {
  const J = (x, s = 200) => new Response(JSON.stringify(x), { status: s });
  if (url.includes("pinJSONToIPFS")) {
    const b = JSON.parse(init.body); pinned.push(b.pinataMetadata);
    return mode === "ok" ? J({ IpfsHash: "QNEW" }) : J({ error: { reason: "FORBIDDEN", details: "Account blocked due to plan usage limit" } }, 403);
  }
  if (url.includes("pinList")) return J({ rows: rows.filter((r) => !unpinned.includes(r.ipfs_pin_hash)) });
  if (url.includes("/unpin/")) { unpinned.push(url.split("/").pop()); return new Response("OK"); }
  throw new Error("unexpected " + url);
};
await call("genesis-import", { state_blob: "B0", n_ticks: 0, genesis_anchor: "A" });
const r1 = await call("pin-now", {});
const sorted = rows.filter((r) => r.metadata.keyvalues && r.metadata.keyvalues.seat === "teich-05").sort((a, b) => (a.date_pinned < b.date_pinned ? 1 : -1));
const expect = sorted.slice(30).map((r) => r.ipfs_pin_hash).sort();
console.log("label", JSON.stringify(pinned[0]));
console.log("rotation unpinned", unpinned.slice().sort().join(","), "== oldest 5:", JSON.stringify(unpinned.slice().sort()) === JSON.stringify(expect));
console.log("other seat / archive untouched:", !unpinned.includes("QOTHER") && !unpinned.includes("QARCHIVE"));
mode = "refuse"; const before = unpinned.length;
const r2 = await call("pin-now", {});
const ev = [...db.prepare("SELECT type FROM events ORDER BY i DESC LIMIT 2").all()].map((e) => e.type);
console.log("refusal ->", r2.error, "| last events", ev.join(","), "| no rotation:", unpinned.length === before);
const n3 = await call("peek", null, "teich-05"); console.log("peek still fine:", n3.alive);
