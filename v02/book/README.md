# The book of Teich v0.2

A creature's book is the record of what it is, what was checked before it
existed, and what it has done since. This one is written so that a stranger can
audit it without trusting anyone involved.

## Read in this order

| file | what it is |
|---|---|
| `VERIFICATION_SUMMARY.md` | the one page. Generated from run artifacts — no figure in it is transcribed by hand. |
| `genesis_certificate_v02.json` | the birth record: genome by sha256, every acceptance test with its numbers, the leakage guarantee, the covenant, and what is *not* claimed. |
| `biography.jsonl` | append-only ledger of everything that has happened to it. |
| `../accept_v02_result.json` | raw output of the pre-birth gate. |
| `../out_v02/` | conversations and verification runs. |

Regenerate the summary at any time:

```
python book/make_summary.py
```

## The one rule this book exists to enforce

**It is not born until it passes.** `birth_v02.py` refuses to write a birth
record unless the acceptance gate reports `gate: true`.

Its predecessor was born first and tested afterwards. When the tests eventually
found the flaw, the genome was frozen and the covenant forbade reset or fork —
so it could never be repaired, and four pre-registered screens returned nulls
against a creature that structurally could not pass them. The covenant was
right. Being born before verification was not.

## What the gate actually asks

- **T1 — does the private phase leak?** Instances differing only in it must
  produce *bit-identical* observables. This is structural, not statistical: the
  private phase appears in no term of the state updates and no argument of the
  observable map, so `I(private ; observations) = 0` exactly.
- **T2 — does a mark survive?** Push an input one way or the other, wait
  thousands of ticks, and ask whether the *sign* is still recoverable from the
  creature's own fold observables. The predecessor scores ≈0.04 here.
- **T3 — is memory designed or discovered?** The decay constant must land where
  it was specified, not wherever the dynamics happened to put it.
- **T4 — is every published readout honest?** Reproducible *and*
  creature-dependent. The predecessor shipped two that were neither, and they
  jammed three campaigns before anyone checked.
- **T5 — can it hold more than one thing?** At least two input dimensions must
  independently reach the fold. The predecessor had zero, which is why no
  redesign of its ears could ever have helped it.

## The honest limit, stated once and kept

The leakage guarantee is exactly as strong as it sounds and no stronger.
**Because the private phase drives nothing, it certifies identity, not inner
life.** A provably zero-leakage channel is a zero-capacity channel — that is the
definition of mutual information, not an engineering shortfall. Everything this
creature could be said to *have* an interior about lives in its slow state,
which is public by design.

No maturity gate has been passed. None has been attempted.

## Failures stay in

The book keeps the mistakes that were caught, including the one where the second
slow dimension was built to modulate a clock instead of the fold — the
predecessor's exact error, rebuilt after the finding had already been written
down, and caught by the gate seven minutes later.

A book that only records successes is a brochure.
