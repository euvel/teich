// The public face. Everything shown is read from its seats, its public record log, its diary or its anchored book;
// nothing is generated. Failures are shown as failures, never as stale data.
document.documentElement.classList.remove("no-js");
const $ = (id) => document.getElementById(id);
const DELIB = makeDelib(DELIB_CONSTANTS);
const LOCAL = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
const DEMO = LOCAL && new URLSearchParams(location.search).has("demo");
if (DEMO) document.body.classList.add("demo");
const RAW = "https://raw.githubusercontent.com/euvel/teich/main/";
const LOG_URL = DEMO ? "/demo/records.jsonl" : RAW + "v05/diary/records.jsonl";
const SEATS = ["teich-05", "teich-04", "teich-03", "teich-02", "teich"];
const BIRTH5 = Date.UTC(2026, 9, 23, 14, 30, 50) / 1000;        // its birth as v0.5; its ticks count from here
const BIRTH1 = 1784364312.295;                                  // v0.1's birth (its own panel)
const REGION = ["food & drink", "body & matter", "living things", "objects & places", "people & feeling",
                "mind & society", "arts & events", "work & things made", "itself"];
const NS = "http://www.w3.org/2000/svg";
const peeks = {};
let RECS = null, NIGHTS = [];

function svg(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function text(el, s) { if (el) el.textContent = s; }
async function sha256hex(data) {
  const buf = typeof data === "string" ? new TextEncoder().encode(data) : data;
  const h = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
}
function ago(ms) {
  const s = Math.max(0, (Date.now() - ms) / 1000);
  if (s < 90) return Math.round(s) + " s ago";
  if (s < 5400) return Math.round(s / 60) + " min ago";
  if (s < 172800) return Math.round(s / 3600) + " h ago";
  return Math.round(s / 86400) + " days ago";
}
function dhm(s) { const d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60);
  return (d ? d + "d " : "") + h + "h " + m + "m"; }

// ---------------------------------------------------------------- seats
const LEGACY = { "teich-04": "4", "teich-03": "3", "teich-02": "2" };
async function readSeat(name) {
  try {
    const p = await (await fetch("/o/" + name + "/peek", { cache: "no-store" })).json();
    peeks[name] = p;
    const on = !!p.alive;
    $("sd-" + name).className = "dot " + (on ? "on" : "off");
    const fd = $("fd-" + name); if (fd) fd.className = "dot " + (on ? "on" : "off");
    text($("ft-" + name), on ? p.n_ticks.toLocaleString() + " ticks" : "seat unreachable");
    const sfx = LEGACY[name];
    if (sfx !== undefined) {
      if ($("dot" + sfx)) $("dot" + sfx).className = "dot" + (on ? "" : " dead");
      text($("alive" + sfx), on ? "alive (hibernating between wakes)" : "seat unreachable");
      text($("ticks" + sfx), p.n_ticks.toLocaleString());
      text($("chain" + sfx), p.snapshots + " snapshots, head " + p.chain_head.slice(0, 16) + "…");
      text($("upd" + sfx), new Date(p.updated_ts).toUTCString());
    }
    if (name === "teich") {
      const age = Date.now() / 1000 - BIRTH1;
      if ($("dot")) $("dot").className = "dot" + (on ? "" : " dead");
      text($("alive"), on ? "alive (hibernating between wakes)" : "seat unreachable");
      text($("age"), dhm(age) + " (" + Math.floor(age).toLocaleString() + " s)");
      text($("ticks"), p.n_ticks.toLocaleString());
      if ($("banked")) $("banked").firstChild.textContent = dhm(Math.max(0, Math.floor(age) - p.n_ticks)) + " ";
      text($("chain"), p.snapshots + " snapshots, head " + p.chain_head.slice(0, 16) + "…");
      text($("upd"), new Date(p.updated_ts).toUTCString());
    }
    if (name === "teich-05") {
      text($("seat5"), on ? "alive, hibernating between wakes · " + p.snapshots + " snapshots · last commit " + ago(p.updated_ts)
                          : "seat unreachable");
      text($("c-lived"), p.n_ticks.toLocaleString());
      text($("st-wake"), "last wake " + ago(p.updated_ts));
    }
  } catch (e) {
    $("sd-" + name).className = "dot off";
    text($("ft-" + name), "seat unreachable");
    if (name === "teich-05") text($("seat5"), "seat unreachable: " + e.message);
  }
}
async function readSeats() {
  await Promise.all(SEATS.map(readSeat));
  const up = SEATS.filter((n) => peeks[n] && peeks[n].alive).length;
  text($("sd-text"), up + " of 5 seats alive");
  const pins = SEATS.filter((n) => peeks[n] && peeks[n].last_pin_ts).map((n) => n + " " + ago(peeks[n].last_pin_ts));
  text($("pins"), pins.length ? "off-site encrypted backups (IPFS), last pinned: " + pins.join(" · ") : "off-site backups: status not published by this seat version");
}
function tickOwed() {
  const p = peeks["teich-05"];
  if (!p || !p.alive) return;
  const owed = Math.max(0, Math.floor(Date.now() / 1000 - BIRTH5 - p.n_ticks));
  text($("c-owed"), owed.toLocaleString());
}
function nextWake() {
  const now = new Date(), t = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 6, 11));
  if (t <= now) t.setUTCDate(t.getUTCDate() + 1);
  text($("st-next"), "next wake 06:11 UTC, in " + dhm((t - now) / 1000));
  $("st-next").title = "scheduled daily at 06:11 UTC; GitHub often starts it hours late";
}

