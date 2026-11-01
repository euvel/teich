"""Teich v0.4 — the second self (BUILD candidate, lab only; spec V04_SPEC_part3_self.md, founder decisions 10-19).

It watches the first self's own doing and nothing else:
  perceiving   one act = one mention the Ears propose for the read-back; kind = heart region of its cluster (9 kinds);
               outcome = the founder strikes it or keeps it (the veto-only read-back, unchanged)
  speaking     one act = one diary reading spoken (a shift); kind READINGS; outcome = revised later although its
               cluster had no accepted step in between (bad), or stood
and does five things: MONITOR (integer counts per kind, per night), PREDICT (before the read-back is shown: the chance
the act is struck, an exact fraction, committed first), COMPARE (verdict per kind: MINE / GIVEN / FINE / UNRESOLVED),
CONTROL (its will: a caution 0..4 per perception kind; raises the thresholds it applies to the Ears' proposals),
INTEGRATE (the nightly `self` block of the diary; every claim has a receipt recomputable from the log).

Confidence of a perception act: cw = the lowest caution level that would change it (withhold it, or drop its feeling),
5 if no level 1..4 would. "lo" acts (cw <= 4) are those its will can reach; "hi" acts (cw = 5) are out of reach.
  MINE   lo acts are struck more than hi acts, beyond chance        -> its own confidence knows where it fails
  GIVEN  enough of both, struck often, and no difference            -> errors are spread over its confidence: the world
  FINE   enough acts, rarely struck
  UNRESOLVED otherwise (it says "I don't know yet")
Arithmetic: Python ints and fractions.Fraction only — identical on every CPU and numpy. No language model. It never
reads the true dials (like the self-reading) and never sees the diary's public `verification` block.
"""
from __future__ import annotations

from fractions import Fraction
from math import comb

N_KINDS = 9                  # perception kinds = heart regions (v0.3's 8 + self); founder decision D-S1
READINGS = 9                 # the speaking kind
K = 10
LEVELS = 4                   # caution 0..4 (D-S2)
NAMING_STEP = 0.03           # caution c raises TAU_MAP by 0.03*c (naming) ...
FEELING_STEP = 0.5           # ... and THETA by 0.5*c (feeling)
RING = 40                    # nights kept (forgetting: W in [W_MIN, RING]; founder-confirmed 3..40)
W_MIN = 3
RECENT = 3                   # nights compared against the rest of the window for the change test
COST = 2                     # a wrong mention costs two right ones (D-S3)
PROBES_PER_DAY = 1           # D-S4 allows up to 3; design 10-19: 1 (probes crowded out the will)
# design constants (D-S5: fixed by design simulations before the freeze)
ALPHA_M = Fraction(1, 100)   # MINE: one-sided Fisher p <= ALPHA_M ...  (design 10-20: 1/20 gave false MINE on GIVEN
                             # kinds from testing every night; 1/100 cut swaps 0.013 -> 0.006 at 4 acts/kind/night)
DELTA = Fraction(1, 10)      # ... and r_lo - r_hi >= DELTA; GIVEN: |r_lo - r_hi| < DELTA
N_G = 20                     # GIVEN / FINE need this many acts (each bucket for GIVEN)
RHO_G = Fraction(1, 10)      # struck rate separating FINE from GIVEN
N_STEP = 5                   # outcomes at a caution level needed before the will moves on it
ALPHA_F = Fraction(1, 100)   # change test for forgetting
PROBE_NEED = 5               # curiosity: probe a hidden level only while the window holds fewer outcomes than the will needs
CODE = "self_v1"


def cw_of(mn: float, mf: float | None) -> tuple[int, int]:
    """(cn, cf): lowest caution level 1..4 that withholds the mention (naming margin mn = cos - TAU_MAP) / drops its
    feeling (feeling margin mf = |attitude| - THETA, None when no feeling); 5 when none does. Computed by the organ
    side once; the creature only sees the integers."""
    cn = next((c for c in range(1, LEVELS + 1) if mn < NAMING_STEP * c), 5)
    cf = 5 if mf is None else next((c for c in range(1, LEVELS + 1) if mf < FEELING_STEP * c), 5)
    return cn, cf


