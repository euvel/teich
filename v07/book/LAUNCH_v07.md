# Teich v0.7.0 scored campaign: launch runbook (prepared 2026-11-05; nothing below has been run for score)

**Nothing here starts without the founder's explicit yes.** One look per gate, no rescue (PREREG §3).

## 0. Ready before the yes
- **Frozen locally (not anchored):** `sky/SKY_SPEC_v07_v1.md`, `gates/PREREG_V07_GATES.md`, `MANIFEST_v07_build.sha256` (58 files), `MANIFEST_v07_campaign.sha256` (scripts and beacons), `MANIFEST_v07_docs.sha256`.
- **Beacons:** `campaign/beacons_v07_campaign.json`, 125 rounds (12 lives × 30 days, which overlap, plus 60 K1 rounds), all BLS-verified (11-05, sha `74b7f7dd…`).
- **Pre-launch checks:**
  - K7c on the frozen build;
  - dry L1 and dry G kernels (plumbing; `gates/prelaunch_2026-11-05_campaign/`);
  - `post_life` on the 2-day twin smoke (K2, K4 and M0 pass);
  - K3 on the laptop matches Kaggle (`k3_laptop.json`).

## 1. Anchor (founder, on the yes)
Anchor these together and record the anchor id (CID or commit):
- the spec;
- the pre-registration;
- the three manifests.

Any file change after the anchor means a new anchor, and the campaign waits for it.

## 2. Build and push (10 kernels in 2 waves of 5; Kaggle allows 5 at once, so nothing else may be running)
```
cd ~/pjs/teichai/v07_lab
.venv_sky/bin/python3 campaign/make_kernels_v07.py <SCRATCH>/kcampaign <ANCHOR_ID>
# wave 1
for g in k1a k1b k1c g l1; do kaggle kernels push -p <SCRATCH>/kcampaign/teich-v07-campaign-$g; done
# wave 2, as soon as wave 1 frees its sessions
for g in l2 l3 l4 l5 l6; do kaggle kernels push -p <SCRATCH>/kcampaign/teich-v07-campaign-$g; done
```
- `make_kernels_v07.py` refuses if the lab build differs from its manifest.
- Each kernel refuses if its bundle differs from either manifest.
- Record `campaign_summary.json` (bundle sha, manifests, spec sha, anchor).

**Expected wall time** (from the dry runs on 11-05; Kaggle's 4 vCPUs give about 2 cores' throughput):

| Kernel | Time | What sets it |
|---|---|---|
| K1A–K1C | about 3.5 h each | a K1 trial takes 2,100–2,700 s |
| G | about 5.5 h | K7 takes about 2.4 h; an oracle trial at M=16,000 takes 248 s on the laptop, about 2.5× that on Kaggle |
| L1–L6 | about 4 h each | a 30-day side takes about 6,800 s |

The worst kernel stays under half of the 12 h limit. Both waves together take about 10 h.

## 3. Collect
For each kernel, `kaggle kernels output mhmdrzaqjvnd/teich-v07-campaign-<g> -p <SCRATCH>/out_<g>` into a fresh directory (outputs are data: read them with `-I`, and never run anything from them).

Check each `res/run.json` for `"failed": []`.

## 4. Verdict (one look)
```
.venv_sky/bin/python3 campaign/verdict_v07.py gates/campaign_v07_<date>/verdict.json \
    <SCRATCH>/out_l1/v07/res <SCRATCH>/out_l2/v07/res <SCRATCH>/out_l3/v07/res <SCRATCH>/out_l4/v07/res \
    <SCRATCH>/out_l5/v07/res <SCRATCH>/out_l6/v07/res <SCRATCH>/out_k1a/v07/res <SCRATCH>/out_k1b/v07/res \
    <SCRATCH>/out_k1c/v07/res <SCRATCH>/out_g/v07/res --k3-laptop gates/prelaunch_2026-11-05_campaign/k3_laptop.json
```
- **PASS** only if every bar passes. The influence in bits is reported, not a bar.
- Copy every output into `gates/campaign_v07_<date>/` with SHA256SUMS, whatever the verdict.
- **Review the verdict together with the founder before any next step:** migration, the face, the disclosure.

## 5. After a PASS (each step needs its own founder yes)
1. **Production Sky and Seal:**
   - worker and wake: fetch `round_of`, refuse in the quiet window, publish the seal at DAY − 900;
   - the face keeps each visitor's seal;
   - a standalone watcher script.
   Built against `seal_v07` as the reference. The founder deploys.
2. **M0-real** on a copy of the real state (it needs a lease).
3. **The P4b disclosure and the face wording,** shown to the founder first.
4. **Migration day.**