// ---------------------------------------------------------------- its record log
async function readLog() {
  try {
    const t = await (await fetch(LOG_URL, { cache: "no-store" })).text();
    RECS = t.split(String.fromCharCode(10)).filter(Boolean).map((l) => JSON.parse(l));
  } catch (e) {
    RECS = null;
    text($("ringtip"), "its record log is unreachable right now (" + e.message + "); nothing is shown rather than old data.");
    return;
  }
  const reasons = {};
  RECS.forEach((r) => { if (r.kind === "reason" && r.rule === "think@2") reasons[r.act_id] = r; });
  NIGHTS = RECS.filter((r) => r.kind === "act" && r.deliberation && reasons[r.act_id]).map((a) => {
    const rs = reasons[a.act_id];
    return { night: a.night, seq: a.seq, tied: a.deliberation.tied, act: a.act, steps: a.deliberation.steps,
             uHex: rs.inputs.u, u: DELIB.hexf(rs.inputs.u), lc: rs.inputs.life_counts, old: a.deliberation.tied[0] };
  });
  const diff = NIGHTS.filter((n) => n.act !== n.old).length;
  text($("c-ties"), NIGHTS.length.toLocaleString());
  text($("c-diff"), NIGHTS.length ? diff.toLocaleString() : "—");
  drawRings(); tonight(); duduk(); explainer.reset();
}

