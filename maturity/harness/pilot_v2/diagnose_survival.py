"""Step B — does a RICHER input survive the gap, or does chaos erase every direction?

Step 0 (REPORT_step0_2026-07-27.md) established that the Ears compress every utterance
to one scalar pushed into `tau[...,0]`, and that even that scalar's SIGN does not survive
300-1800 ticks: two positive-valence sentences produced opposite displacements at the
probe. Before anyone redesigns `ears.py`, this asks whether ANY input direction can carry
a distinguishable mark across the gap. If none can, the "what was said to me" branch is
dead and no Ears redesign helps.

The core is a suspension flow, so its Lyapunov spectrum should be one positive exponent
(the fold, `tau0`), one ZERO (the flow / roof direction, `tau1`), and the rest negative.
That predicts three distinct fates for a perturbation, and they are directly testable:

  tau0  expanding   -> amplifies, then decorrelates; sign destroyed   (today's result)
  tau1  neutral     -> offset neither grows nor decays; persists      (the hypothesis)
  weak/ell contracting -> decays toward zero; no lasting effect

A push on `tau1` is NOT merely "starting earlier": it shifts the clock RELATIVE to the
fold, changing which lobe values coincide with roof wraps, hence which flips happen. The
Ears have never touched it.

DESIGN. Paired +delta / -delta at matched dose, identical seed and tick schedule, so the
only difference between the two runs of a pair is the SIGN of the push. Survival is then
measured as the paired AUC

    P( M(+delta) > M(-delta) )        ties counted 0.5

on each observable readout M at the probe. 0.5 = the probe tells you nothing about what
was done; 1.0 = the sign is perfectly recoverable. This is the same question D1 asked of
the real Ears (which answered P = 0.375, i.e. nothing), generalised to every direction.

Doses are matched as a fraction of each coordinate's own natural spread over a free run
(0.25 x std, the Ears' own BETA), spread over WINDOW=120 ticks exactly as ears.py delivers
force. `tau0_earsdose` additionally reproduces the REAL Ears dose as a positive control,
so the known-null result appears in the table as a reference row.

`ell` is perturbed multiplicatively (additive in log-space, which is what the Observer
consumes via z = cat([tau, log(ell)])), keeping it positive by construction.

NOTHING IS MODIFIED: no ears.py change, no observer.py change, no genome, no seat. This is
an offline probe on fresh synthetic cores, retired seeds only. Measure before building.

Run: python diagnose_survival.py [--seeds 48]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

import scripts_tint as st  # noqa: E402

WINDOW = 120          # ears.py delivery window, ticks
BETA = 0.25           # ears.py dose fraction
WARM = 200            # _CoreEngine warm-up
PRE_PIVOT = 160       # ticks of "conversation" before the push (4 turns x 40)
OBS_WINDOW = 400      # _CoreEngine observation window


class ProbeEngine:
    """Mirror of arms._CoreEngine with a configurable forcing target.

    Identical structure: same synthetic x0, same 200-tick warm-up, same _fn_step /
    private_step order, same 400-tick observation window. The ONLY generalisation is
    which coordinate the nudge lands on. Verified bit-identical to _CoreEngine at zero
    dose by selftest() below -- if that check ever fails, this class has drifted from
    the real engine and every number it produces is void.
    """

    def __init__(self, model, seed):
        from arms import _synthetic_x0
        self.m = model
        from observer import Observer
        self.obs = Observer(model)
        self.period = float(model.gcfg.anchor_period)
        dtype = next(model.parameters()).dtype
        x0 = torch.as_tensor(_synthetic_x0(seed), dtype=dtype).reshape(1, -1)
        with torch.no_grad():
            self.tau, self.ell = model.proxy.raw_to_fn(model.encoder(x0))
            self.phi = model.private_init(1, None)
            self.g = model.gates()
            self.n = 0
            self.pending = {}
            for _ in range(WARM):
                self.tau, self.ell = self.m._fn_step(self.tau, self.ell, self.g)
                self.phi = self.m.private_step(self.phi)

    def push(self, block, idx, total, start_tick):
        """Queue `total` spread evenly over WINDOW ticks from start_tick."""
        per_tick = total / WINDOW
        for i in range(WINDOW):
            self.pending[start_tick + i] = (block, idx, per_tick)

    @torch.no_grad()
    def advance(self, ticks):
        self.obs.reset()
        obs_start = max(0, ticks - OBS_WINDOW)
        r = None
        for i in range(ticks):
            f = self.pending.pop(self.n, None)
            if f is not None:
                block, idx, v = f
                if block == "tau":
                    self.tau = self.tau.clone()
                    if idx == 0:                    # ears.py wraps tau_0 mod period
                        self.tau[0, 0] = (self.tau[0, 0] + v) % self.period
                    else:
                        self.tau[0, idx] = self.tau[0, idx] + v
                else:                               # multiplicative: additive in log ell
                    self.ell = self.ell.clone()
                    self.ell[0, idx] = self.ell[0, idx] * float(np.exp(v))
            self.tau, self.ell = self.m._fn_step(self.tau, self.ell, self.g)
            self.phi = self.m.private_step(self.phi)
            self.n += 1
            if i >= obs_start:
                r = self.obs.observe(self.tau, self.ell, self.phi)
        if r is None:
            r = self.obs.observe(self.tau, self.ell, self.phi)
        return r


def selftest(model):
    """ProbeEngine at zero dose must reproduce arms._CoreEngine exactly."""
    import arms as A
    e1 = A._CoreEngine(model, 0, deaf=True)
    r1 = e1.advance(PRE_PIVOT)
    e2 = ProbeEngine(model, 0)
    r2 = e2.advance(PRE_PIVOT)
    keys = ("basin", "lobe_coord", "saddle_proximity", "steps_to_switch",
            "will_flip", "n_switches")
    bad = [k for k in keys if r1[k] != r2[k]]
    if bad:
        raise SystemExit(f"SELFTEST FAILED: ProbeEngine has drifted from _CoreEngine "
                         f"on {bad}\n  _CoreEngine {[r1[k] for k in bad]}\n"
                         f"  ProbeEngine {[r2[k] for k in bad]}")
    print("selftest OK: ProbeEngine == _CoreEngine at zero dose "
          f"(basin {r1['basin']}, lobe {r1['lobe_coord']:.6f})")


def natural_scales(model):
    """Per-coordinate std over a free run -- the dose normaliser."""
    from arms import _synthetic_x0
    dtype = next(model.parameters()).dtype
    with torch.no_grad():
        x0 = torch.as_tensor(_synthetic_x0(0), dtype=dtype).reshape(1, -1)
        tau, ell = model.proxy.raw_to_fn(model.encoder(x0))
        g = model.gates()
        T, E, t, e = [tau], [ell], tau, ell
        for _ in range(6000):
            t, e = model._fn_step(t, e, g)
            T.append(t); E.append(e)
        Tn = torch.cat(T, 0).double().numpy()
        En = torch.cat(E, 0).double().numpy()
    return Tn.std(0), np.log(En).std(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=48)
    args = ap.parse_args()

    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    selftest(model)

    from observer import Observer
    thresh = Observer(model).flip_thresh
    tau_std, logell_std = natural_scales(model)
    ears_dose = BETA * 0.04038 * WINDOW      # ears.py: max_nudge/tick x WINDOW

    DIRS = [
        ("tau0_earsdose", "tau", 0, ears_dose),                  # real Ears, control
        ("tau0_expanding", "tau", 0, BETA * float(tau_std[0])),
        ("tau1_neutral", "tau", 1, BETA * float(tau_std[1])),    # the hypothesis
        ("tau3_weak", "tau", 3, BETA * float(tau_std[3])),
        ("ell1_contracting", "ell", 1, BETA * float(logell_std[1])),
    ]
    print(f"\ndoses (BETA={BETA} x natural spread, spread over {WINDOW} ticks):")
    for name, blk, idx, dose in DIRS:
        print(f"    {name:18s} {blk}[{idx}]  total {dose:+.5f}")

    def saddle_of(r):
        ax = abs(float(r["lobe_coord"]))
        return max(0.0, 1.0 - abs(ax - thresh) / thresh)

    CHANNELS = {
        "saddle(unshuttered)": saddle_of,
        "lobe_coord": lambda r: float(r["lobe_coord"]),
        "basin": lambda r: float(r["basin"]),
        "n_switches": lambda r: float(r["n_switches"]),
        "steps_to_switch": lambda r: float(r["steps_to_switch"]),
    }

    t0, rows = time.time(), []
    for name, blk, idx, dose in DIRS:
        for seed in range(args.seeds):
            gap = int(st.GAPS[seed % len(st.GAPS)])
            out = {}
            for sign in (+1, -1):
                eng = ProbeEngine(model, seed)
                eng.advance(PRE_PIVOT)
                eng.push(blk, idx, sign * dose, eng.n)
                r = eng.advance(gap)
                out[sign] = {k: fn(r) for k, fn in CHANNELS.items()}
            rows.append(dict(dir=name, seed=seed, gap=gap,
                             plus=out[+1], minus=out[-1]))
        print(f"  {name}: {args.seeds} pairs done ({time.time()-t0:.0f}s)", flush=True)
    (HERE / "out_survival.json").write_text(json.dumps(rows, indent=1))

    # ---- paired AUC: P(M(+d) > M(-d)); 0.5 = the probe knows nothing
    def auc(sub, ch):
        w = [(r["plus"][ch] > r["minus"][ch]) + 0.5 * (r["plus"][ch] == r["minus"][ch])
             for r in sub]
        return float(np.mean(w)), len(w)

    def boot_ci(sub, ch, n_boot=10000, seed=0):
        rng = np.random.RandomState(seed)
        w = np.array([(r["plus"][ch] > r["minus"][ch])
                      + 0.5 * (r["plus"][ch] == r["minus"][ch]) for r in sub], float)
        b = np.array([w[rng.randint(0, len(w), len(w))].mean() for _ in range(n_boot)])
        return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))

    # Discriminability D = 2|AUC - 0.5| in [0,1]. AUC 0.0 is as much survival as
    # AUC 1.0 -- a perfectly consistent NEGATIVE effect (e.g. advancing the roof
    # phase always DECREASES steps_to_switch) recovers the sign just as well. It is
    # the distance from 0.5, not the direction, that says the mark survived.
    print(f"\n=== survival: discriminability  D = 2|AUC - 0.5|   [0 = sign destroyed]")
    hdr = " ".join(f"{c.split('(')[0][:11]:>12s}" for c in CHANNELS)
    print(f"    {'direction':18s} {hdr}")
    summary = {}
    for name, _b, _i, _d in DIRS:
        sub = [r for r in rows if r["dir"] == name]
        cells, marks = [], {}
        for ch in CHANNELS:
            a, n = auc(sub, ch)
            lo, hi = boot_ci(sub, ch)
            d_disc = 2 * abs(a - 0.5)
            marks[ch] = dict(auc=round(a, 4), D=round(d_disc, 4),
                             ci=[round(lo, 4), round(hi, 4)], n=n)
            star = "*" if (lo > 0.5 or hi < 0.5) else " "
            sgn = "+" if a >= 0.5 else "-"
            cells.append(f"{d_disc:10.3f}{sgn}{star}")
        summary[name] = marks
        print(f"    {name:18s} " + " ".join(cells))
    print("    (sign = direction of the AUC; * = 95% bootstrap CI excludes 0.5)")

    print(f"\n=== survival vs gap  (D, channel: saddle(unshuttered) / steps_to_switch)")
    print(f"    {'direction':18s} " + " ".join(f"{g:>17d}t" for g in st.GAPS))
    for name, _b, _i, _d in DIRS:
        cells = []
        for g in st.GAPS:
            sub = [r for r in rows if r["dir"] == name and r["gap"] == g]
            if not sub:
                cells.append(f"{'--':>18s}")
                continue
            a1, _ = auc(sub, "saddle(unshuttered)")
            a2, _ = auc(sub, "steps_to_switch")
            cells.append(f"{2*abs(a1-0.5):8.3f} /{2*abs(a2-0.5):8.3f}")
        print(f"    {name:18s} " + " ".join(cells))

    (HERE / "out_survival_summary.json").write_text(json.dumps(summary, indent=1))
    print("\n--- reading:")
    print("    A direction SURVIVES if its AUC is reliably above 0.5: the probe, after")
    print("    the gap, still reveals which way it was pushed. tau0 rows reproduce the")
    print("    known null. If tau1_neutral survives while the others do not, the")
    print("    neutral (flow) direction is the only place an input can leave a mark")
    print("    that keeps its identity -- and ears.py has never used it.")
    print(f"\n({time.time()-t0:.0f}s)  raw -> out_survival.json")


if __name__ == "__main__":
    main()
