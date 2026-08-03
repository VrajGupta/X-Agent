import html
import json
import os
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from datetime import datetime, timedelta, timezone

from ai_digest import Item, clean_text, clip_post, collect, fallback_pack, fetch_x_post_by_url, fetch_x_timeline, item_signature, make_content_pack, pack_is_valid, parse_alpha_signal, parse_x_post_url, parse_x_response, render_dashboard, render_paste_section, render_x_timeline_section, render_rss, to_post_text, variant_for, x_weighted_length
from x_auth import pkce_values, refresh_user_token, upsert_env, validate_redirect_uri


FEED = b'''<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>AlphaSignal</title>
    <item>
      <title>Agents &amp; tools</title>
      <link>https://example.com/agent</link>
      <guid>agent-1</guid>
      <pubDate>Sat, 01 Aug 2026 14:38:57 GMT</pubDate>
      <description>Tools &amp; memory for agents</description>
      <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Alpha</dc:creator>
    </item>
  </channel>
</rss>'''

NAMESPACED_FEED = b'''<rss xmlns="urn:rss"><channel><item>
<title>Nested &amp; useful</title><link>https://example.com/nested</link><guid>nested-1</guid>
<description>before <b>bold</b> after 25%</description><pubDate>Sat, 01 Aug 2026 14:38:57 GMT</pubDate>
</item></channel></rss>'''

UPDATED_FEED = FEED.replace(b"Tools &amp; memory for agents", b"Tools &amp; memory for agents now 40% faster")
EMPTY_FEED = b"<rss><channel /></rss>"
TITLE_UPDATED_FEED = FEED.replace(b"Agents &amp; tools", b"Updated agents &amp; tools")


def many_item_feed(count):
    items = "".join(
        f"<item><title>Item {index}</title><link>https://example.com/{index}</link><guid>item-{index}</guid><pubDate>Sat, 01 Aug 2026 14:{index:02d}:00 GMT</pubDate><description>item {index}</description></item>"
        for index in range(count)
    )
    return f"<rss><channel>{items}</channel></rss>".encode()


TIMELINE_ME = b'{"data":{"id":"42","username":"vraj","name":"Vraj"}}'
TIMELINE_PAYLOAD = b'{"data":[{"id":"t1","text":"agents getting faster","author_id":"42","created_at":"2026-08-01T14:38:57Z","public_metrics":{"like_count":7,"retweet_count":3}}],"includes":{"users":[{"id":"42","username":"vraj"}]}}'


