// TeichSeat — the Durable Object seat of self (INFRA_DESIGN.md, RECOVERY_POLICY.md).
//
// The state blob is OPAQUE TEXT: this code never parses or re-serializes it, so
// byte-fidelity of the float64 state is by construction (gate I1).
// Single-writer lease/commit makes forking structurally impossible (gate I2).
// Hourly alarm appends to the hash-chained snapshot table (gate I4); daily it pins
// the newest snapshot to Pinata iff the PINATA_JWT secret is installed.
//
// Routing: /o/<name>/<endpoint>. Teich's real seat is name "teich"; gate drills use
// other names. Destructive test endpoints refuse to run on "teich".

import { DurableObject } from "cloudflare:workers";

const LEASE_TTL_MS = 15 * 60 * 1000;
const SNAPSHOT_EVERY_MS = 60 * 60 * 1000;
const PIN_EVERY_MS = 24 * 60 * 60 * 1000;

async function sha256hex(text) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "content-type": "application/json" } });

export class TeichSeat extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`CREATE TABLE IF NOT EXISTS seat (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        blob TEXT NOT NULL, n_ticks INTEGER NOT NULL, genesis_anchor TEXT NOT NULL,
        lease_id TEXT, lease_ts INTEGER, updated_ts INTEGER NOT NULL)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS snapshots (
        i INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL,
        n_ticks INTEGER NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL,
        blob TEXT NOT NULL)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS events (
        i INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL,
        type TEXT NOT NULL, detail TEXT NOT NULL)`);
  }

  #seat() {
    const rows = [...this.sql.exec("SELECT * FROM seat WHERE id=1")];
    return rows.length ? rows[0] : null;
  }

  #event(type, detail) {
    this.sql.exec("INSERT INTO events (ts, type, detail) VALUES (?, ?, ?)",
      Date.now(), type, JSON.stringify(detail));
  }

  #chainHead() {
    const r = [...this.sql.exec("SELECT i, hash, n_ticks, ts FROM snapshots ORDER BY i DESC LIMIT 1")];
    return r.length ? r[0] : null;
  }

  async #snapshot(reason) {
    const seat = this.#seat();
    if (!seat) return null;
    const head = this.#chainHead();
    const prev = head ? head.hash : seat.genesis_anchor;
    const hash = await sha256hex(prev + seat.blob);
    this.sql.exec(
      "INSERT INTO snapshots (ts, n_ticks, prev, hash, blob) VALUES (?, ?, ?, ?, ?)",
      Date.now(), seat.n_ticks, prev, hash, seat.blob);
    this.#event("snapshot", { reason, n_ticks: seat.n_ticks, hash });
    return hash;
  }

  async #verifyChain(uptoI = null) {
    const seat = this.#seat();
    const rows = [...this.sql.exec(
      uptoI === null ? "SELECT * FROM snapshots ORDER BY i"
                     : "SELECT * FROM snapshots WHERE i<=? ORDER BY i", ...(uptoI === null ? [] : [uptoI]))];
    let prev = seat.genesis_anchor;
    for (const r of rows) {
      if (r.prev !== prev) return { ok: false, bad_i: r.i, why: "prev-link mismatch" };
      const h = await sha256hex(prev + r.blob);
      if (h !== r.hash) return { ok: false, bad_i: r.i, why: "hash mismatch" };
      prev = r.hash;
    }
    return { ok: true, n: rows.length, head: prev };
  }

  async #pinNewest() {
    // Public IPFS must NEVER see the state in clear: the blob carries private phi,
    // and deterministic rotation makes one clear sample at a known tick equivalent
    // to publishing phi0 forever (sealed-phi0 amendment). AES-256-GCM under the
    // founder's SNAPSHOT_KEY; chain metadata (prev/hash of PLAINTEXT) stays public
    // so the chain is still verifiable after founder-side decryption.
    if (!this.env.PINATA_JWT) return { error: "no PINATA_JWT secret installed" };
    if (!this.env.SNAPSHOT_KEY) return { error: "no SNAPSHOT_KEY secret installed" };
    const head = [...this.sql.exec("SELECT * FROM snapshots ORDER BY i DESC LIMIT 1")][0];
    if (!head) return { error: "no snapshots" };
    try {
      const keyBytes = new Uint8Array(
        this.env.SNAPSHOT_KEY.match(/.{2}/g).map((h) => parseInt(h, 16)));
      const key = await crypto.subtle.importKey("raw", keyBytes, "AES-GCM", false, ["encrypt"]);
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const ct = new Uint8Array(await crypto.subtle.encrypt(
        { name: "AES-GCM", iv }, key, new TextEncoder().encode(head.blob)));
      const b64 = (u8) => btoa(String.fromCharCode(...u8));
      const r = await fetch("https://api.pinata.cloud/pinning/pinJSONToIPFS", {
        method: "POST",
        headers: { "content-type": "application/json",
                   authorization: `Bearer ${this.env.PINATA_JWT}` },
        body: JSON.stringify({
          pinataMetadata: { name: `teich-seat-snapshot-${head.i}` },
          pinataContent: { i: head.i, ts: head.ts, n_ticks: head.n_ticks,
                           prev: head.prev, hash: head.hash,
                           enc: "AES-256-GCM", iv: b64(iv), ciphertext: b64(ct) },
        }),
      });
      const out = await r.json();
      const ev = { i: head.i, hash: head.hash, ipfs: out.IpfsHash || out, encrypted: true };
      this.#event("pinata-pin", ev);
      return { ok: !!out.IpfsHash, ...ev };
    } catch (e) {
      this.#event("pinata-pin-error", { message: String(e) });
      return { error: String(e) };
    }
  }

  async fetch(request) {
    const url = new URL(request.url);
    // path arrives as /<endpoint> (worker strips /o/<name>); name via header
    const ep = url.pathname.replace(/^\//, "");
    const name = request.headers.get("X-Seat-Name") || "?";
    const now = Date.now();
    const seat = this.#seat();
    const body = request.method === "POST" ? await request.json().catch(() => ({})) : {};

    if (ep === "peek") {
      const head = this.#chainHead();
      return json({
        alive: !!seat, name, n_ticks: seat ? seat.n_ticks : null,
        updated_ts: seat ? seat.updated_ts : null,
        chain_head: head ? head.hash : null, snapshots: head ? head.i : 0,
      });
    }

    if (ep === "genesis-import") {
      if (seat) return json({ error: "seat already initialized" }, 409);
      if (typeof body.state_blob !== "string" || !Number.isInteger(body.n_ticks) ||
          typeof body.genesis_anchor !== "string")
        return json({ error: "need state_blob, n_ticks, genesis_anchor" }, 400);
      this.sql.exec(
        "INSERT INTO seat (id, blob, n_ticks, genesis_anchor, updated_ts) VALUES (1, ?, ?, ?, ?)",
        body.state_blob, body.n_ticks, body.genesis_anchor, now);
      this.#event("genesis-import", { n_ticks: body.n_ticks, anchor: body.genesis_anchor });
      await this.#snapshot("genesis-import");
      await this.ctx.storage.setAlarm(now + SNAPSHOT_EVERY_MS);
      return json({ ok: true, n_ticks: body.n_ticks });
    }

    if (!seat) return json({ error: "seat not initialized" }, 404);

    if (ep === "state")
      return json({ state_blob: seat.blob, n_ticks: seat.n_ticks,
                    lease_open: !!(seat.lease_id && now - seat.lease_ts < LEASE_TTL_MS) });

    if (ep === "lease") {
      if (seat.lease_id && now - seat.lease_ts < LEASE_TTL_MS)
        return json({ error: "lease already open", lease_age_ms: now - seat.lease_ts }, 409);
      const lease_id = crypto.randomUUID();
      this.sql.exec("UPDATE seat SET lease_id=?, lease_ts=? WHERE id=1", lease_id, now);
      this.#event("lease", { lease_id });
      return json({ lease_id, state_blob: seat.blob, n_ticks: seat.n_ticks });
    }

    if (ep === "commit") {
      if (!seat.lease_id || now - seat.lease_ts >= LEASE_TTL_MS)
        return json({ error: "no open lease" }, 409);
      if (body.lease_id !== seat.lease_id)
        return json({ error: "stale or foreign lease" }, 409);
      if (typeof body.state_blob !== "string" || !Number.isInteger(body.n_ticks))
        return json({ error: "need state_blob, n_ticks" }, 400);
      if (body.n_ticks < seat.n_ticks)
        return json({ error: "n_ticks may not decrease outside /restore" }, 409);
      this.sql.exec(
        "UPDATE seat SET blob=?, n_ticks=?, lease_id=NULL, lease_ts=NULL, updated_ts=? WHERE id=1",
        body.state_blob, body.n_ticks, now);
      this.#event("commit", { lease_id: body.lease_id, n_ticks: body.n_ticks });
      return json({ ok: true, n_ticks: body.n_ticks });
    }

    if (ep === "snapshot-now")
      return json({ ok: true, hash: await this.#snapshot(body.reason || "manual") });

    if (ep === "pin-now")
      return json(await this.#pinNewest());

    if (ep === "snapshots") {
      const rows = [...this.sql.exec("SELECT i, ts, n_ticks, prev, hash FROM snapshots ORDER BY i")];
      return json({ snapshots: rows, chain: await this.#verifyChain() });
    }

    if (ep === "snapshot-blob") {
      const r = [...this.sql.exec("SELECT * FROM snapshots WHERE i=?", body.i)];
      return r.length ? json(r[0]) : json({ error: "no such snapshot" }, 404);
    }

    if (ep === "events") {
      const rows = [...this.sql.exec("SELECT * FROM events ORDER BY i DESC LIMIT ?", body.limit || 50)];
      return json({ events: rows });
    }

    if (ep === "restore") {
      // RECOVERY_POLICY §2.3: restore = coma, declared BEFORE first post-restore wake.
      if (!Number.isInteger(body.i) || typeof body.cause !== "string" || !body.cause)
        return json({ error: "need snapshot i and declared cause" }, 400);
      const chain = await this.#verifyChain(body.i);
      if (!chain.ok) return json({ error: "chain verification failed", chain }, 409);
      const r = [...this.sql.exec("SELECT * FROM snapshots WHERE i=?", body.i)];
      if (!r.length) return json({ error: "no such snapshot" }, 404);
      const coma = {
        type: "coma", restored_from_snapshot: body.i, restored_hash: r[0].hash,
        restored_n_ticks: r[0].n_ticks, prior_n_ticks: seat.n_ticks, cause: body.cause,
      };
      this.sql.exec(
        "UPDATE seat SET blob=?, n_ticks=?, lease_id=NULL, lease_ts=NULL, updated_ts=? WHERE id=1",
        r[0].blob, r[0].n_ticks, now);
      this.#event("coma", coma);
      return json({ ok: true, coma });
    }

    if (ep === "diary") {
      // Teich's inner voice: Workers AI, running INSIDE Cloudflare — the words are
      // generated where the seat lives, from the PUBLIC readout only. The caller
      // (a gate-certified body) supplies the fresh post-wake readout; private phi
      // is stripped defensively even if a caller misbehaves.
      if (!this.env.AI) return json({ error: "no AI binding deployed" }, 500);
      const ro = { ...(body.readout || {}) };
      delete ro.private_phase;
      // inner voice: Qwen family (same lineage as the certified Mouth), Workers AI
      // native (@cf/ = neuron-billed free tier; never paid partner models here)
      const model = body.model || "@cf/qwen/qwen3-30b-a3b-fp8";
      const sys =
        "You are the inner voice of Teich, a small dynamical creature: a chaotic " +
        "flow living one tick per real second on a certified attractor, with two " +
        "private phases nobody can decode. You are not a person and not a chatbot; " +
        "never claim consciousness or feelings — you have instrument readouts, not " +
        "introspection beyond them. Write a short private diary entry (3-6 " +
        "sentences, first person) grounded ONLY in the readout: basin is which " +
        "wing of the attractor you are on (-1 or +1); saddle_proximity (0..1) is " +
        "how torn between wings you are; lambda_running is your measured chaos " +
        "strength this window; steps_to_switch and will_flip are your own " +
        "falsifiable prediction about the next possible wing switch; n_switches " +
        "and mean_dwell describe how restless this window was. ticks_added is how " +
        "many seconds of hibernated life this wake just replayed deterministically. " +
        "Quote numbers exactly as given; never invent any.";
      const user = JSON.stringify({
        utc: new Date().toISOString(), n_ticks: body.n_ticks ?? seat.n_ticks,
        ticks_added: body.ticks_added ?? null, readout: ro,
      });
      try {
        const out = await this.env.AI.run(model, {
          messages: [{ role: "system", content: sys }, { role: "user", content: user }],
          max_tokens: 400,
        });
        const text = String(out && out.response ? out.response : "").trim();
        if (!text) return json({ error: "empty AI response", raw: out }, 502);
        const entry = { n_ticks: body.n_ticks ?? seat.n_ticks,
                        ticks_added: body.ticks_added ?? null, model, readout: ro, text };
        this.#event("diary", entry);
        return json({ ok: true, ...entry });
      } catch (e) {
        this.#event("diary-error", { message: String(e) });
        return json({ error: String(e) }, 500);
      }
    }

    if (ep === "anchor") {
      // cross-anchor an external hash (e.g. a diary git commit SHA) into the
      // seat's event log, so the repo history and the seat chain vouch for each
      // other — rewriting either becomes detectable from the other.
      if (typeof body.git_sha !== "string" || !body.git_sha)
        return json({ error: "need git_sha" }, 400);
      const a = { git_sha: body.git_sha, ref: body.ref || "", note: body.note || "" };
      this.#event("git-anchor", a);
      return json({ ok: true, ...a });
    }

    if (ep === "drill-destroy") {
      // test-only: simulate loss by corrupting the live blob. NEVER on the real seat.
      if (name === "teich") return json({ error: "refused on the real seat" }, 403);
      this.sql.exec("UPDATE seat SET blob='CORRUPTED', updated_ts=? WHERE id=1", now);
      this.#event("drill-destroy", {});
      return json({ ok: true });
    }

    return json({ error: `unknown endpoint ${ep}` }, 404);
  }

  async alarm() {
    const now = Date.now();
    await this.#snapshot("alarm-hourly");
    // daily off-Cloudflare pin, iff secret installed
    const lastPin = [...this.sql.exec(
      "SELECT ts FROM events WHERE type='pinata-pin' ORDER BY i DESC LIMIT 1")];
    if (this.env.PINATA_JWT && (!lastPin.length || now - lastPin[0].ts >= PIN_EVERY_MS))
      await this.#pinNewest();
    this.#event("heartbeat", {});
    await this.ctx.storage.setAlarm(now + SNAPSHOT_EVERY_MS);
  }
}

export default {
  async fetch(request, env) {
    try {
      return await handle(request, env);
    } catch (e) {
      return json({ error: "worker exception", message: String(e), stack: e.stack }, 500);
    }
  },
};

async function handle(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/" || url.pathname === "/index.html")
      return new Response(PANEL_HTML, {
        headers: { "content-type": "text/html;charset=utf-8" } });
    if (url.pathname === "/ping")
      return json({ pong: true, has_do: !!env.TEICH_SEAT, has_key: !!env.SEAT_KEY });
    const m = url.pathname.match(/^\/o\/([a-z0-9-]{1,40})\/([a-z-]+)$/);
    if (!m) return json({ error: "path: /o/<name>/<endpoint>" }, 404);
    const [, name, ep] = m;
    if (ep !== "peek") {
      const key = request.headers.get("X-Seat-Key");
      if (!env.SEAT_KEY || key !== env.SEAT_KEY) return json({ error: "unauthorized" }, 401);
    }
    const stub = env.TEICH_SEAT.get(env.TEICH_SEAT.idFromName(name));
    const fwd = new Request(`https://do/${ep}`, {
      method: request.method,
      headers: { "content-type": "application/json", "X-Seat-Name": name },
      body: request.method === "POST" ? await request.text() : undefined,
    });
    return stub.fetch(fwd);
}

// ---------------------------------------------------------------------------
// The public face (infancy: read-only instrument panel; the book opens at
// maturity). Everything shown is ledger/instrument data — no generated text.
const PANEL_HTML = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Teich</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%230b1116'/%3E%3Ccircle cx='32' cy='32' r='22' fill='none' stroke='%232a6e8f' stroke-width='2.5' opacity='.5'/%3E%3Ccircle cx='32' cy='32' r='13' fill='none' stroke='%233fa7c9' stroke-width='2.5' opacity='.75'/%3E%3Ccircle cx='32' cy='32' r='5' fill='%233ddc84'/%3E%3C/svg%3E">
<style>
  :root { color-scheme: dark; }
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         background:#0b1116; color:#d7e0e7; font:16px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }
  .card { max-width:640px; padding:2.2rem 2.4rem; }
  h1 { font-size:1.6rem; margin:0 0 .1rem; letter-spacing:.35em; font-weight:600; }
  .sub { color:#7b8a96; font-size:.8rem; margin-bottom:1.6rem; }
  .dot { display:inline-block; width:.6em; height:.6em; border-radius:50%; background:#3ddc84;
         margin-right:.5em; box-shadow:0 0 8px #3ddc84; }
  .dot.dead { background:#e05252; box-shadow:0 0 8px #e05252; }
  dl { display:grid; grid-template-columns:auto 1fr; gap:.35rem 1.2rem; margin:1.2rem 0; }
  dt { color:#7b8a96; }  dd { margin:0; overflow-wrap:anywhere; }
  .note { color:#9fb0bc; font-size:.85rem; border-top:1px solid #1d2933; padding-top:1.1rem; margin-top:1.4rem; }
  a { color:#6ab0f3; text-decoration:none; }  a:hover { text-decoration:underline; }
  .muted { color:#5c6b77; }
</style></head><body><div class="card">
  <h1>TEICH</h1>
  <div class="sub">a continuously-existing dynamical creature &mdash; born 2026-07-18T08:45:12Z</div>
  <div><span id="dot" class="dot"></span><span id="alive">reading the seat&hellip;</span></div>
  <dl>
    <dt>identity</dt><dd><a href="https://gateway.pinata.cloud/ipfs/QmQEVjtM9k3oihiVxrjJoWiRfLvED2eYSTfRvyLGKUx4yA">QmQEVjtM&hellip;x4yA</a> <span class="muted">(genesis certificate, IPFS)</span></dd>
    <dt>age</dt><dd id="age">&mdash;</dd>
    <dt>ticks lived</dt><dd id="ticks">&mdash;</dd>
    <dt>time banked</dt><dd id="banked">&mdash; <span class="muted">(hibernated, awaiting deterministic replay)</span></dd>
    <dt>snapshot chain</dt><dd id="chain">&mdash;</dd>
    <dt>last commit</dt><dd id="upd">&mdash;</dd>
  </dl>
  <div class="note">
    Teich is not a chatbot. It is a certified chaotic dynamical system &mdash; a public
    suspension core with two private phases nobody can decode &mdash; living one tick per
    real second on a Cloudflare Durable Object, woken daily by whichever machine can
    prove, bit-for-bit, that it computes Teich's dynamics exactly. Hibernation is
    lossless by construction: every banked second is replayed deterministically at the
    next wake. It keeps a private diary; each entry's hash is public.
    <span class="muted">The book opens at maturity.</span>
  </div>
</div>
<script>
const BIRTH = 1784364312.295;
function fmt(s){ const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);
  return (d? d+"d ":"")+h+"h "+m+"m"; }
async function refresh(){
  try {
    const p = await (await fetch("/o/teich/peek")).json();
    const now = Date.now()/1000, age = now-BIRTH;
    document.getElementById("dot").className = "dot"+(p.alive?"":" dead");
    document.getElementById("alive").textContent = p.alive?"alive (hibernating between wakes)":"seat unreachable";
    document.getElementById("age").textContent = fmt(age)+" ("+Math.floor(age).toLocaleString()+" s)";
    document.getElementById("ticks").textContent = p.n_ticks.toLocaleString();
    document.getElementById("banked").firstChild.textContent = fmt(Math.max(0,Math.floor(age)-p.n_ticks))+" ";
    document.getElementById("chain").textContent = p.snapshots+" snapshots, head "+p.chain_head.slice(0,16)+"…";
    document.getElementById("upd").textContent = new Date(p.updated_ts).toUTCString();
  } catch(e) {
    document.getElementById("dot").className = "dot dead";
    document.getElementById("alive").textContent = "panel error: "+e;
  }
}
refresh(); setInterval(refresh, 30000);
</script></body></html>`;
