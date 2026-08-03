# state — what survives between sessions

Short-lived working memory. Read at session start and write at session end.
When a fact becomes durable truth, move it into a real node and remove it here.

## Now

- 2026-08-03 inventory: the repo held five written Markdown files; four project knowledge nodes now live under `CONTEXT/`, while the public `README.md` remains the repo entrypoint outside the vault.
- Vault scope is `CONTEXT/`: 4/4 indexable files are signal (100%); there are no nested `docs/` or `plans/` name collisions, and generated links stay vault-relative.

## Recently tried

- Retrieval benchmark (2026-08-03). Raw means all four nodes; graph means `ROUTER.md`, the matching generated index, and the single best node. Token estimate is measured UTF-8 bytes ÷ 4, rounded up.

  | question | raw tokens / files | graph tokens / files | answer |
  |---|---:|---:|---|
  | product contract and invariants | 10,113 / 4 | 978 / 3 | correct |
  | current work status and dependencies | 10,113 / 4 | 866 / 3 | correct |
  | latest handoff result | 10,113 / 4 | 831 / 3 | correct |
  | **total** | **30,339 / 12** | **2,675 / 9** | **correct** |

  This sample reduced measured context bytes by 91.2%; it is a small proof, not a universal guarantee.

## Dead ends — do not retry

- The repository had no `CONTEXT/` directory, so the existing written docs were reorganized into the vault instead of reading a nonexistent folder.

## Open questions

- Unproven: does the graph preserve answer correctness for questions outside the three benchmark questions? Re-run the benchmark after meaningful node or index changes.
