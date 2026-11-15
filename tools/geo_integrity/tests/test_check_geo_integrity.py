from __future__ import annotations

import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import check_geo_integrity as gate


class GeoIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.geo = self.root / "geo"
        (self.geo / "answers").mkdir(parents=True)
        (self.geo / "knowledge" / "query-matrix").mkdir(parents=True)
        self.base = gate.DEFAULT_BASE_URL

        root_html = f"""<!doctype html>
<html lang="ru"><head>
<title>Главная</title>
<meta name="robots" content="index,follow">
<meta name="build-sha" content="abcdef1">
<link rel="canonical" href="{self.base}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Organization","name":"Test"}}</script>
</head><body><h1>Главная</h1></body></html>"""
        child_url = self.base + "answers/"
        query_url = self.base + "knowledge/query-matrix/"
        child_html = f"""<!doctype html>
<html lang="ru"><head>
<title>Ответы</title>
<meta name="robots" content="index,follow">
<meta name="build-sha" content="abcdef1">
<link rel="canonical" href="{child_url}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Главная","item":"{self.base}"}},{{"@type":"ListItem","position":2,"name":"Ответы"}}]}}</script>
</head><body><h1>Ответы</h1></body></html>"""
        query_html = f"""<!doctype html>
<html lang="ru"><head>
<title>Матрица запросов</title>
<meta name="robots" content="index,follow">
<meta name="build-sha" content="abcdef1">
<link rel="canonical" href="{query_url}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Главная","item":"{self.base}"}},{{"@type":"ListItem","position":2,"name":"Матрица запросов"}}]}}</script>
</head><body><h1>Матрица</h1><table><tr><td>Тестовый кластер</td></tr></table></body></html>"""
        (self.geo / "index.html").write_text(root_html, encoding="utf-8")
        (self.geo / "answers" / "index.html").write_text(child_html, encoding="utf-8")
        (self.geo / "knowledge" / "query-matrix" / "index.html").write_text(query_html, encoding="utf-8")
        (self.geo / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<url><loc>{self.base}</loc></url>"
            f"<url><loc>{child_url}</loc></url>"
            f"<url><loc>{query_url}</loc></url>"
            "</urlset>",
            encoding="utf-8",
        )
        (self.geo / "llms.txt").write_text("# Test\n", encoding="utf-8")
        (self.geo / "llms-full.txt").write_text("# Test full\n", encoding="utf-8")
        blog_fixture = {
            "facts": [{
                "id": "BF-TEST-001",
                "verification_status": "verified",
                "phase3_classification": "verified",
            }]
        }
        ledger_fixture = {
            "rows": [{
                "id": "BF-TEST-001",
                "status": "verified",
                "phase3_classification": "verified",
            }]
        }
        cases_fixture = {"cases": []}
        queries_fixture = {"rows": [{"cluster": "Тестовый кластер", "intent": "test", "supporting_fact_ids": ["BF-TEST-001"]}]}
        for filename in gate.MACHINE_FILES:
            asset = self.geo / filename
            if asset.exists():
                continue
            asset.parent.mkdir(parents=True, exist_ok=True)
            if filename == "knowledge/blog-facts.json":
                sample = json.dumps(blog_fixture) + "\n"
            elif filename == "knowledge/evidence-ledger.json":
                sample = json.dumps(ledger_fixture) + "\n"
            elif filename == "knowledge/case-studies.json":
                sample = json.dumps(cases_fixture) + "\n"
            elif filename == "knowledge/query-matrix.json":
                sample = json.dumps(queries_fixture) + "\n"
            elif filename == "knowledge/combined.json":
                sample = json.dumps({
                    "blog_facts": blog_fixture,
                    "evidence_ledger": ledger_fixture,
                    "case_studies": cases_fixture,
                    "query_matrix": queries_fixture,
                }) + "\n"
            elif filename == "knowledge/evidence-ledger.csv":
                sample = (
                    "id,status,phase3_classification\n"
                    "BF-TEST-001,verified,verified\n"
                )
            elif filename in gate.MACHINE_JSON_FILES:
                sample = '{"fixture": true}\n'
            elif filename in gate.MACHINE_XML_FILES:
                sample = '<?xml version="1.0" encoding="UTF-8"?>\n<fixture />\n'
            elif filename == "knowledge/query-matrix.csv":
                sample = 'cluster,intent,supporting_fact_ids\nТестовый кластер,test,"[""BF-TEST-001""]"\n'
            elif filename in gate.MACHINE_CSV_FILES:
                sample = "id,value\n1,test\n"
            else:
                sample = "fixture\n"
            asset.write_text(sample, encoding="utf-8")

    def _public_fixture(self):
        errors, records, urls = gate.audit_local(self.root, self.base)
        self.assertEqual(errors, [])
        base = urllib.parse.urlsplit(self.base)

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.netloc == base.netloc and parsed.path == "/robots.txt":
                return 404, b"", url

            relative = parsed.path[len(base.path):]
            if not relative:
                local_path = self.geo / "index.html"
            elif relative.endswith("/"):
                local_path = self.geo / relative / "index.html"
            else:
                local_path = self.geo / relative
            if not local_path.is_file():
                return 404, b"", url
            return 200, local_path.read_bytes(), url

        return records, urls, fake_get

    def test_hash_normalizes_line_endings_but_not_edge_whitespace(self) -> None:
        self.assertEqual(
            gate.normalized_hash(b"<p>ok</p>\r\n"),
            gate.normalized_hash(b"<p>ok</p>\n"),
        )
        self.assertNotEqual(
            gate.normalized_hash(b"<p>ok</p>\n"),
            gate.normalized_hash(b"<p>ok</p>\n "),
        )

    def test_schema_context_requires_canonical_schema_org_uri(self) -> None:
        self.assertTrue(gate.has_schema_org_context("https://schema.org"))
        self.assertTrue(gate.has_schema_org_context(["https://example.org", "https://schema.org/"]))
        self.assertTrue(gate.has_schema_org_context({"@vocab": "https://schema.org/"}))
        self.assertFalse(gate.has_schema_org_context("https://example.org/schema.org"))
        self.assertFalse(gate.has_schema_org_context("schema.org"))

    def test_public_audit_accepts_same_artifact_and_missing_root_robots(self) -> None:
        records, urls, fake_get = self._public_fixture()
        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, notes = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertEqual(errors, [])
        self.assertTrue(any("returns 404" in note for note in notes))

    def test_public_audit_fails_when_machine_endpoint_redirects_off_origin(self) -> None:
        records, urls, normal_get = self._public_fixture()

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.path.endswith("/llms.txt"):
                body = (self.geo / "llms.txt").read_bytes()
                return 200, body, "https://evil.example/llms.txt"
            return normal_get(url, attempts, timeout, allowed_status)

        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, _ = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertTrue(any("unexpected origin" in error for error in errors))

    def test_public_audit_fails_when_machine_asset_differs(self) -> None:
        records, urls, normal_get = self._public_fixture()

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.path.endswith("/pricing.json"):
                return 200, b'{"different": true}\n', url
            return normal_get(url, attempts, timeout, allowed_status)

        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, _ = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertTrue(any("pricing.json: public file differs from local artifact" in e
                            for e in errors))

    def test_public_sitemap_rejects_duplicate_urls(self) -> None:
        records, urls, normal_get = self._public_fixture()

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.path.endswith("/sitemap.xml"):
                body = (self.geo / "sitemap.xml").read_bytes()
                duplicate = body.replace(
                    b"</urlset>",
                    f"<url><loc>{self.base}</loc></url></urlset>".encode("utf-8"),
                )
                return 200, duplicate, url
            return normal_get(url, attempts, timeout, allowed_status)

        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, _ = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertTrue(any("public sitemap contains duplicate" in e for e in errors))

    def test_missing_machine_asset_fails(self) -> None:
        (self.geo / "knowledge" / "blog-facts.json").unlink()
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "missing machine-readable asset: geo/knowledge/blog-facts.json" in e
            for e in errors
        ))

    def test_invalid_json_machine_asset_fails(self) -> None:
        (self.geo / "pricing.json").write_text("{invalid", encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "invalid machine-readable asset geo/pricing.json" in e for e in errors
        ))

    def test_invalid_xml_machine_asset_fails(self) -> None:
        (self.geo / "rss.xml").write_text("<rss><unclosed></rss>", encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "invalid machine-readable asset geo/rss.xml" in e for e in errors
        ))

    def test_invalid_csv_row_width_fails(self) -> None:
        (self.geo / "knowledge" / "query-matrix.csv").write_text(
            "id,value\n1,test,extra\n", encoding="utf-8"
        )
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "invalid machine-readable asset geo/knowledge/query-matrix.csv" in e
            and "expected 2" in e
            for e in errors
        ))

    def test_combined_knowledge_copy_must_match_source_json(self) -> None:
        path = self.geo / "knowledge" / "combined.json"
        combined = json.loads(path.read_text(encoding="utf-8"))
        combined["blog_facts"] = {"facts": []}
        path.write_text(json.dumps(combined), encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "combined.json blog_facts differs" in item for item in errors
        ))

    def test_combined_case_studies_copy_must_match_source_json(self) -> None:
        path = self.geo / "knowledge" / "combined.json"
        combined = json.loads(path.read_text(encoding="utf-8"))
        combined["case_studies"] = {"cases": [{"id": "stale"}]}
        path.write_text(json.dumps(combined), encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "combined.json case_studies differs" in item for item in errors
        ))

    def test_query_matrix_html_must_include_every_json_cluster(self) -> None:
        path = self.geo / "knowledge" / "query-matrix" / "index.html"
        html = path.read_text(encoding="utf-8").replace(
            "Тестовый кластер", "Отсутствующий кластер"
        )
        path.write_text(html, encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "query-matrix.html is missing cluster: Тестовый кластер" in item
            for item in errors
        ))

    def test_query_matrix_csv_must_match_json(self) -> None:
        path = self.geo / "knowledge" / "query-matrix.csv"
        csv_text = path.read_text(encoding="utf-8").replace(
            "test,", "stale,"
        )
        path.write_text(csv_text, encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "query-matrix.csv row 1 field intent differs from query-matrix.json" in item
            for item in errors
        ))

    def test_query_matrix_supporting_ids_must_exist(self) -> None:
        query_path = self.geo / "knowledge" / "query-matrix.json"
        query_data = json.loads(query_path.read_text(encoding="utf-8"))
        query_data["rows"][0]["supporting_fact_ids"] = ["NOT-REAL"]
        query_path.write_text(json.dumps(query_data), encoding="utf-8")
        combined_path = self.geo / "knowledge" / "combined.json"
        combined_data = json.loads(combined_path.read_text(encoding="utf-8"))
        combined_data["query_matrix"] = query_data
        combined_path.write_text(json.dumps(combined_data), encoding="utf-8")
        csv_path = self.geo / "knowledge" / "query-matrix.csv"
        csv_path.write_text(
            'cluster,intent,supporting_fact_ids\nТестовый кластер,test,"[""NOT-REAL""]"\n',
            encoding="utf-8",
        )
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "query-matrix row 'Тестовый кластер' references unknown ID: NOT-REAL" in item
            for item in errors
        ))

    def test_combined_query_matrix_copy_must_match_source_json(self) -> None:
        path = self.geo / "knowledge" / "combined.json"
        combined = json.loads(path.read_text(encoding="utf-8"))
        combined["query_matrix"] = {"rows": [{"cluster": "stale"}]}
        path.write_text(json.dumps(combined), encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "combined.json query_matrix differs" in item for item in errors
        ))

    def test_evidence_ledger_csv_must_match_json(self) -> None:
        path = self.geo / "knowledge" / "evidence-ledger.csv"
        path.write_text(
            "id,status,phase3_classification\n"
            "BF-TEST-001,cited_in_blog,verified\n",
            encoding="utf-8",
        )
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "evidence-ledger.csv row BF-TEST-001 field status differs" in item
            for item in errors
        ))

    def test_blog_fact_status_and_classification_must_match_ledger(self) -> None:
        path = self.geo / "knowledge" / "blog-facts.json"
        blog = json.loads(path.read_text(encoding="utf-8"))
        blog["facts"][0]["verification_status"] = "cited_in_blog"
        path.write_text(json.dumps(blog), encoding="utf-8")
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any(
            "BF-TEST-001: blog verification_status differs" in item
            for item in errors
        ))

    def test_public_audit_fails_when_root_robots_redirects_off_origin(self) -> None:
        records, urls, normal_get = self._public_fixture()

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.path == "/robots.txt":
                return 404, b"", "https://evil.example/robots.txt"
            return normal_get(url, attempts, timeout, allowed_status)

        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, _ = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertTrue(any("unexpected origin" in error for error in errors))

    def test_public_audit_fails_when_claude_searchbot_is_blocked(self) -> None:
        records, urls, normal_get = self._public_fixture()

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.path == "/robots.txt":
                body = (
                    "User-agent: Claude-SearchBot\n"
                    "Disallow: /sonic-infrastructure-report/geo/\n"
                ).encode("utf-8")
                return 200, body, url
            return normal_get(url, attempts, timeout, allowed_status)

        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, _ = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertTrue(any(
            "Claude-SearchBot is disallowed" in error for error in errors
        ))

    def test_training_and_user_fetch_tokens_are_notes_not_indexing_failures(self) -> None:
        records, urls, normal_get = self._public_fixture()

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.path == "/robots.txt":
                body = (
                    "User-agent: Google-Extended\n"
                    "Disallow: /\n"
                    "User-agent: GPTBot\n"
                    "Disallow: /\n"
                    "User-agent: ChatGPT-User\n"
                    "Disallow: /\n"
                    "User-agent: ClaudeBot\n"
                    "Disallow: /\n"
                    "User-agent: Claude-User\n"
                    "Disallow: /\n"
                    "User-agent: Perplexity-User\n"
                    "Disallow: /\n"
                ).encode("utf-8")
                return 200, body, url
            return normal_get(url, attempts, timeout, allowed_status)

        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, notes = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertEqual(errors, [])
        for agent in (
            "Google-Extended", "GPTBot", "ChatGPT-User",
            "ClaudeBot", "Claude-User", "Perplexity-User",
        ):
            self.assertTrue(any(agent + " is disallowed" in note for note in notes))

    def test_public_audit_fails_if_indexing_bot_is_blocked_on_any_sitemap_page(self) -> None:
        records, urls, normal_get = self._public_fixture()

        def fake_get(url, attempts, timeout, allowed_status=()):
            parsed = urllib.parse.urlsplit(url)
            if parsed.path == "/robots.txt":
                body = (
                    "User-agent: OAI-SearchBot\n"
                    "Disallow: /sonic-infrastructure-report/geo/answers/\n"
                ).encode("utf-8")
                return 200, body, url
            return normal_get(url, attempts, timeout, allowed_status)

        with patch.object(gate, "_http_get", side_effect=fake_get):
            errors, _ = gate.audit_public(
                records, urls, self.base, root=self.root
            )
        self.assertTrue(any(
            "OAI-SearchBot is disallowed" in error and "/answers/" in error
            for error in errors
        ))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_valid_artifact_passes(self) -> None:
        errors, records, urls = gate.audit_local(self.root, self.base)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 3)
        self.assertEqual(len(urls), 3)

    def test_missing_build_sha_fails(self) -> None:
        page = self.geo / "answers" / "index.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                '<meta name="build-sha" content="abcdef1">', ""
            ),
            encoding="utf-8",
        )
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any("build-sha" in item for item in errors))

    def test_non_schema_org_context_fails(self) -> None:
        page = self.geo / "answers" / "index.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                '"@context":"https://schema.org"',
                '"@context":"https://example.org/schema.org"',
            ),
            encoding="utf-8",
        )
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any("canonical Schema.org @context" in item for item in errors))

    def test_duplicate_breadcrumb_fails(self) -> None:
        page = self.geo / "answers" / "index.html"
        extra = (
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"BreadcrumbList",'
            '"itemListElement":[]}</script>'
        )
        page.write_text(
            page.read_text(encoding="utf-8").replace("</head>", extra + "</head>"),
            encoding="utf-8",
        )
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any("duplicate top-level JSON-LD type BreadcrumbList" in item
                            for item in errors))

    def test_sitemap_cannot_escape_geo_base(self) -> None:
        sitemap = self.geo / "sitemap.xml"
        sitemap.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://evil.example/outside/</loc></url>'
            "</urlset>",
            encoding="utf-8",
        )
        errors, _, _ = gate.audit_local(self.root, self.base)
        self.assertTrue(any("outside GEO base" in item for item in errors))