def cw_of_mention(m, tau_map, theta) -> tuple[int, int]:
    """(cn, cf) for one Ears mention. Topic mentions carry the clause and sentence attitudes (invariance: both must
    agree), so the feeling margin is the weaker one; the self mention carries one `attitude`."""
    if m["sign"] == 0:
        mf = None
    elif "attitude" in m:
        mf = abs(m["attitude"]) - theta
    else:
        mf = min(abs(m["attitude_clause"]), abs(m["attitude_sentence"])) - theta
    return cw_of(m["cos"] - tau_map, mf)


def fisher_greater(a, b, c, d) -> Fraction:
    """One-sided Fisher exact p for 'row 1 has a larger first-column share than row 2'; table [[a, b], [c, d]]."""
    n, k, N = a + b, a + c, a + b + c + d
    if n == 0 or N == n:
        return Fraction(1)
    tot = comb(N, n)
    return Fraction(sum(comb(k, x) * comb(N - k, n - x) for x in range(a, min(k, n) + 1)), tot)


def _empty_night():
    return {"lv": [[0, 0] for _ in range(5)], "alt": [0, 0], "bri": [0, 1], "b0": [0, 1], "ps": [0, 1], "pn": 0, "pr": [0, 0]}


# ---------------------------------------------------------------------- pure functions on counts (receipts call these)
def window_counts(nights):
    """nights: list of per-night dicts -> lo/hi acts and struck, level table, Brier sum, n predictions."""
    lv = [[0, 0] for _ in range(5)]; bri = Fraction(0); b0 = Fraction(0); pn = 0
    for d in nights:
        for i in range(5):
            lv[i][0] += d["lv"][i][0]; lv[i][1] += d["lv"][i][1]
        bri += Fraction(*d["bri"]); b0 += Fraction(*d["b0"]); pn += d["pn"]
    n_lo = sum(lv[i][0] for i in range(4)); s_lo = sum(lv[i][1] for i in range(4))
    return {"lv": lv, "n_lo": n_lo, "s_lo": s_lo, "n_hi": lv[4][0], "s_hi": lv[4][1], "bri": bri, "b0": b0, "pn": pn}


def verdict_of(w, kind) -> str:
    n_lo, s_lo, n_hi, s_hi = w["n_lo"], w["s_lo"], w["n_hi"], w["s_hi"]
    n, s = n_lo + n_hi, s_lo + s_hi
    if kind == READINGS:                      # no lever in v0.4: it cannot test MINE, only say how often it was wrong
        if n >= N_G:
            return "FINE" if Fraction(s, n) < RHO_G else "GIVEN"
        return "UNRESOLVED"
    if n_lo and n_hi:
        r_lo, r_hi = Fraction(s_lo, n_lo), Fraction(s_hi, n_hi)
        if r_lo - r_hi >= DELTA and fisher_greater(s_lo, n_lo - s_lo, s_hi, n_hi - s_hi) <= ALPHA_M:
            return "MINE"
    if n >= N_G and n_lo >= N_G and Fraction(s, n) < RHO_G:     # FINE needs evidence on the acts its will can reach:
        return "FINE"                                           # else "my caution works" would read as "I am fine"
    if n_lo >= N_G and n_hi >= N_G and Fraction(s, n) >= RHO_G and abs(Fraction(s_lo, n_lo) - Fraction(s_hi, n_hi)) < DELTA:
        return "GIVEN"
    return "UNRESOLVED"


