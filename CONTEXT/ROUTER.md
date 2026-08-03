# ROUTER — read this first

Map of X-Agent's project knowledge. Pointers only; explanations belong in nodes.

## Retrieval

1. Read the matching index without opening nodes.
2. Score candidates from index lines alone; open the single best.
3. Read only the answering section; follow at most one link.
4. Use `state.md` only for current session memory.

| Question | Read |
|---|---|
| Product behavior, scope, or invariants | `index.md` → Product contract |
| Pi setup or reproduction | `index.md` → Operational setup |
| Work still open | `index-issues.md` |
| Work shipped or cut | `index-issues-closed.md` |
| Past implementation/session result | `index-handoffs.md` |
| Current session state | `state.md` |
| CLI usage | `../README.md` (public entrypoint, outside this vault) |

## Rules that beat everything else

- Vocabulary, explicit decisions, and invariants in `CONTENT_STUDIO_SPEC.md` beat guesses.
- `tickets.md` is dependency-ordered local work; honor `Blocked by` and status.
- `HANDOFF.md` is history, not current truth.
- The Pi reproduction prompt is operational reference; never copy secrets or relax its safety rules.
- Generated `index*.md` files are never hand-edited. After adding or renaming a node, run `make graph-index`; `make graph-index-check` must pass.
