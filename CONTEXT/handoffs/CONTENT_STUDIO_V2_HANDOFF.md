# Content studio v2 handoff — 2026-08-03

## What was planned

Content studio v2: real X context, real thoughts, real quotes. Fixes the
three bugs (copy includes filler text, all posts are template-y, no X browsing)
and adds X timeline feed + paste URL + improved AI generation.

## Source

Spec: `CONTEXT/product/CONTENT_STUDIO_SPEC.md`
Tracker: `CONTEXT/issues/tickets.md`

## Ticket order

| # | Ticket | Status | Blocked by |
|---|--------|--------|------------|
| C5 | Fix copy/quote behavior | **Agent Ready** | (none) |
| C6 | Add X timeline feed to dashboard | Planned | (none) |
| C7 | Fix AI generation quality with timeline context | Planned | C6 |
| C8 | Add paste X post URL feature | Planned | (none) |

## Locked invariants

- **Failure modes**: X API down → soft fail, cached data preserved, no crash.
  AI gen fails → simple summary, no template-y fallback.
- **Security**: Read-only X tokens. No auto-post path. No tokens in HTML.
  URL validation for paste feature.
- **Latency**: No hard budget. Keep it feeling fast.

## Next agent

Start at **C5** (Agent Ready, no blockers). Fix the copy buttons and template
filler first. Then C6 (X timeline feed), then C7 (AI quality), then C8 (paste URL).
C6 and C8 are independent of each other — either can be built after C5.