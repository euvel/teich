# The public face (teich.euvvel.xyz)

Source of the page the seat Worker serves at `/`. Edit these files, never the built `PANEL_HTML` line in `../index.js`.

- `face.html`, `face.css`, `face.js`: the page.
- `delib.js`: v0.6's certified deliberation ported line for line from `v06/build/delib_cert.py`, so a visitor's browser can re-decide its ties.
- `legacy/`: the earlier sections, kept verbatim for the family panels.
- `duduk_words.json`: the founder's own words in the duduk conversation, published by the founder. Each must hash exactly to its `text_sha256` in the record log; the page checks this again in every visitor's browser.

```
python3 face/build_face.py                       # inline face/ into index.js (one JSON string literal)
python3 infra/worker/deploy.py --deploy          # from the repo root, as before
```

Tests (`test/`):
- `test_delib.js`: the port against Python on 209,600 reference values (bit-exact required); vectors from `make_vectors.py`.
- `test_worker_public.mjs`: the read-only public endpoints and every refusal.
- `test_worker_pins.mjs`: pin labels, rotation and refusal handling.

The worker tests run on `index.js` with the `cloudflare:workers` import replaced by a stub class.