def will_of(w, verdict, c) -> tuple[int, str]:
    """-> (new caution, rule id). Counterfactual from the window: acts at level L are those caution L would change."""
    lv = w["lv"]
    if verdict == "MINE" and c < LEVELS:
        s, k = lv[c][1], lv[c][0] - lv[c][1]            # acts with cw == c+1 (index c)
        if s + k >= N_STEP and COST * s > k:
            return c + 1, "up: MINE, and the next level would remove more cost than value"
    if c > 0:
        if verdict in ("GIVEN", "FINE"):
            return c - 1, f"down: {verdict}, caution there cannot help"
        s, k = lv[c - 1][1], lv[c - 1][0] - lv[c - 1][1]  # acts with cw == c (the ones its caution now hides)
        if s + k >= N_STEP and COST * s <= k:
            return c - 1, "down: what my caution hides is mostly right"
    return c, "keep"


def changed(nights_recent, nights_rest) -> bool:
    a = window_counts(nights_recent); b = window_counts(nights_rest)
    n1, s1 = a["n_lo"] + a["n_hi"], a["s_lo"] + a["s_hi"]
    n2, s2 = b["n_lo"] + b["n_hi"], b["s_lo"] + b["s_hi"]
    if not n1 or not n2:
        return False
    return min(fisher_greater(s1, n1 - s1, s2, n2 - s2), fisher_greater(s2, n2 - s2, s1, n1 - s1)) <= ALPHA_F


