import tempfile
import unittest
from pathlib import Path

from publication_guard import (
    PublicationLedger,
    abbreviation_issues,
    canonicalize_url,
    content_fingerprint,
    event_key_for_item,
)


class PublicationGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = PublicationLedger(Path(self.tmp.name) / "ledger.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def reserve(self, key, guid, url, text):
        return self.ledger.reserve(
            key, guid, url, content_fingerprint(text), text
        )

    def test_tracking_parameters_and_www_do_not_create_new_source(self):
        a = canonicalize_url("https://www.RadioInk.com/story/?utm_source=x&fbclid=abc")
        b = canonicalize_url("https://radioink.com/story")
        self.assertEqual(a, b)

    def test_different_guid_same_event_key_is_blocked(self):
        first = self.reserve("event:rnc-fcc-2026", "variant-a", "", "same event copy")
        second = self.reserve("event:rnc-fcc-2026", "variant-b", "", "rewritten copy")
        self.assertEqual(first["decision"], "RESERVED")
        self.assertEqual(second["decision"], "DUPLICATE")

    def test_same_canonical_source_is_blocked(self):
        first = self.reserve("event:one", "a", "https://radioink.com/story?utm_medium=x", "one")
        second = self.reserve("event:two", "b", "https://www.radioink.com/story/", "two")
        self.assertEqual(first["decision"], "RESERVED")
        self.assertEqual(second["decision"], "DUPLICATE")
        self.assertEqual(second["reason"], "canonical_source_already_used")

    def test_near_duplicate_from_another_source_requires_review(self):
        text_a = (
            "National Republican Committee and Texas party challenge the FCC over "
            "the lowest political advertising rate. The case was filed in Texas "
            "and asks the court to extend the rate or strike it down."
        )
        text_b = (
            "The National Republican Committee and the Texas party challenge "
            "FCC rules on the lowest political ad rate. Filed in Texas, the case "
            "asks the court to extend the rate or strike it down."
        )
        first = self.reserve("event:source-a", "a", "https://a.example/story", text_a)
        second = self.reserve("event:source-b", "b", "https://b.example/story", text_b)
        self.assertEqual(first["decision"], "RESERVED")
        self.assertEqual(second["decision"], "REVIEW_REQUIRED")

    def test_unrelated_story_can_be_reserved(self):
        first = self.reserve("event:one", "a", "https://a.example/one", "one radio story")
        second = self.reserve("event:two", "b", "https://b.example/two", "a different court case")
        self.assertEqual(first["decision"], "RESERVED")
        self.assertEqual(second["decision"], "RESERVED")

    def test_unknown_send_outcome_never_retries_automatically(self):
        first = self.reserve("event:timeout", "a", "", "timeout story")
        self.ledger.mark_unknown("event:timeout", "client timeout")
        second = self.reserve("event:timeout", "a-new-guid", "", "timeout story changed")
        self.assertEqual(first["decision"], "RESERVED")
        self.assertEqual(second["decision"], "DUPLICATE")
        self.assertEqual(second["status"], "UNKNOWN")

    def test_definitive_api_rejection_can_retry(self):
        first = self.reserve("event:rejected", "a", "", "rejected story")
        self.ledger.mark_failed("event:rejected", "Telegram returned ok=false")
        second = self.reserve("event:rejected", "b", "", "rejected story edited")
        self.assertEqual(first["decision"], "RESERVED")
        self.assertEqual(second["decision"], "RESERVED")
        self.assertEqual(self.ledger.get_by_event_key("event:rejected")["attempts"], 2)

    def test_legacy_sent_publication_is_imported(self):
        self.ledger.import_legacy_sent(
            "source:abc", "legacy-guid", "", content_fingerprint("legacy body"),
            "legacy body", "81", "@channel"
        )
        self.assertTrue(self.ledger.has_guid("legacy-guid"))
        self.assertEqual(self.ledger.get_by_guid("legacy-guid")["message_id"], "81")

    def test_explicit_abbreviation_expansions_pass(self):
        copy = (
            "Национальный комитет Республиканской партии США "
            "(Republican National Committee, RNC) обратился в "
            "Федеральную комиссию по связи США "
            "(Federal Communications Commission, FCC)."
        )
        policy = {
            "editorial_version": 2,
            "abbreviations": {
                "RNC": {
                    "mode": "expanded",
                    "expansion": "Национальный комитет Республиканской партии США",
                },
                "FCC": {
                    "mode": "expanded",
                    "expansion": "Федеральную комиссию по связи США",
                },
            },
        }
        self.assertEqual(abbreviation_issues(copy, policy), [])

    def test_expansion_after_first_use_is_rejected(self):
        copy = "RNC подал иск. Позже это название раскрыли как Republican National Committee."
        policy = {
            "editorial_version": 2,
            "abbreviations": {
                "RNC": {
                    "mode": "expanded",
                    "expansion": "Republican National Committee",
                },
            },
        }
        self.assertIn(
            "abbreviation_not_expanded_before_first_use:RNC",
            abbreviation_issues(copy, policy),
        )

    def test_phonetic_cyrillic_rendering_is_rejected(self):
        copy = "Гоппартия США подала иск."
        policy = {"editorial_version": 2, "abbreviations": {}}
        issues = abbreviation_issues(copy, policy)
        self.assertTrue(any("transliteration" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
