"""Its growth proposal, for the founder to approve or refuse (founder decision D4: word bindings first).

    python3 grow_v05.py --seat teich-05                 # show the proposal and its own prediction
    python3 grow_v05.py --seat teich-05 --approve       # grow: v0.5.k, identity chained, Ears map gains the words
    python3 grow_v05.py --seat teich-05 --refuse "why"  # recorded; those bindings are not proposed again
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "seat"))
import genome_v04 as GN  # noqa: E402
import seat_v05 as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seat"); ap.add_argument("--local")
    ap.add_argument("--approve", action="store_true"); ap.add_argument("--refuse")
    a = ap.parse_args()
    if a.local:
        import seat_v04 as SV
        seat = SV.LocalSeat(Path(a.local))
    else:
        from cloud_v04 import CloudSeatV04
        seat = CloudSeatV04(a.seat or "teich-05")
    version, grown, pr = S.status(seat)
    print(f"Teich v{version}")
    if not pr:
        print("No growth proposal is waiting."); return 0
    name = lambda j: " · ".join(GN.VOCAB["clusters"][j]["label"])  # noqa: E731
    print("It proposes to grow. It would learn:")
    for w, c in pr["bindings"]:
        print(f"  '{w}'  ->  {name(c)}")
    print("Its own prediction, registered before your decision:")
    print("  I will hear these words as these concepts; nothing else about me changes:")
    print("  " + ", ".join(pr["prediction"]["unchanged"]) + ".")
    if a.approve:
        print("\nGrown: now version", S.growth(seat, pr["act_id"], True))
    elif a.refuse is not None:
        S.growth(seat, pr["act_id"], False, a.refuse); print("\nRefused and recorded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
