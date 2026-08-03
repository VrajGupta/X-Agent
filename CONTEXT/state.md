# state — what survives between sessions

Short-lived working memory. Read at session start and write at session end.
When a fact becomes durable truth, move it into a real node and remove it here.

## Now

- 2026-08-03: Part3 hardened C5, C6, C7, C8 with parallel C5/C6/C8 workers and a serial C7 worker. Four commits are on `part3-x-agent-hardening`; a concurrent independent part4 pass then graded all four PASS and moved them to Done. 46 tests, self-test, compile, graph, and generated-JavaScript checks pass. C8's static-dashboard localhost-service follow-up is recorded on issue #8 and the part3 handoff.
