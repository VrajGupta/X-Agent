import json
import os
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from datetime import datetime, timedelta, timezone

from ai_digest import Item, clean_text, clip_post, collect, fallback_pack, fetch_x_timeline, item_signature, pack_is_valid, parse_alpha_signal, parse_x_response, render_dashboard, render_x_timeline_section, render_rss, to_post_text, variant_for, x_weighted_length
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

    def test_profile_opinion_changes_fallback_pack(self):
        profile = {"projects": [{"name": "my project"}], "opinions": ["measure task cost first"]}
        item = Item("x:1", "X", "title", "summary", "https://x.com/a", "2026-08-01T14:38:57+00:00")
        pack = fallback_pack(item, profile)
        self.assertIn("measure task cost first", pack["variants"][1]["text"])
        self.assertIn("my project", pack["variants"][1]["text"])

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

        def fake_request_bytes(url, headers=None, method="GET", body=None):
            calls.append((url, headers))
            return TIMELINE_ME if "/users/me" in url else TIMELINE_PAYLOAD

        with patch("ai_digest.request_bytes", side_effect=fake_request_bytes):
            items = fetch_x_timeline("secret-token", max_results=20)
        self.assertEqual(len(calls), 2)
        me_url, timeline_url = calls[0][0], calls[1][0]
        self.assertIn("/users/me", me_url)
        self.assertIn("/users/42/timelines/reverse_chronological", timeline_url)
        self.assertIn("max_results=20", timeline_url)
        for _, headers in calls:
            self.assertEqual(headers["Authorization"], "Bearer secret-token")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "x:t1")
        self.assertEqual(items[0].metrics["like_count"], 7)

    def test_render_x_timeline_section_shows_unavailable_when_none(self):
        self.assertIn("timeline unavailable", render_x_timeline_section(None))

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
        dashboard = render_dashboard([card], x_timeline_items=[item])
        self.assertIn("@vraj", dashboard)
        self.assertIn("agents getting faster every week", dashboard)
        self.assertIn("data-timeline-id", dashboard)
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

    def test_collect_passes_timeline_items_to_dashboard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"alpha_signal_feed": "https://example.com/feed.xml", "x_queries": [], "output_file": str(root / "feed.xml"), "dashboard_file": str(root / "index.html"), "state_file": str(root / "state.json"), "profile_file": str(root / "profile.json"), "max_new_items_per_run": 10, "max_feed_items": 50}

            def fake_request_bytes(url, headers=None, method="GET", body=None):
                if "/users/me" in url or "reverse_chronological" in url:
                    return TIMELINE_ME if "/users/me" in url else TIMELINE_PAYLOAD
                return FEED

            with patch("ai_digest.request_bytes", side_effect=fake_request_bytes), patch.dict(os.environ, {"X_USER_ACCESS_TOKEN": "secret-token"}, clear=True):
                collect(config)
            dashboard = (root / "index.html").read_text()
            self.assertIn("agents getting faster", dashboard)
            self.assertIn("timeline-post", dashboard)
            self.assertNotIn("secret-token", dashboard)

    def test_upsert_env_replaces_values_and_locks_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("KEEP=yes\nX_USER_ACCESS_TOKEN=old\n")
            upsert_env(path, {"X_USER_ACCESS_TOKEN": "new"})
            self.assertEqual(path.read_text(), "KEEP=yes\nX_USER_ACCESS_TOKEN=new\n")
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
