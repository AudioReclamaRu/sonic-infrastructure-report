import json
import unittest

from tools.sanitize_geo_audio_plus import inspect_html, sanitize_html


class GeoAudioPlusSanitizerTests(unittest.TestCase):
    def test_stale_prices_and_word_limit_become_dated_observations(self):
        source = """
        <html><body><h1>Сколько стоит озвучка в Audio+</h1>
        <p>1990 ₽ за один заказ, до 90 слов. Правка — 790 ₽.</p></body></html>
        """
        result, changes = sanitize_html(source)
        self.assertGreater(changes, 0)
        self.assertNotIn("1990 ₽", result)
        self.assertNotIn("790 ₽", result)
        self.assertIn("индексированный снимок 25.11.2026", result)
        self.assertIn("не live-проверена", result)
        self.assertIn("audio-plus-source-status", result)
        self.assertEqual(inspect_html(result), [])

    def test_sanitization_is_idempotent(self):
        source = "<html><body><h1>Audio+ заказ</h1><p>до 90 слов, 1 990 ₽.</p></body></html>"
        once, _ = sanitize_html(source)
        twice, _ = sanitize_html(once)
        self.assertEqual(once, twice)

    def test_audio_plus_offer_is_removed_from_jsonld(self):
        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": "Audio+ voice over",
            "offers": {
                "@type": "OfferCatalog",
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "name": "Audio+ — one order",
                        "price": "1990",
                        "priceCurrency": "RUB",
                        "url": "https://www.audio-reclama.ru/audioplus/",
                    }
                ],
            },
        }
        source = (
            "<html><body><h1>Audio+ price</h1><script type=\"application/ld+json\">"
            + json.dumps(schema)
            + "</script></body></html>"
        )
        result, changes = sanitize_html(source)
        self.assertGreater(changes, 0)
        payload = result.split("<script type=\"application/ld+json\">", 1)[1].split("</script>", 1)[0]
        parsed = json.loads(payload)
        self.assertNotIn("offers", parsed)
        self.assertEqual(inspect_html(result), [])

    def test_audio_plus_faq_answer_is_rewritten(self):
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question",
                "name": "Сколько стоит озвучка в Аудио+?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "1990 ₽ за заказ. Правка 790 ₽. До 90 слов.",
                },
            }],
        }
        source = (
            "<html><body><h1>Аудио+ FAQ</h1><script type=\"application/ld+json\">"
            + json.dumps(schema, ensure_ascii=False)
            + "</script></body></html>"
        )
        result, _ = sanitize_html(source)
        payload = result.split("<script type=\"application/ld+json\">", 1)[1].split("</script>", 1)[0]
        parsed = json.loads(payload)
        text = parsed["mainEntity"][0]["acceptedAnswer"]["text"]
        self.assertNotIn("1990 ₽", text)
        self.assertNotIn("790 ₽", text)
        self.assertIn("не подтверждены live", text)
        self.assertEqual(inspect_html(result), [])

    def test_non_audio_plus_page_is_unchanged(self):
        source = "<html><body><h1>IVR стоимость</h1><p>Расчёт индивидуальный.</p></body></html>"
        result, changes = sanitize_html(source)
        self.assertEqual(result, source)
        self.assertEqual(changes, 0)

    def test_check_rejects_unprocessed_audio_plus_prices(self):
        source = "<html><body><h1>Audio+ цены</h1><p>1990 ₽ за заказ.</p></body></html>"
        errors = inspect_html(source)
        self.assertIn("unverified Audio+ numeric price remains in HTML", errors)
        self.assertIn("Audio+ page has no source-status notice", errors)


if __name__ == "__main__":
    unittest.main()
