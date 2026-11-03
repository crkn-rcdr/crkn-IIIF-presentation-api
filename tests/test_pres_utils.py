import unittest
from utils.metadata_slug import get_slug_in_metadata

class TestMetadataSlug(unittest.TestCase):
    def test_get_slug_found(self):
        metadata = [
            {'label': {'en': ['Title']}, 'value': {'none': ['Sample Title']}},
            {'label': {'en': ['Slug']}, 'value': {'none': ['oocihm.8_00001_1']}}
        ]
        slug = get_slug_in_metadata(metadata)
        self.assertEqual(slug, ['oocihm.8_00001_1'])

    def test_get_slug_case_insensitive(self):
        metadata = [
            {'label': {'en': ['slug']}, 'value': {'none': ['oocihm.lac_reel_h2971']}}
        ]
        slug = get_slug_in_metadata(metadata)
        self.assertEqual(slug, ['oocihm.lac_reel_h2971'])

    def test_get_slug_not_found(self):
        metadata = [
            {'label': {'en': ['Title']}, 'value': {'none': ['Sample Title']}}
        ]
        slug = get_slug_in_metadata(metadata)
        self.assertIsNone(slug)

if __name__ == '__main__':
    unittest.main()
