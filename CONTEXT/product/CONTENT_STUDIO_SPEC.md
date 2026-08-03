# Content studio v2 — real X context, real thoughts, real quotes

## Status: planned

## What changed

The v1 digest fetches AlphaSignal RSS + optional X search results, runs them
through a template or LLM, and renders a dashboard. The output is formulaic:
same templates, 1-2 words swapped, no real connection to X discussions.

v2 keeps the same sources (AlphaSignal RSS + X API read) but adds:

1. A rendered X timeline feed in the dashboard so you can see what's happening
   on X without leaving the digest
2. A paste-X-post-URL feature to bring any post into the digest
3. Real AI-generated thoughts: the LLM sees your timeline context and produces
   varied, opinionated output instead of fill-in-the-blank templates
4. A draft + edit workflow: AI generates, you review and edit before posting
5. Copy buttons that copy the actual X post text for quoting, **and** the AI
   variant separately — no template filler leaking into your clipboard

## Sources

- **AlphaSignal RSS** — kept as-is, feeds into the same pipeline
- **X API read** — kept as-is for timeline/search. No posting. No auto-post path.
- **X.com manual browsing** — you open X in a separate tab. Paste URLs back into
  the digest to fetch and generate from.

## Invariants

### Latency / performance

No hard budget. Keep uncached X API calls under ~2s, AI generation under ~10s.
Dashboard loads from local file, no server needed.

### Failure modes

- X API is down/rate-limited → soft fail: the dashboard still renders with
  cached/AlphaSignal data. No crash. The X section shows "unavailable."
- AI generation fails → fallback to a simple summary (no template-y variants).
- A single post fetch fails → the rest of the dashboard is unaffected.
- Invalid/malformed X post URL → clear error message, not a crash.

### Security / permission boundaries

- X tokens are read-only (timeline + search). No write scope.
- No auto-post path. Ever. Posting requires explicit CLI flags + token.
- No X scraping or undocumented endpoints.
- No OAuth token stored in the dashboard HTML.
- Paste URL input is validated (must be an x.com or twitter.com URL).

## Dashboard layout

Single HTML file. New sections added:

1. **X timeline feed** — a scrollable section showing recent posts from your
   timeline. Each post shows: author, text, metrics (likes/retweets), timestamp.
   Click a post to select it for content generation.
2. **Existing AlphaSignal cards** — unchanged, still show below the X feed.
3. **Paste URL input** — a text field at the top to paste an X post URL.
   Fetches and displays the post, ready to generate from.
4. **Copy buttons** — each post has two copy buttons:
   - "copy post text" — copies the real X post text + URL
   - "copy AI variant" — copies the AI-generated variant (post/opinion/reply/repost)
5. **Draft + edit** — AI-generated variants show as editable text areas, not
   read-only snippets. Edit before copying.

## AI generation changes

- LLM prompt includes the user's recent timeline context (last ~20 posts)
- Prompt is less prescriptive — no "keep under 240 chars" instructions
- No hardcoded fallback templates. If LLM is unavailable, show a simple summary.
- Generate varied structures: sometimes a hot take, sometimes a question,
  sometimes a thread idea, not always "post/opinion/reply/repost" quadrants