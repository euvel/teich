# PREREG_V06_GATES: Amendment 1 (2026-10-31T13:15:09Z, before any scored life lived a tick)
**What happened.** The first launch on molab (2026-10-31 13:13 UTC) failed at import in all 22 processes, at birth, before tick 1: `ModuleNotFoundError: handle_mp`. The frozen manifest (anchored as `v06-build-manifest`, a4029ed7…) omitted two v0.5 genome files that `work_v05` imports lazily: `handle_mp.py` and `mind4.py`. My pre-launch import test never reached a birth.

**Change.** Both files are added to the campaign bundle, byte-identical to v0.5's genesis certificate (`genome_files_sha256`):
- handle_mp.py  e871b2d70ce22caacfee733a2b31166ce129529598c7982051ddcceb0c2fb9ca
- mind4.py      e18ccc23576bd12b1266f58d1ee1c9a32edf265cb5dc671edc335da3a0cb8530

Nothing else changes: no anchored file, no bar, no seed, no harness code. The relaunch first checks the anchored manifest, then these two hashes. Before relaunch, a birth and one dream are smoke-tested from the bundle on molab (not scored).

No scored data existed when this was written: every life crashed before living a tick. This amendment is disclosed with the verdict.