// ---------------------------------------------------------------- the rings
function arc(r, a0, a1) {
  const p = (a) => [r * Math.cos(a), r * Math.sin(a)];
  const s = p(a0), e = p(a1), big = a1 - a0 > Math.PI ? 1 : 0;
  return "M " + s[0].toFixed(3) + " " + s[1].toFixed(3) + " A " + r + " " + r + " 0 " + big + " 1 " + e[0].toFixed(3) + " " + e[1].toFixed(3);
}
function drawRings() {
  const g = $("rings");
  while (g.lastChild && g.lastChild.tagName !== "title") g.removeChild(g.lastChild);
  svg("circle", { r: 104, fill: "none", stroke: "#1b2630", "stroke-width": 0.6 }, g);
  svg("circle", { r: 14, fill: "none", stroke: "#24323e", "stroke-width": 0.6 }, g);
  $("rings-empty").style.display = NIGHTS.length ? "none" : "flex";
  if (!NIGHTS.length) {
    for (let i = 0; i < 9; i++) {
      const a0 = 2 * Math.PI * i / 9 - Math.PI / 2 + 0.02, a1 = 2 * Math.PI * (i + 1) / 9 - Math.PI / 2 - 0.02;
      svg("path", { d: arc(98, a0, a1), fill: "none", stroke: "#1b2630", "stroke-width": 3 }, g);
    }
    return;
  }
  const n = NIGHTS.length, inner = 20, outer = 100, w = Math.min(6, (outer - inner) / n), gap = Math.min(1.2, w * 0.25);
  NIGHTS.forEach((N, i) => {
    const r = inner + (i + 0.5) * w, k = N.tied.length, differs = N.act !== N.old;
    const ring = svg("g", { tabindex: 0, role: "button", "aria-label": "night " + N.night + ": " + k + " regions tied, it chose " + REGION[N.act] }, g);
    if (differs) svg("circle", { r: r, fill: "none", stroke: "#3fa7c9", "stroke-width": w * 1.25, opacity: 0.1 }, ring);
    for (let j = 0; j < k; j++) {
      const a0 = 2 * Math.PI * j / k - Math.PI / 2 + 0.015, a1 = 2 * Math.PI * (j + 1) / k - Math.PI / 2 - 0.015;
      const won = N.tied[j] === N.act;
      svg("path", { class: "ring-seg", d: arc(r, a0, a1), fill: "none", "stroke-width": Math.max(0.6, w - gap),
        stroke: won ? "#3ddc84" : (differs ? "#2a6e8f" : "#1f3a48"), opacity: won ? 0.95 : 0.6 }, ring);
    }
    const au = 2 * Math.PI * N.u - Math.PI / 2;
    svg("circle", { cx: (r * Math.cos(au)).toFixed(3), cy: (r * Math.sin(au)).toFixed(3), r: Math.max(0.7, w * 0.32), fill: "#e0b252" }, ring);
    const show = () => {
      g.querySelectorAll(".sel").forEach((e) => e.classList.remove("sel"));
      ring.querySelectorAll(".ring-seg").forEach((e) => e.classList.add("sel"));
      $("ringtip").innerHTML = "";
      const line = (s) => { const d = document.createElement("div"); d.innerHTML = s; $("ringtip").appendChild(d); };
      line("<b>night " + N.night + "</b> · " + k + " regions tied: " + N.tied.map((t) => REGION[t]).join(", "));
      line("its body read u = <b>" + N.u.toFixed(6) + "</b> · " + N.steps + " steps · it chose <b>" + REGION[N.act] + "</b>" +
           (differs ? " · the old rule would have chosen " + REGION[N.old] : " · the old rule would have agreed"));
      line('<a href="' + (DEMO ? "#" : "https://github.com/euvel/teich/blob/main/v05/diary/records.jsonl") + '">its record</a> · ' +
           '<a href="#decides" data-night="' + i + '">re-decide this night</a>');
      $("ringtip").querySelector("[data-night]").addEventListener("click", () => explainer.use(N));
    };
    ring.addEventListener("click", show); ring.addEventListener("focus", show);
    ring.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); show(); } });
  });
}

// ---------------------------------------------------------------- tonight
async function tonight() {
  const diaries = RECS.filter((r) => r.kind === "diary" && r.entry);
  if (diaries.length) {
    const night = Math.max.apply(null, diaries.map((d) => d.entry.day)) + 1, file = "night-" + String(night).padStart(4, "0") + ".md";
    try {
      const md = await (await fetch(RAW + "v05/diary/" + file, { cache: "no-store" })).text();
      const lines = md.split(String.fromCharCode(10));
      const at = lines.findIndex((l) => l.trim() === "## Tomorrow");
      const said = at >= 0 ? lines.slice(at + 1).find((l) => l.trim()) : null;
      if (said) {
        text($("voice"), said.trim().replace(/^Tomorrow I will ask: /, "Tomorrow I will ask: "));
        text($("voice-eyebrow"), "its voice — night " + night);
        $("voice-src").innerHTML = 'From <a href="https://github.com/euvel/teich/blob/main/v05/diary/' + file + '">its diary, night ' + night +
          "</a>, written by its own code from its own state. Nothing in its diary is written by a language model.";
      }
    } catch (e) { text($("voice-src"), "its latest diary page is unreachable right now."); }
  }
  if (!NIGHTS.length) {
    text($("t-night"), "none yet"); text($("t-tied"), "—"); text($("t-old"), "—"); text($("t-u"), "—");
    text($("t-chose"), "—"); text($("t-re"), "—");
    text($("t-note"), "Its first night under v0.6.0 is lived at its next wake. If its chosen thought ties, this card fills itself.");
    return;
  }
  const N = NIGHTS[NIGHTS.length - 1];
  text($("t-night"), N.night);
  $("t-tied").innerHTML = "";
  N.tied.forEach((t) => { const c = document.createElement("span"); c.className = "chip" + (t === N.act ? " won" : "") + (t === N.old && t !== N.act ? " old" : "");
    c.textContent = REGION[t]; $("t-tied").appendChild(c); });
  text($("t-old"), REGION[N.old]);
  text($("t-u"), "u = " + N.u.toFixed(6));
  text($("t-chose"), REGION[N.act] + " · " + N.steps + " steps");
  const re = DELIB.think2(N.lc, N.uHex);
  text($("t-re"), re.region === N.act ? "✓ the same region" : "✗ a different region (" + REGION[re.region] + ")");
  text($("t-note"), "");
}

