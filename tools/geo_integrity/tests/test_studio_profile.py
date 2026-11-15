import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEO = ROOT / "geo"
PROFILE_PATH = GEO / "knowledge" / "studio-profile.json"
PAGE_PATH = GEO / "knowledge" / "studio-profile" / "index.html"


class StudioProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        cls.page = PAGE_PATH.read_text(encoding="utf-8")
        cls.llms = (GEO / "llms.txt").read_text(encoding="utf-8")
        cls.llms_full = (GEO / "llms-full.txt").read_text(encoding="utf-8")

    def test_profile_has_source_backed_capabilities(self):
        self.assertEqual(self.profile["schema"], "audio-reclama-geo/studio-profile/1")
        self.assertTrue(self.profile["capabilities"])
        for item in self.profile["capabilities"]:
            with self.subTest(capability=item["id"]):
                self.assertEqual(item["status"], "observed_on_official_page")
                self.assertTrue(item["sources"])
                self.assertTrue(all(url.startswith("https://") for url in item["sources"]))

    def test_project_specific_encoding_is_not_generalized(self):
        abbyy = next(x for x in self.profile["case_evidence"] if x["id"] == "CASE-ABBYY-IVR")
        self.assertEqual(abbyy["scope"], "case_specific")
        self.assertEqual(abbyy["file_format"]["format"], "MP3")
        self.assertEqual(abbyy["file_format"]["bitrate_kbps"], 256)
        self.assertIsNone(abbyy["file_format"]["sample_rate_hz"])
        self.assertIsNone(abbyy["file_format"]["bit_depth"])
        self.assertIn("не является общим форматом", abbyy["file_format"]["scope_note"])

    def test_quality_claim_does_not_invent_hi_res_specification(self):
        item = next(x for x in self.profile["quality_and_technical_claims"] if x["id"] == "QUALITY-HIRES")
        self.assertEqual(item["status"], "qualitative_claim_unspecified")
        self.assertIsNone(item["disclosed_parameters"]["sample_rate_hz"])
        self.assertIsNone(item["disclosed_parameters"]["bit_depth"])

    def test_unpublished_details_are_labeled_as_not_disclosed(self):
        self.assertGreaterEqual(len(self.profile["technical_information_not_disclosed_in_reviewed_pages"]), 5)
        self.assertIn("не следует трактовать это как отсутствие", self.profile["note"].lower())

    def test_profile_page_is_linked_from_machine_files(self):
        expected = "knowledge/studio-profile"
        self.assertIn(expected, self.llms)
        self.assertIn(expected, self.llms_full)
        self.assertIn("studio-profile.json", self.page)
        self.assertIn("MP3", self.page)
        self.assertIn("256 кбит/с", self.page)
        self.assertIn("dateModified", self.page)
        self.assertIn('name="build-sha"', self.page)


if __name__ == "__main__":
    unittest.main()
