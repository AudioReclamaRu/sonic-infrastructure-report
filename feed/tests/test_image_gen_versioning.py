# tests/test_image_gen_versioning.py
# Version-aware cover regeneration contract tests (feed/image_gen.py).
# Run from repo root: python -m unittest feed.tests.test_image_gen_versioning
# or:                     python feed/tests/test_image_gen_versioning.py
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import image_gen

GUID = 'test-guid-2026-01-01'
IMG_NAME = 'test-guid-2026-01-01'


def make_csv(path):
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write('TITLE~~~DESC~~~DATE~~~CHANNEL~~~' + GUID + '~~~' + IMG_NAME + '\n')


class Context:
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix='cover_t_')
        self.images = os.path.join(self.tmp, 'images')
        os.makedirs(self.images, exist_ok=True)
        make_csv(os.path.join(self.tmp, 'items.csv'))
        self.prev = {}
        for k in ('OUT_DIR', 'ITEMS_CSV', 'MANIFEST', 'BACKUP_ROOT', 'DESIGN_VERSION'):
            self.prev[k] = getattr(image_gen, k)
        image_gen.OUT_DIR = self.images
        image_gen.ITEMS_CSV = os.path.join(self.tmp, 'items.csv')
        image_gen.MANIFEST = os.path.join(self.images, 'manifest.json')
        image_gen.BACKUP_ROOT = os.path.join(self.images, 'backup-test')
        image_gen.DESIGN_VERSION = 'test-v1'

    def restore(self):
        for k, v in self.prev.items():
            setattr(image_gen, k, v)


class TestVersionAwareCoverGeneration(unittest.TestCase):
    def setUp(self):
        self.ctx = Context()

    def tearDown(self):
        self.ctx.restore()

    def asset_path(self):
        return os.path.join(self.ctx.images, IMG_NAME + '.png')

    def load_manifest(self):
        with open(os.path.join(self.ctx.images, 'manifest.json'), 'r', encoding='utf-8') as f:
            return json_load(f)

    # --- Test 1: PNG absent -> created + manifest updated ---
    def test_1_absent_creates_and_updates_manifest(self):
        p = self.asset_path()
        self.assertFalse(os.path.exists(p))
        out = image_gen.ensure_asset(GUID)
        self.assertEqual(out, p)
        self.assertTrue(os.path.exists(p))
        man = self.load_manifest()
        self.assertIn(GUID, man)
        e = man[GUID]
        self.assertEqual(e['design_version'], 'test-v1')
        self.assertEqual(e['asset_hash'], image_gen.build_asset_hash(GUID))
        self.assertIn('generated_at', e)
        self.assertEqual(e['path'], '/'.join(['feed', 'images', IMG_NAME + '.png']))

    # --- Test 2: PNG exists + same DESIGN_VERSION -> skip ---
    def test_2_exists_same_version_skips(self):
        p = self.asset_path()
        image_gen.ensure_asset(GUID)
        hash_before = self.load_manifest()[GUID]['asset_hash']
        size_before = os.path.getsize(p)
        old_generated = self.load_manifest()[GUID]['generated_at']
        out = image_gen.ensure_asset(GUID)
        self.assertEqual(out, p)
        self.assertFalse(image_gen.needs_regeneration(GUID, image_gen.load_manifest()))
        man = self.load_manifest()
        self.assertEqual(man[GUID]['asset_hash'], hash_before)
        self.assertEqual(man[GUID]['generated_at'], old_generated)
        self.assertEqual(os.path.getsize(p), size_before)

    # --- Test 3: DESIGN_VERSION bumped -> PNG reissued + hash changed ---
    def test_3_version_bump_reissues(self):
        p = self.asset_path()
        image_gen.ensure_asset(GUID)
        first_hash = self.load_manifest()[GUID]['asset_hash']
        image_gen.DESIGN_VERSION = 'test-v2'
        self.assertTrue(image_gen.needs_regeneration(GUID, image_gen.load_manifest()))
        image_gen.ensure_asset(GUID)
        man = self.load_manifest()
        self.assertEqual(man[GUID]['design_version'], 'test-v2')
        self.assertNotEqual(man[GUID]['asset_hash'], first_hash)
        self.assertTrue(os.path.exists(p))

    # --- Test 4: repeated run -> 0 regenerated ---
    def test_4_repeat_run_regen_zero(self):
        image_gen.ensure_asset(GUID)
        first_generated = self.load_manifest()[GUID]['generated_at']
        image_gen.ensure_asset(GUID)
        image_gen.ensure_asset(GUID)
        self.assertEqual(self.load_manifest()[GUID]['generated_at'], first_generated)
        self.assertFalse(image_gen.needs_regeneration(GUID, image_gen.load_manifest()))


def json_load(stream):
    import json
    return json.load(stream)


if __name__ == '__main__':
    unittest.main()