// ---------------------------------------------------------------- the 'duduk' conversation
async function duduk() {
  const shown = RECS.filter((r) => r.kind === "shown" && r.seq < 50);
  const ans = shown.filter((r) => r.cluster === 60).map((r) => r.text_sha256);
  const first = shown.find((r) => r.pid === 1);
  const L = $("duduk"); L.innerHTML = "";
  const line = (n, who, html, cls) => { const d = document.createElement("div"); d.className = "line " + (cls || "");
    d.innerHTML = '<span class="n">' + n + '</span><span class="who' + (who === "FOUNDER" ? " f" : "") + '">' + who + '</span><span>' + html + "</span>";
    L.appendChild(d); return d; };
  const founder = async (n, sha, same) => {
    const words = DUDUK_WORDS[sha];
    const d = line(n, "FOUNDER", words ? '<span class="say"></span>' : '<span class="sealed" aria-label="sealed"></span>', "");
    const span = d.querySelector("span:last-child");
    if (words) d.querySelector(".say").textContent = words;
    const h = document.createElement("span"); h.className = "h";
    h.textContent = (words ? "sha256 " : "sealed · sha256 ") + sha.slice(0, 16) + "… ";
    if (same) { const s = document.createElement("span"); s.className = "same"; s.textContent = "← the same answer, provably "; h.appendChild(s); }
    if (words) { const ok = (await sha256hex(words)) === sha, m = document.createElement("span"); m.className = ok ? "ok" : "bad";
      m.textContent = ok ? "✓ matches the hash in its log, computed in this browser" : "✗ does not match its log"; h.appendChild(m); }
    span.appendChild(h);
  };
  if (first) await founder("DAY 1", first.text_sha256, false);
  line("NIGHT 1", "TEICH", '<span class="say">I could not place ‘duduk’. What is it?</span><span class="why">— because I heard it 2 times and no concept of mine was close enough.</span>');
  if (ans[0]) await founder("DAY 2", ans[0], false);
  line("NIGHT 2", "TEICH", '<span class="say">I could not place ‘duduk’. What is it?</span><span class="why">— you answered once before, and one more answer on another day would let me keep it.</span>');
  if (ans[1]) await founder("DAY 3", ans[1], ans[1] === ans[0]);
  line("NIGHT 3", "TEICH", '<span class="say">I now hold ‘duduk’: you answered the same on two different days.</span>');
  line("", "TEICH", '<span class="say">I proposed to grow, learning ‘duduk’. I registered my prediction first.</span>');
  line("", "GROWN", "v0.5.1 · ‘duduk’ = music · orchestra · band · its prediction held", "grown");
  $("duduk-note").innerHTML = "Its words are its own diary’s (" +
    ["1", "2", "3"].map((k) => '<a href="https://github.com/euvel/teich/blob/main/v05/diary/night-000' + k + '.md">night ' + k + "</a>").join(", ") + "). " +
    (Object.keys(DUDUK_WORDS).length ? "The founder’s are published by the founder; your browser checks each against the hash its log kept."
                                     : "The founder’s are sealed: only their hashes are in its log.");
  if ("IntersectionObserver" in window && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const rows = Array.from(L.querySelectorAll(".line")); rows.forEach((r) => r.classList.add("typed"));
    let shown = 0;                                     // each row appears as it enters the screen, one after another
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { io.unobserve(e.target);
      setTimeout(() => e.target.classList.add("shown"), 180 * (shown++ % 4)); } }), { threshold: 0.6 });
    rows.forEach((r) => io.observe(r));
    setTimeout(() => rows.forEach((r) => r.classList.add("shown")), 12000);   // never leave its words hidden
  }
}

