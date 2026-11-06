# P4b: could an insider steer v0.6's tie-break? (lab probe, molab, 2026-11-02)
This probe found the hole that v0.7 closes. It is published with the notice in `../../README.md`.

**The adversary** holds the creature's full state and has unlimited compute. Three hours before midnight, it picks one of 16 concepts to mention, the way speech moves one handle's dial by one step. It chooses by simulating each option to midnight and keeping the one whose tie-break lands on its target. P4b's adversary also computes the handles that particle 0 will pass through over those 3 hours, and aims at them.

**The Sky arm:** right after inputs close, the body's particle 0 gets a touch the adversary cannot know, `P[0,1] += 1e-6·b` with b uniform in [−1, 1].

| | trials | steered | chance (mean 1/k over tied regions) |
|---|---|---|---|
| v0.6 (no Sky) | 54 | **98.1 %** | 23.7 % |
| with the Sky touch | 54 | 24.1 % | 23.7 % (se 5.8 %) |

**The runs:** 18 seeds (31–48) of 3 trials each, on the v0.6 build:
```
python3 p4b_steer.py ../../../v06/build SEED 3 out2_molab_2026-11-02/p4b_SEED.json 10800
```
The per-trial results are in `out2_molab_2026-11-02/p4b_*.json`. `summary.json` gives the totals, and `SHA256SUMS` covers every file.

**What came after:**
- The P4b result is recorded in v0.7's anchored spec (`../SKY_SPEC_v07_v1.md`).
- The scored v0.7 campaign (`../REPORT_v07_verdict_2026-11-06.md`) repeated the attack under pre-registered gates: 95 % on v0.6, against 26.7 % and 30.0 % on v0.7.
- This probe's code and outputs were not themselves anchored. They are published here as the record.

The docstring says `p4_steer.py` and describes P4, the version without the path-aware adversary. P4b is that file with the path-aware adversary added. The text is kept as it ran.