class DigestTests(unittest.TestCase):
    def test_clean_text_removes_markup_and_collapses_space(self):
        self.assertEqual(clean_text("<p>Hello&nbsp; <b>world</b></p>"), "Hello world")

    def test_parse_alpha_signal_item(self):
        item = parse_alpha_signal(FEED)[0]
        self.assertEqual(item.id, "alpha:agent-1")
        self.assertEqual(item.title, "Agents & tools")
        self.assertEqual(item.author, "Alpha")

    def test_parse_namespaced_nested_feed(self):
        item = parse_alpha_signal(NAMESPACED_FEED)[0]
        self.assertEqual(item.description, "before bold after 25%")
        self.assertEqual(item.claims, ("before bold after 25%",))

    def test_render_rss_escapes_content(self):
        item = Item(
            id="x:1",
            source="X",
            title="a < b",
            description="plain summary",
            url="https://x.com/example/status/1?a=1&b=2",
            published_at="2026-08-01T14:38:57+00:00",
        )
        rss = render_rss([item])
        self.assertIn("a &lt; b", rss)
        self.assertIn("a=1&amp;b=2", rss)

    def test_render_dashboard_contains_copyable_post(self):
        item = Item(
            id="x:1",
            source="X",
            title="a useful update",
            description="plain summary",
            url="https://x.com/example/status/1",
            published_at="2026-08-01T14:38:57+00:00",
        )
        dashboard = render_dashboard([item])
        self.assertIn("copyPost", dashboard)
        self.assertIn("a useful update", dashboard)
        self.assertIn("https://x.com/example/status/1", dashboard)

    def test_pending_items_are_promoted_fifo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {
                "alpha_signal_feed": "https://example.com/feed.xml",
                "x_queries": [],
                "output_file": str(root / "feed.xml"),
                "dashboard_file": str(root / "index.html"),
                "state_file": str(root / "state.json"),
                "profile_file": str(root / "profile.json"),
                "max_new_items_per_run": 5,
                "max_feed_items": 50,
            }
            with patch("ai_digest.request_bytes", return_value=many_item_feed(20)):
                for _ in range(6):
                    _, state = collect(config)
            completed = {item["id"] for item in [*state["items"], *state["archive_items"]]}
            self.assertIn("alpha:item-0", completed)
            self.assertEqual(state["pending_items"], [])

    def test_collect_repairs_invalid_cached_pack_without_source_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = Item("alpha:old", "AlphaSignal", "old title", "old summary", "https://example.com/old", "2026-08-01T14:38:57+00:00")
            (root / "state.json").write_text(json.dumps({"items": [asdict(item)], "archive_items": [], "pending_items": [], "posted_ids": []}))
            config = {"alpha_signal_feed": "https://example.com/feed.xml", "x_queries": [], "output_file": str(root / "feed.xml"), "dashboard_file": str(root / "index.html"), "state_file": str(root / "state.json"), "profile_file": str(root / "profile.json"), "max_new_items_per_run": 10, "max_feed_items": 50}
            with patch("ai_digest.request_bytes", return_value=EMPTY_FEED):
                _, state = collect(config)
            self.assertTrue(state["items"][0]["pack"])

    def test_collect_refreshes_title_only_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"alpha_signal_feed": "https://example.com/feed.xml", "x_queries": [], "output_file": str(root / "feed.xml"), "dashboard_file": str(root / "index.html"), "state_file": str(root / "state.json"), "profile_file": str(root / "profile.json"), "max_new_items_per_run": 10, "max_feed_items": 50}
            with patch("ai_digest.request_bytes", side_effect=[FEED, TITLE_UPDATED_FEED]):
                collect(config)
                _, state = collect(config)
            self.assertIn("Updated agents", state["items"][0]["pack"]["variants"][0]["text"])

    def test_cached_overlong_pack_is_rejected(self):
        item = Item("x:1", "X", "title", "summary", "https://x.com/a", "2026-08-01T14:38:57+00:00")
        bad = {"source_signature": item_signature(item), "variants": [{"kind": kind, "text": "🙂" * 200} for kind in ("post", "opinion", "reply", "repost")]}
        cached = replace(item, pack=bad)
        self.assertFalse(pack_is_valid(bad, item))
        self.assertLessEqual(x_weighted_length(variant_for(cached, {"projects": [], "opinions": []}, "post")), 280)

    def test_collect_refreshes_changed_source_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {
                "alpha_signal_feed": "https://example.com/feed.xml",
                "x_queries": [],
                "output_file": str(root / "feed.xml"),
                "dashboard_file": str(root / "index.html"),
                "state_file": str(root / "state.json"),
                "profile_file": str(root / "profile.json"),
                "max_new_items_per_run": 10,
                "max_feed_items": 50,
            }
            with patch("ai_digest.request_bytes", side_effect=[FEED, UPDATED_FEED]):
                collect(config)
                _, state = collect(config)
            self.assertIn("40% faster", state["items"][0]["summary"])

    def test_empty_profile_lists_use_safe_fallbacks(self):
        item = Item("x:1", "X", "title", "summary", "https://x.com/a", "2026-08-01T14:38:57+00:00")
        pack = fallback_pack(item, {"projects": [], "opinions": []})
        self.assertTrue(pack["variants"][1]["text"])

    def test_dashboard_rejects_unsafe_source_links_and_accepts_custom_title(self):
        item = Item("x:1", "X", "unsafe", "summary", "javascript:alert(1)", "2026-08-01T14:38:57+00:00")
        dashboard = render_dashboard([item], title="custom digest")
        self.assertIn("custom digest", dashboard)
        self.assertNotIn("javascript:", dashboard)

    def test_fallback_pack_is_simple_and_source_grounded(self):
        profile = {"projects": [{"name": "template project"}], "opinions": ["generic profile opinion"]}
        item = Item("x:1", "X", "title", "source summary", "https://x.com/a", "2026-08-01T14:38:57+00:00")
        variants = {variant["kind"]: variant["text"] for variant in fallback_pack(item, profile)["variants"]}
        self.assertEqual(variants["post"], clip_post("title\n\nsource summary", item.url))
        self.assertEqual(variants["opinion"], "source summary")
        self.assertEqual(variants["reply"], "source summary")
        self.assertEqual(variants["repost"], clip_post("source summary", item.url))
        self.assertNotIn("generic profile opinion", "".join(variants.values()))
        self.assertNotIn("template project", "".join(variants.values()))

    def test_fallback_pack_does_not_duplicate_identical_title_and_summary(self):
        item = Item("x:1", "X", "same source text", "same source text", "https://x.com/a", "2026-08-01T14:38:57+00:00")
        post = fallback_pack(item, {})["variants"][0]["text"]
        self.assertEqual(post, clip_post("same source text", item.url))

    def test_x_metrics_and_media_are_preserved(self):
        payload = b'''{"data":[{"id":"1","text":"new model 20% faster","author_id":"u","created_at":"2026-08-01T14:38:57Z","public_metrics":{"like_count":4},"attachments":{"media_keys":["m"]}}],"includes":{"users":[{"id":"u","username":"vraj"}],"media":[{"media_key":"m","type":"photo","url":"https://img.example/a.png"}]}}'''
        item = parse_x_response(payload)[0]
        self.assertEqual(item.metrics["like_count"], 4)
        self.assertEqual(item.image_url, "https://img.example/a.png")

    def test_redirect_uri_stays_on_loopback(self):
        self.assertEqual(validate_redirect_uri("http://127.0.0.1:8765/callback"), "http://127.0.0.1:8765/callback")
        with self.assertRaises(RuntimeError):
            validate_redirect_uri("https://example.com:443/callback")
        with self.assertRaises(RuntimeError):
            validate_redirect_uri("http://0.0.0.0:8765/callback")
        with self.assertRaises(RuntimeError):
            validate_redirect_uri("http://127.0.0.1:8765/other")

    def test_post_text_stays_within_x_limit(self):
        item = Item(
            id="x:1",
            source="X",
            title="A useful title",
            description="x" * 500,
            url="https://x.com/example/status/1",
            published_at="2026-08-01T14:38:57+00:00",
        )
        text = to_post_text(item)
        self.assertLessEqual(len(text), 280)
        self.assertTrue(text.endswith(item.url))
        unicode_post = clip_post("🙂" * 500, item.url)
        self.assertLessEqual(sum(2 if ord(character) > 0x7F else 1 for character in unicode_post), 280)
        self.assertEqual(clip_post("text", "javascript:alert(1)"), "text")

    def test_pkce_values_are_url_safe(self):
        verifier, challenge = pkce_values()
        self.assertEqual(len(verifier), 64)
        self.assertEqual(len(challenge), 43)
        self.assertNotIn("=", verifier + challenge)

    def test_malformed_expiry_does_not_crash_refresh_check(self):
        with patch.dict(os.environ, {"X_USER_ACCESS_TOKEN": "token", "X_ACCESS_TOKEN_EXPIRES_AT": "bad"}, clear=True):
            self.assertEqual(refresh_user_token(), "token")

    def test_fetch_x_timeline_resolves_me_then_timeline(self):
        calls = []

        def fake_request_bytes(url, headers=None, method="GET", body=None, timeout=None):
            calls.append((url, headers, timeout))
            return TIMELINE_ME if "/users/me" in url else TIMELINE_PAYLOAD

        with patch("ai_digest.request_bytes", side_effect=fake_request_bytes):
            items = fetch_x_timeline("secret-token", max_results=20)
        self.assertEqual(len(calls), 2)
        me_url, timeline_url = calls[0][0], calls[1][0]
        self.assertIn("/users/me", me_url)
        self.assertIn("/users/42/timelines/reverse_chronological", timeline_url)
        self.assertIn("max_results=20", timeline_url)
        for _, headers, timeout in calls:
            self.assertEqual(headers["Authorization"], "Bearer secret-token")
            self.assertEqual(timeout, 2)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "x:t1")
        self.assertEqual(items[0].metrics["like_count"], 7)

    def test_fetch_x_timeline_rejects_garbage_and_deduplicates_posts(self):
        for payload in (b"{}", b'{"meta":[]}', b'{"data":{}}', b'{"data":[{}]}'):
            with self.subTest(payload=payload), patch("ai_digest.request_bytes", side_effect=[TIMELINE_ME, payload]):
                with self.assertRaises(RuntimeError):
                    fetch_x_timeline("token")

        duplicate_payload = json.loads(TIMELINE_PAYLOAD)
        duplicate_payload["data"].append(duplicate_payload["data"][0])
        with patch("ai_digest.request_bytes", side_effect=[TIMELINE_ME, json.dumps(duplicate_payload).encode()]):
            items = fetch_x_timeline("token")
        self.assertEqual([item.id for item in items], ["x:t1"])

    def test_render_x_timeline_section_shows_unavailable_when_none(self):
        self.assertIn("timeline unavailable", render_x_timeline_section(None))

    def test_render_x_timeline_section_escapes_and_defaults_metrics(self):
        item = Item("x:1", "X", "title", "<script>alert(1)</script>", "https://x.com/i/status/1", "bad", author="@user")
        dashboard = render_x_timeline_section([item])
        self.assertNotIn("<script>", dashboard)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", dashboard)
        self.assertIn("0 likes · 0 reposts", dashboard)

    def test_dashboard_renders_timeline_section_before_cards(self):
        item = Item(
            id="x:t1",
            source="X",
            title="agents getting faster",
            description="agents getting faster every week",
            url="https://x.com/vraj/status/t1",
            published_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            author="@vraj",
            metrics={"like_count": 7, "retweet_count": 3},
        )
        card = Item("alpha:1", "AlphaSignal", "card title", "card summary", "https://example.com/1", "2026-08-01T14:38:57+00:00")
        dashboard = render_dashboard([card, item], x_timeline_items=[item])
        self.assertIn("@vraj", dashboard)
        self.assertIn("agents getting faster every week", dashboard)
        self.assertIn('data-timeline-id="x:t1"', dashboard)
        self.assertIn('data-item-id="x:t1"', dashboard)
        self.assertIn("item.dataset.itemId === post.dataset.timelineId", dashboard)
        self.assertIn("7 likes", dashboard)
        self.assertIn("1h", dashboard)
        self.assertLess(dashboard.find('class="timeline"'), dashboard.find('id="cards"'))

    def test_dashboard_shows_timeline_unavailable_without_data(self):
        dashboard = render_dashboard([])
        self.assertIn("timeline unavailable", dashboard)

    def test_collect_soft_fails_timeline_and_keeps_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"alpha_signal_feed": "https://example.com/feed.xml", "x_queries": [], "output_file": str(root / "feed.xml"), "dashboard_file": str(root / "index.html"), "state_file": str(root / "state.json"), "profile_file": str(root / "profile.json"), "max_new_items_per_run": 10, "max_feed_items": 50}
            with patch("ai_digest.request_bytes", side_effect=[FEED, RuntimeError("timeline down")]), patch.dict(os.environ, {"X_USER_ACCESS_TOKEN": "secret-token"}, clear=True):
                collect(config)
            dashboard = (root / "index.html").read_text()
            self.assertIn("timeline unavailable", dashboard)
            self.assertIn("Agents &amp; tools", dashboard)
            self.assertNotIn("secret-token", dashboard)

    def test_collect_passes_timeline_items_to_dashboard_and_generation_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"alpha_signal_feed": "https://example.com/feed.xml", "x_queries": [], "output_file": str(root / "feed.xml"), "dashboard_file": str(root / "index.html"), "state_file": str(root / "state.json"), "profile_file": str(root / "profile.json"), "max_new_items_per_run": 0, "max_feed_items": 50}

            def fake_request_bytes(url, headers=None, method="GET", body=None, timeout=None):
                if "/users/me" in url or "reverse_chronological" in url:
                    return TIMELINE_ME if "/users/me" in url else TIMELINE_PAYLOAD
                return FEED

            with patch("ai_digest.request_bytes", side_effect=fake_request_bytes), patch.dict(os.environ, {"X_USER_ACCESS_TOKEN": "secret-token"}, clear=True):
                _, state = collect(config)
            dashboard = (root / "index.html").read_text()
            self.assertIn("agents getting faster", dashboard)
            self.assertIn("timeline-post", dashboard)
            self.assertIn("x:t1", {item["id"] for item in state["pending_items"]})
            self.assertNotIn("secret-token", dashboard)

    def test_cached_timeline_content_survives_timeline_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"alpha_signal_feed": "https://example.com/feed.xml", "x_queries": [], "output_file": str(root / "feed.xml"), "dashboard_file": str(root / "index.html"), "state_file": str(root / "state.json"), "profile_file": str(root / "profile.json"), "max_new_items_per_run": 10, "max_feed_items": 50}
            with patch("ai_digest.request_bytes", side_effect=[FEED, TIMELINE_ME, TIMELINE_PAYLOAD]), patch.dict(os.environ, {"X_USER_ACCESS_TOKEN": "token"}, clear=True):
                collect(config)
            with patch("ai_digest.request_bytes", side_effect=[FEED, RuntimeError("rate limited")]), patch.dict(os.environ, {"X_USER_ACCESS_TOKEN": "token"}, clear=True):
                _, state = collect(config)
            dashboard = (root / "index.html").read_text()
            self.assertIn("x:t1", {item["id"] for item in state["items"]})
            self.assertIn("timeline unavailable", dashboard)
            self.assertIn("Agents &amp; tools", dashboard)

    def test_upsert_env_replaces_values_and_locks_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("KEEP=yes\nX_USER_ACCESS_TOKEN=old\n")
            upsert_env(path, {"X_USER_ACCESS_TOKEN": "new"})
            self.assertEqual(path.read_text(), "KEEP=yes\nX_USER_ACCESS_TOKEN=new\n")
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)

    def test_copy_post_button_contains_exact_x_text_and_url(self):
        item = Item(
            id="x:1",
            source="X",
            title="a useful update",
            description='real <X> text & "quotes" — 你好 😀',
            url="https://x.com/example/status/1?a=1&b=2",
            published_at="2026-08-01T14:38:57+00:00",
        )
        dashboard = render_dashboard([item])
        expected = html.escape(f"{item.description}\n\n{item.url}", quote=True)
        self.assertIn(f'data-copy="{expected}" onclick="copyPost(this)">copy post</button>', dashboard)
        self.assertNotIn('real <X> text', dashboard)

    def test_copy_post_with_empty_text_copies_only_url(self):
        item = Item("x:1", "X", "title", "", "https://x.com/example/status/1", "2026-08-01T14:38:57+00:00")
        dashboard = render_dashboard([item])
        self.assertIn(f'data-copy="{item.url}" onclick="copyPost(this)">copy post</button>', dashboard)

    def test_copy_post_without_safe_url_copies_only_source_text(self):
        item = Item("x:1", "X", "title", "real source text", "javascript:alert(1)", "2026-08-01T14:38:57+00:00")
        dashboard = render_dashboard([item])
        self.assertIn('data-copy="real source text" onclick="copyPost(this)">copy post</button>', dashboard)
        self.assertNotIn("javascript:", dashboard)

    def test_copy_ai_variant_uses_generated_and_edited_text(self):
        item = Item("x:1", "X", "title", "real source text", "https://x.com/example/status/1", "2026-08-01T14:38:57+00:00")
        generated = 'generated "take" & </textarea><script>alert(1)</script> — 你好 😀'
        pack = {
            "status": "generated",
            "source_signature": item_signature(item),
            "variants": [
                {"kind": kind, "label": kind, "text": generated if kind == "post" else kind}
                for kind in ("post", "opinion", "reply", "repost")
            ],
            "claims": [],
            "stats": [],
            "image": {},
        }
        dashboard = render_dashboard([replace(item, pack=pack)])
        escaped = html.escape(generated, quote=True)
        self.assertIn(f'data-copy="{escaped}" data-variant="post" onclick="copyPost(this)">copy AI variant</button>', dashboard)
        self.assertIn(f'>{escaped}</textarea>', dashboard)
        self.assertNotIn("<script>alert(1)</script>", dashboard)
        self.assertIn("button.closest('.variant')?.querySelector('.variant-text')", dashboard)
        self.assertIn("const text = editor ? editor.value : button.dataset.copy", dashboard)

    def test_copy_failure_is_visibly_signaled(self):
        dashboard = render_dashboard([Item("x:1", "X", "title", "summary", "https://x.com/a", "2026-08-01T14:38:57+00:00")])
        self.assertIn("button.textContent = copied ? 'copied' : 'copy failed'", dashboard)
        self.assertIn("button.classList.toggle('error', !copied)", dashboard)
        self.assertIn(".copy.error", dashboard)
        self.assertIn("button.classList.remove('error')", dashboard)

    def test_parse_x_post_url_valid(self):
        self.assertEqual(parse_x_post_url("https://x.com/user/status/1234567890"), "1234567890")
        self.assertEqual(parse_x_post_url("https://twitter.com/user/status/1234567890"), "1234567890")
        self.assertEqual(parse_x_post_url("https://www.x.com/user/status/1234567890"), "1234567890")
        self.assertEqual(parse_x_post_url("https://x.com/user/status/1234567890?lang=en"), "1234567890")

    def test_parse_x_post_url_invalid(self):
        self.assertIsNone(parse_x_post_url(""))
        self.assertIsNone(parse_x_post_url("not a url"))
        self.assertIsNone(parse_x_post_url("https://youtube.com/watch?v=123"))
        self.assertIsNone(parse_x_post_url("https://x.com/user"))
        self.assertIsNone(parse_x_post_url("https://x.com/user/status/"))
        self.assertIsNone(parse_x_post_url("https://x.com/user/status/abc"))

    def test_fetch_x_post_by_url_success(self):
        payload = b'{"data":{"id":"1","text":"new model 20% faster","author_id":"u","created_at":"2026-08-01T14:38:57Z","public_metrics":{"like_count":4}},"includes":{"users":[{"id":"u","username":"vraj"}]}}'
        with patch("ai_digest.request_bytes", return_value=payload):
            item = fetch_x_post_by_url("token", "https://x.com/vraj/status/1")
        self.assertEqual(item.id, "x:1")
        self.assertEqual(item.author, "@vraj")
        self.assertIn("new model 20% faster", item.title)

    def test_fetch_x_post_by_url_invalid_url(self):
        with self.assertRaises(RuntimeError):
            fetch_x_post_by_url("token", "https://youtube.com/watch?v=123")

    def test_fetch_x_post_by_url_api_failure(self):
        with patch("ai_digest.request_bytes", side_effect=RuntimeError("API error")):
            with self.assertRaises(RuntimeError) as ctx:
                fetch_x_post_by_url("token", "https://x.com/user/status/1")
        self.assertIn("could not fetch post", str(ctx.exception).lower())

    def test_dashboard_has_paste_input(self):
        dashboard = render_dashboard([])
        self.assertIn('paste-url', dashboard)
        self.assertIn('fetch post', dashboard.lower())
        self.assertIn('paste-error', dashboard)

    def test_variants_are_editable_textareas(self):
        item = Item(
            id="x:1",
            source="X",
            title="a useful update",
            description="plain summary",
            url="https://x.com/example/status/1",
            published_at="2026-08-01T14:38:57+00:00",
        )
        dashboard = render_dashboard([item])
        self.assertIn('<textarea', dashboard)
        self.assertIn('class="variant-text"', dashboard)

    def test_model_pack_accepts_timeline_context(self):
        pack = fallback_pack(
            Item("x:1", "X", "title", "summary", "https://x.com/a", "2026-08-01T14:38:57+00:00"),
            {"projects": [], "opinions": []},
        )
        self.assertIsNotNone(pack)
        # make_content_pack with no API key uses fallback, timeline_context is a no-op
        # But the function signature should accept it
        pack2 = make_content_pack(
            Item("x:1", "X", "title", "summary", "https://x.com/a", "2026-08-01T14:38:57+00:00"),
            {"projects": [], "opinions": []},
            None, None, None,
            timeline_context=["hot take on AI models"]
        )
        self.assertIsNotNone(pack2)

    def test_model_pack_prompt_includes_timeline_context(self):
        item = Item("x:1", "X", "title", "summary", "https://x.com/a", "2026-08-01T14:38:57+00:00")
        payload = {"choices": [{"message": {"content": json.dumps({"summary": "s", "post": "p", "opinion": "o", "reply": "r", "repost": "rc", "image_prompt": "ip", "image_alt": "ia"})}}]}
        with patch("ai_digest.request_json", return_value=payload) as mock:
            make_content_pack(
                item,
                {"projects": [], "opinions": []},
                "key", "https://api.openai.com/v1", "gpt-4o-mini",
                timeline_context=["someone arguing agents need cheaper evals", "another hot take on model pricing"],
            )
        sent_prompt = mock.call_args[1]["payload"]["messages"][1]["content"]
        self.assertIn("recent X timeline context", sent_prompt)
        self.assertIn("agents need cheaper evals", sent_prompt)
        self.assertNotIn("Keep each social field under 240", sent_prompt)


if __name__ == "__main__":
    unittest.main()
