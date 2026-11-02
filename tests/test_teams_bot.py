"""Tests for the Teams bot's pure helpers (no SDK needed)."""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deploy", "teams-bot")))
import botlogic as bl  # noqa: E402


class BotLogicTests(unittest.TestCase):
    def test_empty_allowlist_allows_nobody(self):
        self.assertFalse(bl.is_allowed("abc", set()))
        self.assertFalse(bl.is_allowed(None, {"abc"}))
        self.assertTrue(bl.is_allowed("abc", bl.parse_list(" abc , def ")))

    def test_channel_thread_maps_to_channel_company(self):
        m = {"19:chan@thread.tacv2": "classmat"}
        self.assertEqual(bl.company_for("19:chan@thread.tacv2;messageid=123", m, "catice"), "classmat")
        self.assertEqual(bl.company_for("a:personal-chat", m, "catice"), "catice")

    def test_split_message_respects_limit_and_keeps_text(self):
        text = "\n\n".join(["ก" * 30, "b" * 30, "c" * 95])
        chunks = bl.split_message(text, limit=40)
        self.assertTrue(all(len(c) <= 40 for c in chunks))
        self.assertEqual("".join(chunks).replace("\n", ""), text.replace("\n", ""))
        self.assertEqual(bl.split_message(""), [""])

    def test_session_store_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            s = bl.SessionStore(os.path.join(d, "x", "sessions.json"))
            self.assertIsNone(s.get("c1"))
            s.set("c1", "sess-1"); s.set("c2", "sess-2")
            self.assertEqual(bl.SessionStore(s.path).get("c1"), "sess-1")
            self.assertEqual(json.load(open(s.path)), {"c1": "sess-1", "c2": "sess-2"})


if __name__ == "__main__":
    unittest.main()