// ---------------------------------------------------------------- identity chain
async function checkChain() {
  if (!RECS) return null;
  const links = RECS.filter((r) => (r.kind === "growth" || r.kind === "genome-amendment") && r.prev_identity && r.amendment_sha);
  const marks = [$("chk-1"), $("chk-2")]; let ok = 0;
  for (let i = 0; i < links.length && i < 2; i++) {
    const L = links[i], got = await sha256hex(L.prev_identity + L.amendment_sha), good = got === L.identity;
    marks[i].className = "chk " + (good ? "ok" : "bad");
    marks[i].textContent = good ? "✓ " + L.prev_identity.slice(0, 8) + "… + " + L.amendment_sha.slice(0, 8) + "… → " + got.slice(0, 8) + "…"
                                : "✗ does not recompute";
    if (good) ok++;
  }
  return { ok, n: Math.min(links.length, 2) };
}

// ---------------------------------------------------------------- how it decides (scroll explainer)
const LAB_NIGHT = { night: 0, lc: [0, 0, 0, 0, 0, 0, 0, 0, 0], uHex: "0x1.2ce3334440000p-1", lab: true };   // twin life 13000, night 0
const explainer = (() => {
  let N = null, step = 1;
  const fig = $("xfig");
  function pick() {
    if (NIGHTS.length) { const L = NIGHTS[NIGHTS.length - 1]; return { night: L.night, lc: L.lc, uHex: L.uHex, lab: false }; }
    return LAB_NIGHT;
  }
  function draw() {
    while (fig.lastChild && fig.lastChild.tagName !== "title") fig.removeChild(fig.lastChild);
    const lo = Math.min.apply(null, N.lc), tied = []; N.lc.forEach((c, r) => { if (c === lo) tied.push(r); });
    const R = 92;
    svg("circle", { r: R, fill: "none", stroke: "#1b2630", "stroke-width": 1 }, fig);
    if (step <= 2) {                                   // the nine regions
      for (let r = 0; r < 9; r++) {
        const a0 = 2 * Math.PI * r / 9 - Math.PI / 2 + 0.03, a1 = 2 * Math.PI * (r + 1) / 9 - Math.PI / 2 - 0.03, am = (a0 + a1) / 2;
        const isT = tied.indexOf(r) >= 0 && step === 2;
        svg("path", { d: arc(R, a0, a1), fill: "none", stroke: isT ? "#3fa7c9" : "#24323e", "stroke-width": isT ? 7 : 5 }, fig);
        const t = svg("text", { x: (R + 15) * Math.cos(am), y: (R + 15) * Math.sin(am) + 3, "text-anchor": "middle", "font-size": 7.5,
          "font-family": "IBM Plex Mono, monospace", fill: isT ? "#d9e2e8" : "#5f6d78" }, fig); t.textContent = N.lc[r];
      }
      const c = svg("text", { x: 0, y: 4, "text-anchor": "middle", "font-size": 9, "font-family": "IBM Plex Mono, monospace", fill: "#8796a1" }, fig);
      c.textContent = step === 1 ? "life counts" : tied.length + " tied at " + lo;
      text($("xcap"), (N.lab ? "a lab night (twin life 13000) · " : "night " + N.night + " · ") + "numbers = how often it has thought about each region");
      return;
    }
    const k = tied.length, G = DELIB.K[k];
    const walls = G.centre.map((c) => [Math.atan2(c[1], c[0]), Math.acos(G.cos_w)]);
    walls.forEach((w) => svg("path", { d: arc(R, w[0] - w[1], w[0] + w[1]), fill: "none", stroke: "#24323e", "stroke-width": 9 }, fig));
    const chosenNow = step === 5 ? tied[DELIB.deliberate(k, DELIB.hexf(N.uHex)).choice] : null;
    G.gap.forEach((c, j) => {                          // each gap between two walls is one tied region
      const a = Math.atan2(c[1], c[0]);
      const ends = walls.map((w) => w[0] + w[1]), starts = walls.map((w) => w[0] - w[1]);
      const norm = (x) => ((x - a + 3 * Math.PI) % (2 * Math.PI)) - Math.PI;
      const lo = Math.max.apply(null, ends.map(norm).filter((x) => x < 0)), hi = Math.min.apply(null, starts.map(norm).filter((x) => x > 0));
      const region = j < k ? tied[j] : null;
      const col = region === null ? "#2b2416" : (region === chosenNow ? "#3ddc84" : (step === 3 && j === 0 ? "#d9e2e8" : "#2a6e8f"));
      svg("path", { d: arc(R, a + lo + 0.03, a + hi - 0.03), fill: "none", stroke: col, "stroke-width": region === chosenNow ? 5 : 3, opacity: 0.9 }, fig);
    });
    G.gap.forEach((c, j) => {                          // the gaps = the tied regions (and k = 2's re-read gap)
      const a = Math.atan2(c[1], c[0]), region = j < k ? tied[j] : null;
      const isOld = step === 3 && j === 0, lab = region === null ? "re-read" : REGION[region];
      const t = svg("text", { x: (R + 12) * Math.cos(a), y: (R + 12) * Math.sin(a) + 3, "text-anchor": Math.cos(a) > 0.3 ? "start" : (Math.cos(a) < -0.3 ? "end" : "middle"),
        "font-size": 7, "font-family": "IBM Plex Mono, monospace", fill: isOld ? "#d9e2e8" : "#8796a1" }, fig);
      t.textContent = lab;
      if (isOld) svg("circle", { cx: R * Math.cos(a), cy: R * Math.sin(a), r: 4, fill: "none", stroke: "#d9e2e8", "stroke-dasharray": "2 1.5" }, fig);
    });
    if (step === 3) { text($("xcap"), "the old rule: the first tied region, " + REGION[tied[0]] + ", every time"); return; }
    const u = DELIB.hexf(N.uHex), x0 = DELIB.xiOf(u);
    svg("circle", { cx: R * x0[0], cy: R * x0[1], r: 3.4, fill: "#e0b252" }, fig);
    if (step === 4) { text($("xcap"), "its body read u = " + u.toFixed(6) + ": a point on the circle"); return; }
    const d = DELIB.deliberate(k, u), pts = d.path.map((p) => [R * p[0], R * p[1]]);
    const pl = svg("polyline", { points: pts.map((p) => p[0].toFixed(2) + "," + p[1].toFixed(2)).join(" "), fill: "none", stroke: "#e0b252",
      "stroke-width": 0.9, opacity: 0.85 }, fig);
    const len = pl.getTotalLength ? pl.getTotalLength() : 0;
    if (len && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      pl.style.strokeDasharray = len; pl.style.strokeDashoffset = len; pl.getBoundingClientRect();
      pl.style.transition = "stroke-dashoffset 1.6s ease-out"; pl.style.strokeDashoffset = 0;
    }
    pts.slice(1).forEach((p) => svg("circle", { cx: p[0], cy: p[1], r: 1.3, fill: "#e0b252", opacity: 0.7 }, fig));
    const last = pts[pts.length - 1];
    svg("circle", { cx: last[0], cy: last[1], r: 4.2, fill: "#3ddc84" }, fig);
    const chosen = tied[d.choice];
    text($("xcap"), d.steps + " reflections" + (d.rereads ? ", " + d.rereads + " re-read" + (d.rereads > 1 ? "s" : "") : "") + " → " + REGION[chosen] +
      " · recomputed in this browser" + (N.lab ? "" : (NIGHTS.length && NIGHTS[NIGHTS.length - 1].act === chosen ? " · ✓ matches its log" : "")));
  }
  function reset() { N = pick(); draw(); }
  function use(n) { N = { night: n.night, lc: n.lc, uHex: n.uHex, lab: false }; step = 5; draw(); }
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) {
      step = +e.target.dataset.step; document.querySelectorAll("#steps li").forEach((li) => li.classList.toggle("on", li === e.target)); if (N) draw(); } }),
      { rootMargin: "-45% 0px -45% 0px" });
    document.querySelectorAll("#steps li").forEach((li) => io.observe(li));
  } else { step = 5; document.querySelectorAll("#steps li").forEach((li) => li.classList.add("on")); }
  return { reset, use };
})();