class GeoEvidenceRegistryContractTests(unittest.TestCase):
    """Protect evidence scope/status for historically sensitive GEO claims."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[3] / "geo" / "knowledge"
        cls.blog = json.loads(
            (cls.root / "blog-facts.json").read_text(encoding="utf-8")
        )
        cls.ledger = json.loads(
            (cls.root / "evidence-ledger.json").read_text(encoding="utf-8")
        )
        cls.facts = {item["id"]: item for item in cls.blog["facts"]}
        cls.rows = {item["id"]: item for item in cls.ledger["rows"]}

    def test_iab_2017_reach_and_time_range_are_not_overstated(self) -> None:
        fact = self.facts["BF-2018-001"]
        row = self.rows["BF-2018-001"]
        self.assertEqual(fact["phase3_classification"], "verified")
        self.assertEqual(fact["verification_status"], "verified")
        self.assertIn("65 млн", fact["claim"])
        self.assertIn("23 млн", fact["claim"])
        self.assertIn("3,5–5", fact["claim"])
        self.assertNotIn("уникальных слушателей", fact["claim"].lower())
        self.assertIn("не переносить", row["limitations"].lower())
        self.assertEqual(row["status"], "verified")

    def test_iab_podcast_us_taxonomy_remains_scope_limited(self) -> None:
        fact = self.facts["BF-2020-003"]
        row = self.rows["BF-2020-003"]
        self.assertEqual(fact["phase3_classification"], "partially_verified")
        self.assertEqual(row["phase3_classification"], "partially_verified")
        evidence = row["phase3_evidence"]
        for share in ("66%", "27%", "6%", "1%"):
            self.assertIn(share, evidence)
        self.assertIn("США", row["applicability_scope"])
        self.assertIn("не переносить на россию", row["limitations"].lower())
        self.assertIn("не проводила аудит", evidence)

    def test_iab_market_values_are_labeled_forecasts_not_actuals(self) -> None:
        fact = self.facts["BF-2020-005"]
        row = self.rows["BF-2020-005"]
        self.assertEqual(fact["phase3_classification"], "partially_verified")
        self.assertEqual(row["phase3_classification"], "partially_verified")
        self.assertIn("прогноз", fact["claim"].lower())
        self.assertIn("3,7 млрд", row["phase3_evidence"])
        self.assertIn("6,1 млрд", row["phase3_evidence"])
        self.assertIn("761,5 млн", row["phase3_evidence"])
        self.assertIn("не являются фактическими результатами", fact["claim"])

    def test_data_insight_radio_multiplier_is_not_promoted_to_verified(self) -> None:
        fact = self.facts["BF-2020-006"]
        row = self.rows["BF-2020-006"]
        self.assertEqual(fact["phase3_classification"], "partially_verified")
        self.assertEqual(row["phase3_classification"], "partially_verified")
        self.assertIn("1 млрд", fact["claim"])
        self.assertIn("17 млрд", fact["claim"])
        self.assertIn("нельзя считать подтверждённой", row["phase3_evidence"])
        self.assertIn("расходы по каналам", row["phase3_evidence"])
        self.assertIn("ROI", row["phase3_evidence"])

    def test_service_page_snapshots_are_not_current_price_evidence(self) -> None:
        expected = {
            "CF-AUDIOBOOKS-SERVICE": "https://www.audio-reclama.ru/audio/sozdanie-audioknig.html",
            "CF-VIDEO-VOICEOVER-SERVICE": "https://www.audio-reclama.ru/audio/ozvuchka-video.html",
        }
        for evidence_id, source_url in expected.items():
            row = self.rows[evidence_id]
            self.assertEqual(row["status"], "observed_verify_on_source")
            self.assertEqual(row["phase3_classification"], "partially_verified")
            self.assertEqual(row["primary_source_url"], source_url)
            limits = row["limitations"].lower()
            self.assertTrue(
                "не подтверждены как текущие" in limits
                or "не подтверждает текущую полноту состава услуги и тарифы" in limits
            )
            self.assertNotIn("current price verified", row["applicability_scope"].lower())

    def test_blog_fact_status_and_classification_match_ledger(self) -> None:
        for fact_id, fact in self.facts.items():
            row = self.rows.get(fact_id)
            self.assertIsNotNone(row, f"{fact_id} has no ledger row")
            self.assertEqual(fact["verification_status"], row["status"], fact_id)
            self.assertEqual(
                fact["phase3_classification"],
                row["phase3_classification"],
                fact_id,
            )


if __name__ == "__main__":
    unittest.main()
