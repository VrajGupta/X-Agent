# Content studio handoff

## Final state

Local-only delivery; no GitHub Project or push was used.

The studio now reads AlphaSignal's public RSS and optional official X API data, then writes a personalized copy-first dashboard at `out/index.html` and an RSS file at `out/ai-digest.xml`.

## Personalized context

`profile.json` carries Vraj's voice, themes, opinions, projects and avoid rules. It references the skills repo, Lullabook, Media-Agent and Surf Royale.

Each item can show:

- original post
- opinion
- reply
- repost with comment
- source-linked evidence claims
- X public metrics when available
- source image or an image prompt
- copy actions with visible failure state

## Safety and invariants

- no X scraping or undocumented endpoints
- no implicit X write; posting requires explicit CLI flags and a token
- source links are restricted to HTTP/HTTPS
- OAuth is PKCE + state checked + loopback callback only
- cached packs are signature-checked and length-checked
- pending items are FIFO and archive is bounded
- source failures keep prior artifacts and expose source health
- generated claims and metrics retain source URLs
- dashboard uses OKLCH colors, readable measures, monospace metadata and responsive layout

## Verification

```sh
python3 -m unittest -v
python3 ai_digest.py --self-test
python3 -m py_compile ai_digest.py x_auth.py test_ai_digest.py
```

Final run: 19 tests passed, self-test passed, compile passed, RSS parsed, dashboard rendered 50 cards × 4 variants, pending queue 0, invalid visible packs 0.

## Use

```sh
python3 ai_digest.py
open out/index.html
```

Edit `profile.json` to tune the voice and projects. Add X OAuth locally with `python3 x_auth.py` only if official X API access is available. Copy manually from the dashboard by default.