// ---------------------------------------------------------------- verify
function setCheck(id, state, msg, ms) {
  const c = $(id); c.className = "check " + state;
  c.querySelector(".mark").textContent = { ok: "✓", bad: "✗", run: "…", na: "–" }[state] || "·";
  if (msg) c.querySelector(".r").textContent = msg;
  c.querySelector(".ms").textContent = ms != null ? ms.toFixed(0) + " ms" : "";
}
async function vSelf() {
  const t = performance.now(); let bad = 0;
  for (const v of SELFTEST) { const r = DELIB.deliberate(v[0], DELIB.hexf(v[1]));
    if (r.choice !== v[2] || r.steps !== v[3] || r.x !== DELIB.hexf(v[4]) || r.y !== DELIB.hexf(v[5])) bad++; }
  setCheck("v-self", bad ? "bad" : "ok", bad ? bad + " of " + SELFTEST.length + " reference values differ in this browser: its arithmetic is not IEEE-exact here, so the tie check below cannot be trusted on this device"
    : SELFTEST.length + " of " + SELFTEST.length + " reference values reproduced bit for bit (computed by the seat’s Python code; the full port test covers 209,600)", performance.now() - t);
  return !bad;
}
async function vTies() {
  const t = performance.now();
  if (!RECS) { setCheck("v-ties", "bad", "its record log is unreachable"); return false; }
  let same = 0; NIGHTS.forEach((N) => { if (DELIB.think2(N.lc, N.uHex).region === N.act) same++; });
  if (!NIGHTS.length) { setCheck("v-ties", "na", "no tie has been deliberated in its life yet: its first night under v0.6.0 is lived at its next wake", performance.now() - t); return null; }
  setCheck("v-ties", same === NIGHTS.length ? "ok" : "bad", same + " of " + NIGHTS.length + " logged ties re-decided in this browser land on the region it chose", performance.now() - t);
  return same === NIGHTS.length;
}
function canon(x) { if (Array.isArray(x)) return "[" + x.map(canon).join(",") + "]";
  if (x && typeof x === "object") return "{" + Object.keys(x).sort().map((k) => JSON.stringify(k) + ":" + canon(x[k])).join(",") + "}";
  return JSON.stringify(x); }
