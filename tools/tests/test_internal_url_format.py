import unittest

from tools.check_internal_url_format import find_malformed_domain_joins


class InternalUrlFormatTests(unittest.TestCase):
    def test_accepts_valid_internal_paths(self):
        text = "\n".join(
            [
                "https://www.audio-reclama.ru/audio/radioroliki-zakaz.html",
                "https://www.audio-reclama.ru/perevodchiki/",
                "https://www.audio-reclama.ru",
            ]
        )
        self.assertEqual(find_malformed_domain_joins(text), [])

    def test_rejects_path_joined_to_domain(self):
        text = (
            "https://www.audio-reclama.ruaudio/radioroliki-zakaz.html\n"
            "https://www.audio-reclama.ruproject/vnukovo.html"
        )
        found = find_malformed_domain_joins(text)
        self.assertEqual([line for line, _ in found], [1, 2])
        self.assertEqual(len(found), 2)

    def test_ignores_other_domains(self):
        self.assertEqual(
            find_malformed_domain_joins(
                "https://example.comaudio/radioroliki-zakaz.html"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