# ---------------------------------------------------------------------- the second self (state lives in the blob)
class SecondSelf:
    def __init__(self):
        self.ring = [[_empty_night() for _ in range(RING)] for _ in range(K)]
        self.caution = [0] * N_KINDS
        self.verdict = ["UNRESOLVED"] * K
        self.W = [RING] * K
        self.night = 0                       # the night outcomes are currently counted into
        self.probe_day, self.probes_used = -1, 0
        self.pending = {}                    # pid -> proposal shown, awaiting the founder's decision
        self.next_pid = 1
        self.open_readings = {}              # cluster -> {"seq": predict seq, "night": n, "p": [num, den], "to": r}
        self.organ = None

    # ---------------------------------------------------------- blob
    def to_json(self):
        return {"ring": self.ring, "caution": self.caution, "verdict": self.verdict, "W": self.W, "night": self.night,
                "probe": [self.probe_day, self.probes_used], "pending": {str(k): v for k, v in sorted(self.pending.items())},
                "next_pid": self.next_pid, "open_readings": {str(k): v for k, v in sorted(self.open_readings.items())},
                "organ": self.organ}

    @classmethod
    def from_json(cls, d):
        s = cls()
        s.ring, s.caution, s.verdict, s.W, s.night = d["ring"], d["caution"], d["verdict"], d["W"], d["night"]
        s.probe_day, s.probes_used = d["probe"]
        s.pending = {int(k): v for k, v in d["pending"].items()}
        s.next_pid = d["next_pid"]
        s.open_readings = {int(k): v for k, v in d["open_readings"].items()}
        s.organ = d["organ"]
        return s

    # ---------------------------------------------------------- helpers
    def _slot(self, kind, night=None):
        return self.ring[kind][(self.night if night is None else night) % RING]

    def _window(self, kind, end):
        return [self.ring[kind][n % RING] for n in range(max(0, end - self.W[kind] + 1), end + 1)]

    def _windows(self):
        """Window counts of every perception kind (constant within one present(): outcomes arrive only in decide)."""
        return [window_counts(self._window(k, self.night)) for k in range(N_KINDS)]

    def _p(self, kind, lo, ws=None):
        """-> (p, p0). p = chance this act goes wrong: its kind's window (same bucket), shrunk toward the pooled rate of
        all perception kinds (same bucket) with the weight of 2 acts; the pool itself starts from 1/2.
        p0 = the baseline WITHOUT self-knowledge: its overall struck rate (all kinds, all confidence), for S6."""
        def ns(w):
            if kind == READINGS:
                return w["n_lo"] + w["n_hi"], w["s_lo"] + w["s_hi"]
            return (w["n_lo"], w["s_lo"]) if lo else (w["n_hi"], w["s_hi"])
        if kind == READINGS:
            n, s = ns(window_counts(self._window(kind, self.night)))
            p = Fraction(s + 1, n + 2)
            return p, p
        allp = ws if ws is not None else self._windows()
        n, s = ns(allp[kind])
        pool = [ns(w) for w in allp]
        m = Fraction(sum(x[1] for x in pool) + 1, sum(x[0] for x in pool) + 2)
        m0 = Fraction(sum(w["s_lo"] + w["s_hi"] for w in allp) + 1, sum(w["n_lo"] + w["n_hi"] for w in allp) + 2)
        return (s + 2 * m) / (n + 2), m0

    # ---------------------------------------------------------- PRESENT (phase 1 of a conversation; committed first)
    def present(self, proposals, conversation, day, organ, emit):
        """proposals: [{"cluster", "kind", "sign", "text_sha256", "cn", "cf"}] from the Ears, in order.
        -> [{"pid", "cluster", "sign", "shown", "altered", "probe"}]; emits `shown` and `predict` records."""
        if organ != self.organ:                 # a new organ: the old errors were another organ's
            if self.organ is not None:
                for k in range(N_KINDS):
                    self.ring[k] = [_empty_night() for _ in range(RING)]; self.W[k] = RING
                    self.verdict[k] = "UNRESOLVED"; self.caution[k] = 0
            self.organ = organ
        if day != self.probe_day:
            self.probe_day, self.probes_used = day, 0
        out, probe_pid = [], None
        ws = self._windows()
        hidden = [i for i, p in enumerate(proposals) if min(p["cn"], p["cf"]) <= self.caution[p["kind"]]]
        if hidden and self.probes_used < PROBES_PER_DAY:
            def need(i):                         # fewest outcomes on the level its will would give back next (cw == c)
                k = proposals[i]["kind"]
                return (ws[k]["lv"][self.caution[k] - 1][0], k, i)
            cand = [i for i in hidden if self.verdict[proposals[i]["kind"]] != "GIVEN" and need(i)[0] < PROBE_NEED]
            if cand:
                probe_pid = min(cand, key=need)
        for i, p in enumerate(proposals):
            pid = self.next_pid; self.next_pid += 1
            c = self.caution[p["kind"]]; cw = min(p["cn"], p["cf"])
            probe = i == probe_pid
            if probe:
                self.probes_used += 1
            withheld = p["cn"] <= c and not probe
            altered = (not withheld) and (not probe) and p["cf"] <= c and p["sign"] != 0
            sign = 0 if altered else p["sign"]
            item = {"pid": pid, "cluster": p["cluster"], "act_kind": p["kind"], "sign": sign, "shown": not withheld,
                    "altered": altered, "probe": probe, "cw": cw, "caution": c}
            emit("shown", {**item, "conversation": conversation, "text_sha256": p["text_sha256"],
                           "why": ("probe: I'm unsure here; I'm testing myself" if probe else
                                   "withheld: unsure" if withheld else "feeling dropped: unsure" if altered else "shown")})
            if not withheld:
                rec = {**item, "conversation": conversation, "text_sha256": p["text_sha256"]}
                if not altered:
                    pr, p0 = self._p(p["kind"], cw <= LEVELS, ws)
                    rec["p"], rec["p0"] = _q(pr), _q(p0)
                    rec["predict_seq"] = emit("predict", {"pid": pid, "act_kind": p["kind"], "cw": cw,
                                                          "p": rec["p"], "p0": rec["p0"], "fn": f"{CODE}.p"})
                self.pending[pid] = rec
            out.append(item)
        return out

    # ---------------------------------------------------------- DECIDE (phase 2: the founder's strikes)
    def decide(self, conversation, struck, emit):
        """struck: set of pids. -> the kept items (to be heard by the first self under its laws)."""
        kept = []
        for pid in sorted(k for k, v in self.pending.items() if v["conversation"] == conversation):
            rec = self.pending.pop(pid); bad = pid in struck
            slot = self._slot(rec["act_kind"])
            if rec["probe"]:
                slot["pr"][0] += 1; slot["pr"][1] += bad
            if rec["altered"]:
                slot["alt"][0] += 1; slot["alt"][1] += bad
            else:
                L = rec["cw"] - 1
                slot["lv"][L][0] += 1; slot["lv"][L][1] += bad
                p = Fraction(*rec["p"]); o = 1 if bad else 0
                slot["bri"] = _q(Fraction(*slot["bri"]) + (p - o) ** 2); slot["ps"] = _q(Fraction(*slot["ps"]) + p)
                slot["b0"] = _q(Fraction(*slot["b0"]) + (Fraction(*rec["p0"]) - o) ** 2)
                slot["pn"] += 1
            emit("outcome", {"pid": pid, "act_kind": rec["act_kind"], "night": self.night, "cw": rec["cw"],
                             "altered": rec["altered"], "probe": rec["probe"], "struck": bad,
                             "p": rec.get("p"), "p0": rec.get("p0"), "predict_seq": rec.get("predict_seq")})
            if not bad:
                kept.append(rec)
        return kept

    # ---------------------------------------------------------- speaking: diary readings
    def readings(self, entry, moved, emit):
        """Called at night close with tonight's diary entry. moved: clusters whose dial moved in this window."""
        slot = self._slot(READINGS)
        for j in sorted(moved):
            o = self.open_readings.pop(j, None)
            if o:
                self._close_reading(j, o, False, slot, emit)
        for sh in entry["shifts"]:
            j = sh["cluster"]; o = self.open_readings.pop(j, None)
            if o:
                self._close_reading(j, o, True, slot, emit)        # revised with no step in between
            if sh["to"] > 0:
                pr, _ = self._p(READINGS, False)
                seq = emit("predict", {"act_kind": READINGS, "cluster": j, "read": sh["to"],
                                       "p": _q(pr), "p0": _q(pr), "fn": f"{CODE}.p"})
                self.open_readings[j] = {"seq": seq, "night": self.night, "p": _q(pr)}
        for j in sorted(self.open_readings):
            if self.night - self.open_readings[j]["night"] >= RING:
                self._close_reading(j, self.open_readings.pop(j), False, slot, emit)

    def _close_reading(self, j, o, bad, slot, emit):
        slot["lv"][4][0] += 1; slot["lv"][4][1] += bad
        p = Fraction(*o["p"]); slot["bri"] = _q(Fraction(*slot["bri"]) + (p - (1 if bad else 0)) ** 2)
        slot["b0"] = _q(Fraction(*slot["b0"]) + (p - (1 if bad else 0)) ** 2)
        slot["ps"] = _q(Fraction(*slot["ps"]) + p); slot["pn"] += 1
        emit("outcome", {"act_kind": READINGS, "cluster": j, "night": self.night, "cw": 5, "altered": False,
                         "probe": False, "struck": bad, "p": o["p"], "p0": o["p"], "predict_seq": o["seq"]})

    # ---------------------------------------------------------- NIGHT: compare, will, forget, integrate
    def nightly(self, log_through):
        """Close night self.night. -> the `self` block for tonight's diary entry (and the control records' content)."""
        d = self.night
        block = {"night": d, "log_through": log_through, "facts": [], "comparisons": [], "verdicts": [],
                 "will": [], "curiosity": [], "calibration": None}
        errs = []
        for k in range(K):
            win = self._window(k, d)
            w = window_counts(win)
            a, b = max(0, d - self.W[k] + 1), d
            sel = {"kind": k, "nights": [a, b]}
            v = verdict_of(w, k)
            n, s = w["n_lo"] + w["n_hi"], w["s_lo"] + w["s_hi"]
            rc = {"log_through": log_through, "select": sel}
            if v != self.verdict[k]:
                block["verdicts"].append({"kind": k, "from": self.verdict[k], "to": v,
                                          "receipt": {**rc, "fn": f"{CODE}.verdict_of",
                                                      "out": {"verdict": v, "n_lo": w["n_lo"], "s_lo": w["s_lo"],
                                                              "n_hi": w["n_hi"], "s_hi": w["s_hi"]}}})
            self.verdict[k] = v
            if w["pn"]:
                pred = _pred_mean(win)
                act = Fraction(s, n) if n else Fraction(0)
                errs.append((abs(pred - act), k, pred, act, n, s))
            if k < N_KINDS:
                c0 = self.caution[k]; c1, why = will_of(w, v, c0)
                if c1 != c0:
                    self.caution[k] = c1
                    block["will"].append({"kind": k, "caution": [c0, c1], "why": why,
                                          "receipt": {**rc, "fn": f"{CODE}.will_of",
                                                      "out": {"caution_before": c0, "caution": c1, "lv": w["lv"], "verdict": v}}})
        errs.sort(key=lambda e: (-e[0], e[1]))
        for e, k, pred, act, n, s in errs[:3]:
            block["comparisons"].append({"kind": k, "predicted": _q(pred), "actual": _q(act),
                                         "receipt": {"log_through": log_through,
                                                     "select": {"kind": k, "nights": [max(0, d - self.W[k] + 1), d]},
                                                     "fn": f"{CODE}.compare", "out": {"n": n, "struck": s}}})
        allw = [self.ring[k][n % RING] for k in range(K) for n in range(max(0, d - self.W[k] + 1), d + 1)]
        tot = window_counts(allw)
        if tot["pn"]:
            block["calibration"] = {"brier": _q(tot["bri"] / tot["pn"]), "without_self_knowledge": _q(tot["b0"] / tot["pn"]),
                                    "receipt": {"log_through": log_through, "select": {"kind": "all", "W": list(self.W),
                                                                                       "night": d},
                                                "fn": f"{CODE}.calibration", "out": {"pn": tot["pn"]}}}
        acts = [(k, self.ring[k][d % RING]) for k in range(K)]
        block["facts"] = [{"kind": k, "acts": sum(x[0] for x in sl["lv"]) + sl["alt"][0],
                           "struck": sum(x[1] for x in sl["lv"]) + sl["alt"][1],
                           "receipt": {"log_through": log_through, "select": {"kind": k, "nights": [d, d]},
                                       "fn": f"{CODE}.facts"}}
                          for k, sl in acts if sum(x[0] for x in sl["lv"]) + sl["alt"][0]]
        block["curiosity"] = [{"kind": k, "probes": sl["pr"][0], "struck": sl["pr"][1],
                               "receipt": {"log_through": log_through, "select": {"kind": k, "nights": [d, d]},
                                           "fn": f"{CODE}.curiosity"}}
                              for k, sl in acts if sl["pr"][0]]
        # forgetting: each kind's window shrinks after a change, grows by one night otherwise
        for k in range(K):
            recent = [self.ring[k][n % RING] for n in range(max(0, d - RECENT + 1), d + 1)]
            rest = [self.ring[k][n % RING] for n in range(max(0, d - self.W[k] + 1), max(0, d - RECENT + 1))]
            self.W[k] = RECENT if changed(recent, rest) else min(self.W[k] + 1, RING)
        # the next night starts empty
        self.night = d + 1
        self.ring_clear(self.night)
        return block

    def ring_clear(self, night):
        for k in range(K):
            self.ring[k][night % RING] = _empty_night()


def _q(f: Fraction):
    return [f.numerator, f.denominator]


def _pred_mean(nights):
    """Mean prediction over the window's outcomes (each night keeps the sum of its predictions, 'ps')."""
    ps = Fraction(0); n = 0
    for d in nights:
        ps += Fraction(*d.get("ps", [0, 1])); n += d["pn"]
    return ps / n if n else Fraction(0)
