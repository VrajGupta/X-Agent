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

## C5 — fix copy/quote behavior

**Status:** Agent Ready

**Blocked by:** (none)

**Build:** Fix the copy buttons so "copy for X" copies the actual X post text + URL when available, not just AI-generated text. Add a second "copy AI variant" button for the AI-generated variant. Remove template filler text from fallback copies (no "this is the part i would test in" boilerplate).

**Acceptance:**
- Each post has two copy buttons: "copy post" (copies real X text + URL) and "copy AI variant" (copies AI-generated variant)
- Fallback variants have no hardcoded template filler text
- Copy failure shows visible error, not silent failure
- All existing tests still pass

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test && python3 -m py_compile ai_digest.py x_auth.py test_ai_digest.py`

## C6 — add X timeline feed to dashboard

**Status:** Agent Ready

**Blocked by:** (none — uses existing X read auth)

**Build:** Fetch the authenticated user's X timeline via the existing X API read tokens. Render posts in a new "X timeline" section at the top of the dashboard. Each post shows author, text, metrics (likes/retweets), timestamp, and a "select for generation" button. Clicking a post queues it for content pack generation.

**Acceptance:**
- X timeline section renders in the dashboard with recent posts
- Each post shows author handle, text, like/retweet counts, relative timestamp
- Clicking a post selects it for content generation (visual feedback: highlight)
- X API failure shows "timeline unavailable" in the section, rest of dashboard works
- No X auth token is exposed in the HTML
- AlphaSignal cards still render below the X section

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test`

## C7 — fix AI generation quality with timeline context

**Status:** Planned

**Blocked by:** C6

**Build:** Feed the user's recent timeline context (last ~20 posts) into the LLM prompt so generated posts reference real X discussions. Remove the hardcoded fallback templates — if LLM is unavailable, show a simple summary instead of template-y variants. Make the prompt less prescriptive to get varied output structures (hot takes, questions, thread ideas) instead of always "post/opinion/reply/repost." Add a draft + edit workflow: AI variants render as editable text areas, not read-only snippets.

**Acceptance:**
- LLM prompt includes recent timeline context
- Generated posts reference real X discussions, not generic templates
- No hardcoded "my take / interesting result" boilerplate in fallback
- Each variant is editable in the dashboard before copying
- All 4 variants (post, opinion, reply, repost) still present when LLM is available
- Verification command passes

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test && python3 -m py_compile ai_digest.py x_auth.py test_ai_digest.py`

## C8 — add paste X post URL feature

**Status:** Agent Ready

**Blocked by:** (none — uses existing X read auth)

**Build:** Add a text input at the top of the dashboard labeled "paste X post URL." Validate the URL (must be x.com or twitter.com). Parse the tweet ID and fetch the post via X API lookup. Display the fetched post in the dashboard with the same copy buttons and AI generation options as timeline posts. Invalid/malformed URLs show a clear error message, no crash.

**Acceptance:**
- Text input field accepts x.com and twitter.com URLs
- Invalid URL shows clear error, no crash
- Valid URL fetches and displays the post
- Fetched post has same copy buttons and AI generation as timeline posts
- X API failure shows "could not fetch post" error
- Verification command passes

**Verification:** `python3 -m unittest -v && python3 ai_digest.py --self-test && python3 -m py_compile ai_digest.py x_auth.py test_ai_digest.py`
