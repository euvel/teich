"""Live verify for Teich v0.5 — anyone can run this on its published life log.

For every act the creature chose (ask, stay silent, probe, caution, …) it checks, from the log alone:
  completeness  the act's reason was written before the act, and every reason has its act
  receipt       the named rule, given only the logged reason, computes exactly the logged act
  consequence   the act is what the creature then actually did
  necessity     moving the reason across the rule's documented boundary changes the act as documented
Rules are part of the genome (acts_v05.py); nothing else is needed.
    python3 verify_live_v05.py LOG.jsonl          (one record per line, as published)
    python3 verify_live_v05.py --seat teich-05    (reads the seat's public record log)
"""
import json
import sys

from f1_v05 import check_log


def main():
    if sys.argv[1] == "--seat":
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "seat"))
        from cloud_v04 import CloudSeatV04
        recs = [r["rec"] for r in CloudSeatV04(sys.argv[2]).log_read()]
    else:
        recs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    f = check_log(recs)
    bad = f["completeness"] + f["receipt"] + f["consequence"] + f["necessity"]
    print(json.dumps(f, indent=1))
    print(f"\n{f['acts']} acts checked: " + ("every reason is the act's true cause." if bad == 0 else f"{bad} FAILURES."))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
