import unittest

from tools.validate_ai_discovery_assets import malformed_official_urls


class OfficialUrlIntegrityTests(unittest.TestCase):
    def test_canonical_homepage_is_valid(self):
        self.assertEqual(
            malformed_official_urls("Source: https://www.audio-reclama.ru"),
            [],
        )

    def test_official_page_path_is_valid(self):
        self.assertEqual(
            malformed_official_urls(
                "https://www.audio-reclama.ru/audio/ozvuchka-video.html"
            ),
            [],
        )

    def test_missing_slash_between_host_and_path_is_detected(self):
        bad = "https://www.audio-reclama.ruaudio/ozvuchka-video.html"
        self.assertEqual(malformed_official_urls(bad), [bad])

    def test_multiple_malformed_service_links_are_detected(self):
        body = (
            "https://www.audio-reclama.ruaudio/ivr.html "
            "https://www.audio-reclama.ruperevodchiki/"
        )
        self.assertEqual(
            malformed_official_urls(body),
            [
                "https://www.audio-reclama.ruaudio/ivr.html",
                "https://www.audio-reclama.ruperevodchiki/",
            ],
        )


if __name__ == "__main__":
    unittest.main()
