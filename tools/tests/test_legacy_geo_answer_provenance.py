"""Regression tests for source-generator and legacy GEO answer provenance."""
from __future__ import annotations

import copy
import json
import unittest

from tools.legacy_geo_answer_provenance import (
    REGISTRY,
    ROOT,
    _read_text,
    extract_builder_slugs,
    validate_provenance,
)

ANSWERS = ROOT / "geo/answers"
BUILDER = ROOT / "tools/build_geo_site.py"
INDEX = ANSWERS / "index.html"
LLMS = ROOT / "geo/llms.txt"
SITEMAP = ROOT / "geo/sitemap.xml"


class TestLegacyGeoAnswerProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.builder = BUILDER.read_text(encoding="utf-8")
        cls.answers_index = INDEX.read_text(encoding="utf-8-sig")
        cls.llms = LLMS.read_text(encoding="utf-8-sig")
        cls.sitemap = SITEMAP.read_text(encoding="utf-8-sig")
        cls.actual_slugs = {p.name for p in ANSWERS.iterdir() if p.is_dir() and (p / "index.html").is_file()}
        cls.canonicals = {}
        import re
        for slug in cls.actual_slugs:
            page = (ANSWERS / slug / "index.html").read_text(encoding="utf-8-sig")
            match = re.search(r'<link[^>]+rel=[\"\']canonical[\"\'][^>]+href=[\"\']([^\"\']+)', page, re.I)
            if not match:
                match = re.search(r'<link[^>]+href=[\"\']([^\"\']+)[\"\'][^>]+rel=[\"\']canonical', page, re.I)
            cls.canonicals[slug] = match.group(1) if match else ""

    def test_current_repository_provenance_registry_is_valid(self):
        self.assertEqual(
            validate_provenance(self.registry,self.builder,self.answers_index,self.llms,self.sitemap,self.actual_slugs,self.canonicals),
            [],
        )

    def test_generator_model_detects_only_current_source_routes(self):
        hardcoded, dynamic, errors = extract_builder_slugs(self.builder)
        self.assertEqual(errors, [])
        self.assertEqual(hardcoded, {"skolko-stoit-ozvuchka","ivr-privetstvie-cena"})
        self.assertEqual(len(dynamic), 6)
        self.assertEqual(len(hardcoded | dynamic), 8)

    def test_new_unregistered_static_directory_is_rejected(self):
        slugs = set(self.actual_slugs) | {"new-legacy-page"}
        errors = validate_provenance(self.registry,self.builder,self.answers_index,self.llms,self.sitemap,slugs,self.canonicals)
        self.assertTrue(any("answer directory inventory differs" in e for e in errors))

    def test_legacy_page_cannot_be_marked_generator_managed(self):
        data = copy.deepcopy(self.registry)
        data["legacy_pages"][0]["current_generator_class"] = "managed"
        errors = validate_provenance(data,self.builder,self.answers_index,self.llms,self.sitemap,self.actual_slugs,self.canonicals)
        self.assertTrue(any("generator class must stay explicitly unmanaged" in e for e in errors))

    def test_page_cannot_be_marked_llms_listed_without_source_link(self):
        data = copy.deepcopy(self.registry)
        data["legacy_pages"][0]["listed_in_geo_llms"] = True
        errors = validate_provenance(data,self.builder,self.answers_index,self.llms,self.sitemap,self.actual_slugs,self.canonicals)
        self.assertTrue(any("llms flag differs" in e for e in errors))

    def test_global_lastmod_must_not_be_mistaken_for_per_page_update(self):
        data = copy.deepcopy(self.registry)
        data["legacy_pages"][0]["sitemap_lastmod"] = "2026-11-06"
        errors = validate_provenance(data,self.builder,self.answers_index,self.llms,self.sitemap,self.actual_slugs,self.canonicals)
        self.assertTrue(any("sitemap lastmod must be recorded as 2026-11-15" in e for e in errors))

    def test_legacy_canonical_must_match_committed_file(self):
        data = copy.deepcopy(self.registry)
        data["legacy_pages"][0]["canonical_url"] = "https://www.audio-reclama.ru/answers/"
        errors = validate_provenance(data,self.builder,self.answers_index,self.llms,self.sitemap,self.actual_slugs,self.canonicals)
        self.assertTrue(any("canonical URL differs" in e for e in errors))

    def test_cache_or_publish_status_is_not_tested(self):
        data = copy.deepcopy(self.registry)
        data["policy"]["live_public_serving_status"] = "available"
        errors = validate_provenance(data,self.builder,self.answers_index,self.llms,self.sitemap,self.actual_slugs,self.canonicals)
        self.assertTrue(any("live public serving must remain not_tested" in e for e in errors))

    def test_all_legacy_pages_are_not_in_the_llms_answer_list(self):
        self.assertFalse(any(item["listed_in_geo_llms"] for item in self.registry["legacy_pages"]))

    def test_legacy_pages_unlisted_in_llms_remain_in_the_sitemap(self):
        for item in self.registry["legacy_pages"]:
            self.assertTrue(item["present_in_current_sitemap"])


if __name__ == "__main__":
    unittest.main()