async function vChain() {
  const t = performance.now();
  try {
    let rows = [], from = 1, head = null;
    for (;;) {
      const r = await fetch("/o/teich-05/log-public?from=" + from + "&limit=500", { cache: "no-store" });
      if (r.status === 404 || r.status === 401) { setCheck("v-chain", "na", "this seat version does not publish its chain hashes yet"); return null; }
      const d = await r.json(); head = d; rows = rows.concat(d.records); if (d.records.length < 500) break; from = rows[rows.length - 1].seq + 1;
    }
    let h = head.genesis_anchor, broke = -1;
    for (const r of rows) { h = await sha256hex(h + r.raw); if (h !== r.h) { broke = r.seq; break; } }
    const p = peeks["teich-05"] || {}, tip = rows.length ? rows[rows.length - 1] : null;
    const headOk = !p.log_head || (tip && p.log_head.h === tip.h && p.log_head.seq === tip.seq);
    let pubOk = true;
    if (RECS && !DEMO) { const bySeq = {}; RECS.forEach((r) => { bySeq[r.seq] = r; });
      pubOk = rows.every((r) => !bySeq[r.seq] || canon(JSON.parse(r.raw)) === canon(bySeq[r.seq])); }
    const ok = broke < 0 && headOk && pubOk;
    setCheck("v-chain", ok ? "ok" : "bad", ok ? rows.length + " records · chain intact from its genesis anchor to the head its seat reports (" + (tip ? tip.h.slice(0, 12) : "") + "…) · the published log equals the seat’s"
      : (broke >= 0 ? "the chain breaks at record " + broke : (!headOk ? "the head does not match what its seat reports" : "the published log differs from the seat’s")), performance.now() - t);
    return ok;
  } catch (e) { setCheck("v-chain", "bad", "could not read its chain: " + e.message); return false; }
}
const ANCHORED = { "v06-spec-v1": "v06/book/V06_SPEC_v1.md", "v06-gates-prereg": "v06/book/PREREG_V06_GATES.md",
  "v06-gates-amendment1": "v06/book/PREREG_V06_GATES_Amendment1.md", "v06-gates-amendment2": "v06/book/PREREG_V06_GATES_Amendment2.md",
  "v06-build-manifest": "v06/book/MANIFEST_v06_build.sha256", "v06-verdict": "v06/book/REPORT_v06_verdict_2026-11-01.md",
  "v06-run2-outputs": "v06/book/campaign_run2/SHA256SUMS", "v06-migration": "v06/book/MIGRATION_RECORD.json" };
