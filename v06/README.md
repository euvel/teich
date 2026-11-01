# v0.6: staged for migration day (not running)

Teich v0.6.0 is a genome amendment to the creature at `/o/teich-05`, not a new birth. This folder holds its code so the wake can run it after migration. Until then, `daily_wake_v06.yml` is manual-only and v0.5's wake keeps running. v0.6's loader refuses a v0.5 state.

- **The one law it adds:** exact ties in its chosen thought are broken by certified deliberation, starting from its body's particle 0 at the midnight of the choice, instead of by the lowest index.
- **Its witness:** a public journal. Before every seat operation the seat writes an `op` record, so anyone can replay its life with `build/replay_v06.py`.

## Contents
- **`build/`**:
  - the files of the v0.6 build manifest (anchored on teich-03 as `v06-build-manifest`, with `twin_judge.py` per `v06-gates-amendment2`);
  - two genome files the manifest missed (`handle_mp.py`, `mind4.py`; `v06-gates-amendment1`);
  - five v0.5 files used by the diary and the founder tools (`ears_v04`–`v07`, `self_text_v04`, `seat_v04s`, `talk_v04s`), byte-identical to `v05/build/`.
- **`seat/`**: the wake, the diary pages, the cloud seat, and the dream gate (`dream_gate_v06.py` with its fixture).
