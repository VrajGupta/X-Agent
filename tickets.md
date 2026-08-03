# Local content studio tracker

No GitHub Project is used for this workspace.

## C1 — profile-aware content packs

**Status:** Done (local part 2 build)

**Build:** Add profile context and generate original, opinion, reply and repost-comment variants with a deterministic fallback.

**Acceptance:** Profile context changes output; every variant is copyable and <=280 chars; source URL remains attached.

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test`

## C2 — evidence and media

**Status:** Done (local part 2 build)

**Blocked by:** C1

**Build:** Preserve source images, extracted numeric claims, public metrics and image suggestions.

**Acceptance:** Stats have source provenance; unsafe links are not clickable; missing evidence is labeled.

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test`

## C3 — review studio UI

**Status:** Done (local part 2 build)

**Blocked by:** C1, C2

**Build:** Replace the flat list with a personalized dashboard using OKLCH color tokens, readable typography, content-pack sections, filters and copy actions.

**Acceptance:** Page works from `file://`, responsive cards render, copy failures are visible, and no generated HTML is unescaped.

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test && python3 -m py_compile ai_digest.py x_auth.py test_ai_digest.py`

## C4 — hardening and grade

**Status:** Done (local part 4 grade PASS; final score 87/100)

**Blocked by:** C3

**Build:** Cover namespaced feeds, malformed providers, state consistency, unsafe URLs, unicode limits and stale-source behavior.

**Acceptance:** The verification command is green; failures do not erase usable prior artifacts; no auto-post path is added.

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test && python3 -m py_compile ai_digest.py x_auth.py test_ai_digest.py`
