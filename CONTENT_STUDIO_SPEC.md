# Vraj content studio

## Goal

Turn AI/news source items into copy-ready, opinionated content that sounds like Vraj: casual, technical, lowercase-friendly, evidence-led, and connected to the projects he is actually building.

## Scope

The local Python job fetches AlphaSignal and optional official X API items, then writes:

- `out/ai-digest.xml` for RSS
- `out/index.html` for review and copy/paste
- `out/state.json` for idempotent local state

The page shows an original post, opinion, reply, repost comment, source evidence, stats, and an image idea for each featured item. It never scrapes X, bypasses authentication, or posts without an explicit user action.

## Profile context

The seeded context is based on Vraj's public/local work:

- `VrajGupta/skills` — developer skills, explicit invariants, simple implementations, testable gates
- `VrajGupta/Lullabook` — product engineering and structured systems
- `VrajGupta/Surf-Royale` — game building and interaction design
- `VrajGupta/Media-Agent` — automation and media workflows

## Invariants

1. **Attribution:** every source-backed variant keeps a source URL in the card; extracted stats show their source.
2. **No invented evidence:** deterministic fallback stats come only from source text or X public metrics; missing stats are labeled unavailable.
3. **Length:** every copyable X variant is at most 280 Python characters and is visibly marked if it is a fallback.
4. **Safety:** only `http` and `https` source URLs become links; generated text is HTML-escaped.
5. **Degradation:** AlphaSignal, X, and the language model fail independently; existing artifacts remain usable.
6. **Consent:** the studio is copy-first. No background X write path is used by the dashboard.
7. **Typography:** body text stays readable at 16px with a capped measure; metadata uses monospace and tabular numbers.
8. **Color:** the UI uses a restrained OKLCH blue-slate palette with readable text contrast.

## Verification command

```sh
python3 -m unittest -v && python3 ai_digest.py --self-test && python3 -m py_compile ai_digest.py x_auth.py test_ai_digest.py
```
