from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import check_geo_integrity as gate


class GeoIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.geo = self.root / "geo"
        (self.geo / "answers").mkdir(parents=True)
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
        child_html = f"""<!doctype html>
<html lang="ru"><head>
<title>Ответы</title>
<meta name="robots" content="index,follow">
<meta name="build-sha" content="abcdef1">
<link rel="canonical" href="{child_url}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Главная","item":"{self.base}"}},{{"@type":"ListItem","position":2,"name":"Ответы"}}]}}</script>
</head><body><h1>Ответы</h1></body></html>"""
        (self.geo / "index.html").write_text(root_html, encoding="utf-8")
        (self.geo / "answers" / "index.html").write_text(child_html, encoding="utf-8")
        (self.geo / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<url><loc>{self.base}</loc></url>"
            f"<url><loc>{child_url}</loc></url>"
            "</urlset>",
            encoding="utf-8",
        )
        (self.geo / "llms.txt").write_text("# Test\n", encoding="utf-8")
        (self.geo / "llms-full.txt").write_text("# Test full\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_valid_artifact_passes(self) -> None:
        errors, records, urls = gate.audit_local(self.root, self.base)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 2)
        self.assertEqual(len(urls), 2)

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


if __name__ == "__main__":
    unittest.main()