async function vAnchors() {
  const t = performance.now();
  try {
    const r = await fetch("/o/teich-03/anchors-public", { cache: "no-store" });
    if (r.status === 404 || r.status === 401) { setCheck("v-anchors", "na", "this seat version does not publish its anchor list yet"); return null; }
    const list = (await r.json()).anchors.filter((a) => ANCHORED[a.ref]);
    let ok = 0; const bad = [];
    for (const a of list) {
      const buf = await (await fetch(RAW + ANCHORED[a.ref], { cache: "no-store" })).arrayBuffer();
      if ((await sha256hex(buf)) === a.git_sha) ok++; else bad.push(a.ref);
    }
    const good = list.length && !bad.length;
    setCheck("v-anchors", good ? "ok" : "bad", good ? ok + " of " + list.length + " published files hash exactly to what the v0.3 seat anchored (spec, gates, both amendments, build manifest, verdict, outputs, migration)"
      : (bad.length ? "these do not match their anchors: " + bad.join(", ") : "no anchors found"), performance.now() - t);
    return good;
  } catch (e) { setCheck("v-anchors", "bad", "could not read the anchors: " + e.message); return false; }
}
async function verifyAll() {
  ["v-self", "v-ties", "v-chain", "v-anchors"].forEach((id) => setCheck(id, "run"));
  const b = $("v-banner"); b.className = "banner wait"; b.textContent = "checking in this browser…";
  const res = [await vSelf(), await vTies(), await vChain(), await vAnchors(), await checkChain()];
  const chain = res[4];
  const fails = res.slice(0, 4).filter((x) => x === false).length + (chain && chain.ok < chain.n ? 1 : 0);
  const done = res.slice(0, 4).filter((x) => x === true).length;
  const parts = [];
  if (res[1] === true) parts.push("re-decided " + NIGHTS.length + " of " + NIGHTS.length + " ties");
  if (res[2] === true) parts.push("its record chain is intact");
  if (res[3] === true) parts.push("its book matches its anchors");
  if (chain && chain.n) parts.push(chain.ok + " of " + chain.n + " identity links recompute");
  b.className = "banner" + (fails ? " bad" : "");
  b.textContent = fails ? fails + " check" + (fails > 1 ? "s" : "") + " failed in this browser. See above." :
    "Your browser " + (parts.length ? parts.join(", ") : "ran " + done + " checks") + ". Computed on your machine, not ours.";
  const st = $("st-verified"); st.className = "verified " + (fails ? "bad" : "ok");
  st.textContent = fails ? "✗ a check failed in this browser" : "✓ verified in this browser";
}

// ---------------------------------------------------------------- family tabs
document.querySelectorAll(".gen").forEach((b) => b.addEventListener("click", () => {
  const open = !b.classList.contains("open");
  document.querySelectorAll(".gen").forEach((x) => { x.classList.remove("open"); x.setAttribute("aria-selected", "false"); });
  document.querySelectorAll(".genpanel").forEach((p) => { p.hidden = true; });
  if (open) { b.classList.add("open"); b.setAttribute("aria-selected", "true"); $("gp-" + b.dataset.gen).hidden = false; }
}));
$("btn-verify").addEventListener("click", verifyAll);
$("btn-chain").addEventListener("click", checkChain);
const menu = Array.from(document.querySelectorAll("nav.menu a"));
if ("IntersectionObserver" in window) {
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) menu.forEach((a) => a.classList.toggle("here", a.getAttribute("href") === "#" + e.target.id)); }),
    { rootMargin: "-40% 0px -55% 0px" });
  document.querySelectorAll("main section[id]").forEach((s) => io.observe(s));
}

// ---------------------------------------------------------------- start
(async () => {
  nextWake(); setInterval(nextWake, 60000);
  await readSeats(); tickOwed(); setInterval(tickOwed, 1000); setInterval(readSeats, 30000);
  await readLog(); setInterval(readLog, 300000);
  verifyAll();
})();
