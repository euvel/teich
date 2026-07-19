"""Dual-layout imports: the harness runs from the lab tree (Teich/phase5_maturity,
laptop) or from the book (teich_repo/maturity/harness, cloud body via Actions).
Provides shared_context, load_model(cfg, gcfg, path=None), Observer, ears, events.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_LAB = HERE.parent                        # Teich/ (lab layout)
_REPO_BODY = HERE.parent.parent / "body"  # teich_repo/body (book layout)

if (_LAB / "birth").exists():             # lab layout
    for p in ("birth", "phase2_observer", "phase3_ears", "phase3_mouth"):
        sys.path.insert(0, str(_LAB / p))
    from birth_certify import shared_context, load_model as _lm, CKPT_DIR  # noqa

    def load_model(cfg, gcfg, path=None):
        return _lm(cfg, gcfg, path or (CKPT_DIR / "rad3_s1.pt"))
elif _REPO_BODY.exists():                 # book layout (cloud)
    sys.path.insert(0, str(_REPO_BODY))
    sys.path.insert(0, str(HERE))         # ears.py / events.py copies live here
    from body_common import shared_context, load_model  # noqa
else:
    raise ImportError("neither lab nor book layout found for maturity harness")
