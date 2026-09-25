# image_gen.py - RED FIELD cover generator (standards/red-field-visual.md).
# Black field + red signal + human silhouette + ONE physical conflict.
# NO text on the image. White is forbidden. Palette per standard.
# Usage:
#   python image_gen.py                  (rebuild stale assets only)
#   python image_gen.py --verify         (report OK/REGEN; exit 1 if any stale)
#   python image_gen.py --rebuild        (regenerate stale assets only)
#   python image_gen.py --force          (full rebuild of all assets)
#   python image_gen.py --guid UID       (limit to a single slot)
#
# Version-aware idempotency (standard, decision 13.09 + 19.09.2026):
#   CONTENT_ID = stable slot guid.
#   DESIGN_VERSION = explicit visual-language version; ANY visual change bumps it.
#   ASSET_HASH = sha256(CONTENT_ID + ":" + DESIGN_VERSION).
#   manifest.json is the single source of truth:
#   { CONTENT_ID: {design_version, asset_hash, generated_at, path} }.
#   A PNG is skipped ONLY if the file exists AND manifest entry matches
#   DESIGN_VERSION + ASSET_HASH. Otherwise regenerate (old file -> backup).
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 630
OUT_DIR = os.path.join(os.path.dirname(__file__), 'images')
ITEMS_CSV = os.path.join(os.path.dirname(__file__), 'items.csv')
CONCEPTS_FILE = os.path.join(os.path.dirname(__file__), 'concepts.json')
MANIFEST = os.path.join(OUT_DIR, 'manifest.json')
BACKUP_ROOT = os.path.join(OUT_DIR, 'backup-red-field')
# red-field-v7 = visual language change: арт-директор (объект на новость), notrinsic
# картины-силуэты. ЛЮБАЯ смена визуального языка машины требует бампа версии.
DESIGN_VERSION = 'red-field-v7'

VOID = (0, 0, 0)
DEEP_RED = (24, 0, 0)
SIGNAL_RED = (101, 0, 0)
ACTIVE_RED = (176, 0, 0)
HOT_RED = (255, 26, 26)
SILH = (6, 0, 0)

# guid -> serial conflict. Each conflict = one physical idea.
# Every guid in feed/items.csv MUST have its own entry (fallback only as guard).
# Neighbouring dates get different conflicts so the series never clones shots.
CONFLICT_MAP = {
    # --- epoch 1 (04-22.09, re-issued as RED FIELD) ---
    'fitoussi-human-preference-2026-09-04': 'choice',
    'umg-elevenlabs-2026-09-10': 'split',
    'voice-scams-trust-2026-09-11': 'attack',
    'kto-proveril-golos-2026-09-12': 'trust',
    'golos-banka-2026-09-13': 'interface',
    'vybor-diktora-2026-09-14': 'choice',
    'ozvuchka-video-2026-09-15': 'deficit',
    'umg-infrastruktura-2026-09-16': 'infrastructure',
    'golos-pult-2026-09-17': 'interface',
    'pravovoy-sloy-golosa-2026-09-18': 'right',
    'radio-ne-umret-2026-09-19': 'power',
    'slepoj-test-golosa-2026-09-20': 'split',
    'aktery-protiv-klonov-2026-09-21': 'right',
    'open-source-golos-2026-09-22': 'deficit',
    # --- epoch 2 (23-30.09 re-release) ---
    'slepoi-test-2026-09-23': 'trust',
    'podkast-i-radio-2026-09-24': 'attention',
    'golos-kak-povedenie-2026-09-25': 'provenance',
    'pervaya-sekunda-banka-2026-09-26': 'interface',
    'eksport-govorit-2026-09-27': 'deficit',
    'muzej-govorit-2026-09-28': 'memory',
    'meropriyatiya-govoryat-2026-09-29': 'infrastructure',
    'itog-sentyabrya-2026-09-30': 'split',
    # --- epoch 3 (October) ---
    'golos-pervaya-sekunda-2026-10-01': 'attention',
    'doverie-intonaciya-2026-10-02': 'trust',
    'doverie-intonaciya-2026-10-03': 'trust',
    'muzej-golos-2026-10-04': 'memory',
    'eksport-golos-2026-10-05': 'power',
    'ivr-uderzhanie-2026-10-06': 'interface',
    'itog-nedeli-2026-10-07': 'split',
    'after-red-field-2026-10-08': 'attention',
    'podkast-i-radio-2026-10-09': 'provenance',
    'golos-kak-povedenie-2026-10-10': 'attention',
    'pervaya-sekunda-banka-2026-10-11': 'interface',
    'eksport-golos-2026-10-12': 'power',
    'muzej-golos-2026-10-13': 'memory',
    'itog-nedeli-2026-10-14': 'attention',
    'uderzhanie-na-linii-2026-10-15': 'interface',
    'golos-i-cifra-2026-10-16': 'interface',
    'dzen-i-golos-2026-10-17': 'attention',
    'tishina-v-efire-2026-10-18': 'trust',
    'bank-govorit-scenarij-2026-10-19': 'attention',
    'eksport-i-akcent-2026-10-20': 'provenance',
    'itog-nedeli-2026-10-21': 'split',
    # --- the fixed open-source-golos slot (23.09) ---
    'open-source-golos-2026-09-23': 'deficit',
}


def key_of(guid: str) -> str:
    for k, v in CONFLICT_MAP.items():
        if k in guid:
            return v
    return 'trust'


def conflict_of(guid: str) -> str:
    return CONFLICT_MAP.get(guid, key_of(guid))


def build_asset_hash(content_id: str) -> str:
    """ASSET_HASH = sha256(CONTENT_ID + ':' + DESIGN_VERSION)."""
    return hashlib.sha256(
        (content_id + ':' + DESIGN_VERSION).encode('utf-8')
    ).hexdigest()


def load_manifest() -> dict:
    """manifest.json is the single source of truth.
    Format: { CONTENT_ID: {design_version, asset_hash, generated_at, path} }."""
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_manifest(m: dict):
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def backup_old(img_path: str):
    if not os.path.exists(img_path):
        return
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    dest_dir = os.path.join(BACKUP_ROOT, stamp)
    os.makedirs(dest_dir, exist_ok=True)
    name = os.path.basename(img_path)
    os.replace(img_path, os.path.join(dest_dir, name))


def entry_for(content_id: str, seed: int) -> dict:
    name = img_name_for(content_id)
    entry = {
        'design_version': DESIGN_VERSION,
        'asset_hash': build_asset_hash(content_id),
        'generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'path': '/'.join(['feed', 'images', name + '.png']),
    }
    vo = object_of(content_id)
    if vo:
        entry['visual_object'] = vo
    return entry


def render_asset(content_id: str) -> str:
    """Render a single asset (always regenerates). Returns the PNG path."""
    name = img_name_for(content_id)
    seed = int(re.sub(r'\D', '', content_id) or 0)
    out = os.path.join(OUT_DIR, name + '.png')
    conflict = conflict_of(content_id)
    img = cover_auto(content_id, seed=seed)
    backup_old(out)
    img.save(out, 'PNG')
    vo = object_of(content_id)
    print('COVER GEN ' + name + ' conflict=' + conflict +
          (' object="%s"' % vo if vo else ''))
    return out


def needs_regeneration(content_id: str, manifest: dict) -> bool:
    """True if the asset must be regenerated: absent file, missing entry,
    changed DESIGN_VERSION, or ASSET_HASH mismatch."""
    name = img_name_for(content_id)
    out = os.path.join(OUT_DIR, name + '.png')
    if not os.path.exists(out):
        return True
    entry = manifest.get(content_id)
    if not entry:
        return True
    if entry.get('design_version') != DESIGN_VERSION:
        return True
    if entry.get('asset_hash') != build_asset_hash(content_id):
        return True
    return False


def ensure_asset(content_id: str, force: bool = False) -> str:
    """Version-aware asset idempotency. Returns the path of the current PNG.

    Contract: 'file exists -> skip' is FORBIDDEN. An asset is current only if
    file exists AND manifest entry matches DESIGN_VERSION + ASSET_HASH.
    """
    man = load_manifest()
    if not force and not needs_regeneration(content_id, man):
        return os.path.join(OUT_DIR, img_name_for(content_id) + '.png')
    out = render_asset(content_id)
    seed = int(re.sub(r'\D', '', content_id) or 0)
    man[content_id] = entry_for(content_id, seed)
    save_manifest(man)
    return out


class RGBA:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.layer)

    def ellipse(self, box, fill=None, outline=None, width=0):
        self.d.ellipse(box, fill=fill, outline=outline, width=width)

    def polygon(self, pts, fill, outline=None):
        self.d.polygon(pts, fill=fill, outline=outline)

    def line(self, pts, fill, width=1):
        self.d.line(pts, fill=fill, width=width)

    def rectangle(self, box, fill=None, outline=None, width=1):
        self.d.rectangle(box, fill=fill, outline=outline, width=width)

    def blur(self, r):
        self.layer = self.layer.filter(ImageFilter.GaussianBlur(r))
        return self

    def alpha(self, a):
        arr = np.array(self.layer)
        arr[..., 3] = (arr[..., 3].astype(np.float64) * a).astype(np.uint8)
        self.layer = Image.fromarray(arr, 'RGBA')
        return self


def vgrad_rgb():
    top = np.array(VOID, dtype=np.float64)
    bot = np.array((12, 0, 0), dtype=np.float64)
    rows = np.linspace(0, 1, H)[:, None, None]
    arr = (top[None, None, :] * (1 - rows) + bot[None, None, :] * rows)
    arr = arr.astype(np.uint8)
    return Image.fromarray(np.repeat(arr, W, axis=1), 'RGB').convert('RGBA')


def base_canvas():
    return vgrad_rgb()


def silhouette_layer(cx, cy, scale=1.0, fill=SILH, alpha=1.0):
    g = RGBA()
    s = scale
    # torso
    left = cx - 130 * s
    right = cx + 130 * s
    top = cy - 210 * s
    bot = cy + 250 * s
    shoulder_y = cy - 120 * s
    waist_w = 62 * s
    neck_w = 34 * s
    g.polygon([
        (left, top + 40 * s), (right, top + 40 * s),
        (right - (130 - waist_w) * 0.5, shoulder_y + 60 * s),
        (cx + waist_w, bot), (cx - waist_w, bot),
        (left + (130 - waist_w) * 0.5, shoulder_y + 60 * s),
    ], fill=fill)
    # head
    head_r = 52 * s
    g.ellipse((cx - head_r, cy - 300 * s, cx + head_r, cy - 300 * s + head_r * 2), fill=fill)
    # neck
    g.rectangle((cx - neck_w / 2, cy - 250 * s, cx + neck_w / 2, top + 40 * s), fill=fill)
    if alpha < 1.0:
        g.alpha(alpha)
    return g.layer


def draw_silhouette_rgba(img, cx, cy, scale=1.0, alpha=1.0):
    img.alpha_composite(silhouette_layer(cx, cy, scale, alpha=alpha))


def red_glow_bg(img, cx, cy, rx=620, ry=420, color=ACTIVE_RED, strength=0.35):
    g = RGBA()
    g.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=color + (255,))
    g.blur(220).alpha(strength)
    img.alpha_composite(g.layer)


def r01(seed: int, salt: int) -> float:
    """Deterministic pseudo-random in [0,1) from seed+salt (sha256, no collisions)."""
    h = hashlib.sha256(('%d:%d' % (seed, salt)).encode('utf-8')).hexdigest()
    return int(h[:8], 16) / float(0xffffffff)


def jitter(seed: int, spread: int, salt: int) -> int:
    return int((r01(seed, salt) - 0.5) * 2 * spread)


# --- Арт-директор. IMAGE_CONCEPT вместо CONFLICT_MAP: у каждой новости свой
# --- визуальный ОБЪЕКТ (один предмет), красный - акцент, а не заливка.
# --- Правила: изъять предмет; если предмет уже похож на одну из последних
# --- 20 обложек - твист кадра (другой объект/ракурс); один объект на кадр.

CONCEPTS = None


def load_concepts() -> dict:
    global CONCEPTS
    if CONCEPTS is None:
        CONCEPTS = {}
        if os.path.exists(CONCEPTS_FILE):
            try:
                with open(CONCEPTS_FILE, 'r', encoding='utf-8') as f:
                    CONCEPTS = json.load(f)
            except Exception:
                CONCEPTS = {}
    return CONCEPTS


def dhash(img, size=17):
    """Difference-hash of a PIL image (grayscale). size=17 -> 272 bits,
    fine enough to tell apart objects on a black+red field."""
    g = img.convert('L').resize((size, size + 1), Image.LANCZOS)
    px = list(g.getdata())
    w, h = g.size
    bits = 0
    for y in range(h - 1):
        for x in range(w):
            bits = (bits << 1) | (1 if px[y * w + x] > px[(y + 1) * w + x] else 0)
    return bits


def hamming(a, b):
    return bin(a ^ b).count('1')


# Similarity threshold for objects on a black field: 8% of bits flipped
# ≈ same object, different arrangement. Different objects are much further.
UNIQ_THRESHOLD = int(17 * 17 * 0.08)


def last_20_hashes() -> list:
    """dHash of the 20 most-recently-generated PNGs falling back to by-name order."""
    try:
        return load_last_20_hashes()
    except Exception:
        return []


def load_last_20_hashes():
    hashes = []
    files = []
    if os.path.isdir(OUT_DIR):
        for fn in os.listdir(OUT_DIR):
            if fn.endswith('.png'):
                files.append(fn)
    files.sort(key=lambda fn: os.path.getmtime(os.path.join(OUT_DIR, fn)), reverse=True)
    for fn in files[:20]:
        try:
            hashes.append(dhash(Image.open(os.path.join(OUT_DIR, fn))))
        except Exception:
            pass
    return hashes


def _obj_atom(x, y, w, h):
    return (x, y, x + w, y + h)


def render_object(concept: dict, seed: int, attempt: int = 0):
    """Draw ONE visual object per news. Red = accent, never the whole image."""
    img = base_canvas()
    cx = W / 2 + jitter(seed, 60, 101) + attempt * 7
    cy = 415 + jitter(seed, 30, 102) + attempt * 5
    off = jitter(seed, 60, 103) + attempt * 11
    obj = (concept.get('visual_object') or '').lower()

    if 'маск' in obj:
        # треснувшая театральная маска с одной красной нитью
        w, h = 340, 300
        g = RGBA()
        g.polygon([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                   (cx + w / 2 + 90, cy + h / 2), (cx - w / 2 + 40, cy + h / 2)], fill=DEEP_RED + (255,))
        g.ellipse(_obj_atom(cx - 92, cy - 150, 70, 110), fill=VOID + (255,))
        g.ellipse(_obj_atom(cx + 20, cy - 150, 70, 110), fill=VOID + (255,))
        g.line([(cx + 40, cy - 60), (cx + 130, cy + 40), (cx + 250, cy + 60)], ACTIVE_RED + (255,), width=7)
        g.blur(10).alpha(0.92)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.line([(cx + 250, cy + 60), (cx + 320, cy - 120), (cx + 380, cy - 40)],
                HOT_RED + (255,), width=4)
        g2.blur(3).alpha(1.0)
        img.alpha_composite(g2.layer)
        g3 = RGBA()
        g3.ellipse(_obj_atom(cx + 220, cy - 220, 26, 26), fill=HOT_RED + (255,))
        g3.blur(12).alpha(0.9)
        img.alpha_composite(g3.layer)

    elif 'трубк' in obj or 'секунд' in obj:
        # телефонная трубка + циферблат с красным попаданием секунды
        g = RGBA()
        g.polygon([(cx - 300, cy - 140), (cx - 160, cy - 200), (cx - 120, cy - 60),
                   (cx - 260, cy + 20), (cx - 320, cy - 40)], fill=DEEP_RED + (255,))
        g.ellipse(_obj_atom(cx + 60, cy - 240, 260, 260), outline=ACTIVE_RED + (255,), width=8)
        for a in range(12):
            import math
            ang = a * math.pi / 6
            x0 = cx + 190 + 115 * math.cos(ang)
            y0 = cy - 110 + 115 * math.sin(ang)
            x1 = cx + 190 + 130 * math.cos(ang)
            y1 = cy - 110 + 130 * math.sin(ang)
            g.line([(x0, y0), (x1, y1)], SIGNAL_RED + (255,), width=4)
        g.line([(cx + 190, cy - 110), (cx + 190 + 110, cy - 110)], HOT_RED + (255,), width=6)
        g.blur(6).alpha(0.95)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse(_obj_atom(cx + 300, cy - 130, 46, 46), fill=HOT_RED + (255,))
        g2.blur(20).alpha(0.85)
        img.alpha_composite(g2.layer)

    elif 'компас' in obj or 'стрелк' in obj:
        # компасная стрелка указывает на звуковую волну за линией
        g = RGBA()
        g.ellipse(_obj_atom(cx - 300, cy - 260, 380, 380), outline=SIGNAL_RED + (255,), width=6)
        g.polygon([(cx - 260, cy - 20), (cx - 170, cy - 70), (cx + 220, cy - 6),
                   (cx - 170, cy + 70)], fill=DEEP_RED + (255,))
        g.polygon([(cx - 200, cy - 8), (cx - 120, cy - 30), (cx + 100, cy - 4),
                   (cx - 120, cy + 50)], fill=VOID + (255,))
        g.line([(cx + 130, cy - 4), (cx + 250, cy - 4)], HOT_RED + (255,), width=5)
        for i in range(3):
            g.line([(cx + 100 + i * 60, cy - 140), (cx + 100 + i * 60, cy - 40)],
                   (ACTIVE_RED if i % 2 else SIGNAL_RED) + (255,), width=4)
        g.blur(5).alpha(0.95)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse(_obj_atom(cx + 150, cy - 170, 40, 40), fill=HOT_RED + (255,))
        g2.blur(24).alpha(0.9)
        img.alpha_composite(g2.layer)

    elif 'граммофон' in obj or 'раструб' in obj:
        # граммофон: из раструба выходит красная волна
        g = RGBA()
        g.polygon([(cx - 300, cy - 40), (cx + 260, cy - 250), (cx + 300, cy - 150),
                   (cx - 260, cy + 60)], fill=DEEP_RED + (255,))
        g.polygon([(cx - 320, cy - 90), (cx - 250, cy - 70), (cx - 250, cy + 120),
                   (cx - 320, cy + 150)], fill=ACTIVE_RED + (255,))
        for i in range(4):
            yy = cy - 40 + i * 70
            g.line([(cx - 300, yy + 50), (cx + 250, yy)], (ACTIVE_RED if i % 2 else SIGNAL_RED) + (255,), width=5)
        g.blur(6).alpha(0.95)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        for i in range(3):
            g2.line([(cx + 240, cy - 180 - i * 40), (cx + 340, cy - 220 - i * 40)],
                    (HOT_RED if i == 1 else ACTIVE_RED) + (255,), width=4)
        g2.blur(4).alpha(1.0)
        img.alpha_composite(g2.layer)
        g3 = RGBA()
        g3.ellipse(_obj_atom(cx + 320, cy - 280, 34, 34), fill=HOT_RED + (255,))
        g3.blur(18).alpha(0.9)
        img.alpha_composite(g3.layer)

    elif 'микрофон' in obj or 'стойк' in obj:
        # стоечный микрофон: один красный акцент-кольцо
        g = RGBA()
        g.ellipse(_obj_atom(cx - 130, cy - 200, 200, 200), fill=DEEP_RED + (255,))
        g.ellipse(_obj_atom(cx - 90, cy - 160, 120, 120), fill=VOID + (255,))
        g.line([(cx + 60, cy - 20), (cx + 60, cy + 250)], ACTIVE_RED + (255,), width=16)
        g.line([(cx + 60, cy + 250), (cx + 190, cy + 250)], DEEP_RED + (255,), width=18)
        g.line([(cx + 190, cy + 250), (cx + 260, cy + 250)], DEEP_RED + (255,), width=18)
        g.blur(6).alpha(0.95)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse(_obj_atom(cx - 110, cy - 180, 160, 160), outline=HOT_RED + (255,), width=7)
        g2.blur(3).alpha(1.0)
        img.alpha_composite(g2.layer)
        g3 = RGBA()
        g3.ellipse(_obj_atom(cx + 20, cy - 130, 60, 60), fill=HOT_RED + (255,))
        g3.blur(30).alpha(0.7)
        img.alpha_composite(g3.layer)

    elif 'календар' in obj or 'лист' in obj:
        # перевернутый лист календаря с красной датой
        g = RGBA()
        g.polygon([(cx - 260, cy - 200), (cx + 60, cy - 200), (cx + 40, cy + 200),
                   (cx - 280, cy + 200)], fill=DEEP_RED + (255,))
        g.polygon([(cx + 60, cy - 200), (cx + 260, cy - 160), (cx + 240, cy + 240),
                   (cx + 40, cy + 200)], fill=SIGNAL_RED + (255,))
        g.line([(cx - 100, cy - 120), (cx + 60, cy - 120)], ACTIVE_RED + (255,), width=6)
        g.line([(cx - 100, cy - 40), (cx + 60, cy - 40)], ACTIVE_RED + (255,), width=6)
        g.line([(cx + 100, cy - 90), (cx + 220, cy - 70)], SIGNAL_RED + (255,), width=6)
        g.blur(6).alpha(0.95)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse(_obj_atom(cx + 120, cy - 80, 48, 48), fill=HOT_RED + (255,))
        g2.blur(20).alpha(0.9)
        img.alpha_composite(g2.layer)

    elif 'импульс' in obj or 'волн' in obj:
        # один импульс, вырвавшийся из тишины
        g = RGBA()
        g.line([(cx - 330, cy + 70), (cx + 320, cy + 70)], SIGNAL_RED + (255,), width=6)
        g.line([(cx - 260, cy + 70), (cx + 40, cy - 280), (cx + 160, cy + 70)], ACTIVE_RED + (255,), width=12)
        g.line([(cx + 160, cy + 70), (cx + 230, cy - 100), (cx + 320, cy + 70)], SIGNAL_RED + (255,), width=7)
        g.line([(cx + 40, cy - 280), (cx + 10, cy - 200)], HOT_RED + (255,), width=10)
        g.blur(5).alpha(0.95)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse(_obj_atom(cx + 30, cy - 310, 40, 40), fill=HOT_RED + (255,))
        g2.blur(22).alpha(0.9)
        img.alpha_composite(g2.layer)

    elif 'ухо' in obj or 'интонац' in obj:
        # ухо в профиль, внутрь входит красная линия
        g = RGBA()
        g.ellipse(_obj_atom(cx - 190, cy - 240, 340, 400), outline=ACTIVE_RED + (255,), width=10)
        g.ellipse(_obj_atom(cx - 130, cy - 160, 200, 240), outline=SIGNAL_RED + (255,), width=7)
        g.line([(cx - 270, cy - 60), (cx - 170, cy - 110), (cx - 120, cy - 60),
                (cx - 150, cy + 40), (cx - 80, cy + 60)], ACTIVE_RED + (255,), width=6)
        g.blur(4).alpha(0.95)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.line([(cx - 280, cy + 80), (cx - 120, cy + 60), (cx - 40, cy - 80)], HOT_RED + (255,), width=5)
        g2.blur(3).alpha(1.0)
        img.alpha_composite(g2.layer)
        g3 = RGBA()
        g3.ellipse(_obj_atom(cx - 300, cy + 10, 34, 34), fill=HOT_RED + (255,))
        g3.blur(18).alpha(0.9)
        img.alpha_composite(g3.layer)

    else:
        # запасной объект: единственный силуэт, красный контур (не заливка)
        draw_silhouette_rgba(img, cx, cy, 1.0)
        g = RGBA()
        g.ellipse(_obj_atom(cx - 120, cy - 320, 240, 300), outline=ACTIVE_RED + (255,), width=4)
        g.blur(3).alpha(0.8)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse(_obj_atom(cx - 26, cy - 46, 52, 52), fill=HOT_RED + (255,))
        g2.blur(30).alpha(0.8)
        img.alpha_composite(g2.layer)

    out = Image.alpha_composite(img, Image.new('RGBA', (W, H), (0, 0, 0, 0)))
    return out.convert('RGB')


def render_object_with_uniqueness(concept: dict, seed: int):
    """Render object; if too close to any of the last 20 covers, twist the frame."""
    recent = last_20_hashes()
    for attempt in range(6):
        img = render_object(concept, seed, attempt)
        h = dhash(img)
        similar = any(hamming(h, x) < UNIQ_THRESHOLD for x in recent)
        if not similar:
            return img, attempt
    return img, 5  # accept last attempt even if still similar


def object_of(guid: str):
    concepts = load_concepts()
    if guid in concepts:
        return concepts[guid].get('visual_object', '')
    return ''


def cover_auto(guid: str, seed: int = 0):
    """Art-director dispatch: object cover if concept exists, else legacy conflict."""
    concepts = load_concepts()
    if guid in concepts:
        concept = concepts[guid]
        img, _attempt = render_object_with_uniqueness(concept, seed)
        return img
    return cover(conflict_of(guid), seed=seed)


def cover(conflict: str, seed: int = 0):
    img = base_canvas()
    cx, cy = W / 2 + jitter(seed, 60, 1), 430 + jitter(seed, 40, 2)

    if conflict == 'choice':
        # several possible versions of one voice: silhouette between red fields
        red_glow_bg(img, cx, cy, 500, 400, ACTIVE_RED, 0.16)
        for i, off in enumerate((-330, -180, 180, 330)):
            g = RGBA()
            x = cx + off
            g.ellipse((x - 74, cy - 300, x + 74, cy + 60), fill=SIGNAL_RED + (255,))
            g.ellipse((x - 30, cy - 240, x + 30, cy + 30), fill=(255 + (i * 30) % 90, 0, 0, 255))
            g.blur(46).alpha(0.55)
            img.alpha_composite(g.layer)
        draw_silhouette_rgba(img, cx, cy, 1.0)

    elif conflict == 'split':
        # market split: two red poles, silhouette between
        red_glow_bg(img, cx, cy, 480, 420, SIGNAL_RED, 0.12)
        for side in (-1, 1):
            g = RGBA()
            x = cx + side * 330
            g.polygon([(x - 130, 0), (x + 40, 0), (x - 40, H), (x - 210, H)], fill=ACTIVE_RED + (255,))
            g.blur(60).alpha(0.4)
            img.alpha_composite(g.layer)
        draw_silhouette_rgba(img, cx, cy, 0.95)

    elif conflict == 'right':
        # legal boundary around the person: the right is a frame, not a colour
        red_glow_bg(img, cx, cy, 520, 440, DEEP_RED, 0.5)
        g = RGBA()
        g.rectangle((cx - 220, cy - 360, cx + 220, cy + 260), fill=None,
                    outline=ACTIVE_RED + (255,), width=6)
        g.rectangle((cx - 200, cy - 340, cx + 200, cy + 240), fill=None,
                    outline=SIGNAL_RED + (255,), width=2)
        g.alpha(0.8)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.line([(cx - 300, cy + 320), (cx + 300, cy + 320)], HOT_RED + (255,), width=3)
        g2.alpha(0.6)
        img.alpha_composite(g2.layer)
        draw_silhouette_rgba(img, cx, cy, 0.92)

    elif conflict == 'trust':
        # clean dark space, thin red halo, nothing extra
        red_glow_bg(img, cx, cy, 420, 380, SIGNAL_RED, 0.22)
        g = RGBA()
        g.ellipse((cx - 250, cy - 420, cx + 250, cy + 330), fill=None,
                  outline=ACTIVE_RED + (255,), width=3)
        g.blur(2).alpha(0.55)
        img.alpha_composite(g.layer)
        draw_silhouette_rgba(img, cx, cy, 1.0)
        g2 = RGBA()
        g2.ellipse((cx - 260, cy - 430, cx + 260, cy + 340), fill=None,
                   outline=HOT_RED + (255,), width=2)
        g2.blur(4).alpha(0.25)
        img.alpha_composite(g2.layer)

    elif conflict == 'attention':
        # point where voice passes inspection: red burst at the head
        red_glow_bg(img, cx, cy, 460, 420, ACTIVE_RED, 0.5)
        for k, r in enumerate((70, 120, 180, 250, 330)):
            g = RGBA()
            g.ellipse((cx - r, cy - 300 - r, cx + r, cy - 300 + r), fill=None,
                      outline=(HOT_RED if k < 3 else ACTIVE_RED) + (255,), width=4 - (k // 3))
            g.blur(4).alpha(0.7 - k * 0.1)
            img.alpha_composite(g.layer)
        gbg = RGBA()
        gbg.ellipse((cx - 90, cy - 360, cx + 90, cy - 180), fill=HOT_RED + (255,))
        gbg.blur(30).alpha(0.55)
        img.alpha_composite(gbg.layer)
        draw_silhouette_rgba(img, cx, cy, 0.98)
        g2 = RGBA()
        g2.ellipse((cx - 34, cy - 334, cx + 34, cy - 266), fill=HOT_RED + (255,))
        g2.blur(18).alpha(0.85)
        img.alpha_composite(g2.layer)

    elif conflict == 'interface':
        # gesture -> reaction in space: line from hand into red field
        red_glow_bg(img, cx, cy, 520, 430, DEEP_RED, 0.45)
        g = RGBA()
        g.line([(cx + 60, cy - 40), (cx + 330, cy - 140)], HOT_RED + (255,), width=4)
        g.line([(cx + 60, cy - 40), (cx + 330, cy - 20)], ACTIVE_RED + (255,), width=3)
        g.ellipse((cx + 300, cy - 180, cx + 400, cy - 60), fill=ACTIVE_RED + (255,))
        g.blur(8).alpha(0.85)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse((cx + 330, cy - 130, cx + 480, cy + 60), fill=SIGNAL_RED + (255,))
        g2.blur(70).alpha(0.5)
        img.alpha_composite(g2.layer)
        draw_silhouette_rgba(img, cx, cy, 1.0)

    elif conflict == 'deficit':
        # small person, big space, something missing
        red_glow_bg(img, cx + 320, cy + 220, 300, 260, ACTIVE_RED, 0.4)
        g = RGBA()
        g.ellipse((W - 220, 60, W - 60, 220), fill=ACTIVE_RED + (255,))
        g2 = RGBA()
        g2.ellipse((W - 180, 100, W - 100, 180), fill=HOT_RED + (255,))
        g.blur(60).alpha(0.65)
        img.alpha_composite(g.layer)
        g2.blur(18).alpha(0.75)
        img.alpha_composite(g2.layer)
        draw_silhouette_rgba(img, cx - 260, cy - 60, 0.42, alpha=0.9)

    elif conflict == 'infrastructure':
        # red lines BEHIND the person, not over: person inside the system
        red_glow_bg(img, cx, cy, 560, 460, ACTIVE_RED, 0.4)
        for i, yy in enumerate(range(120, H, 90)):
            g = RGBA()
            g.line([(0, yy), (W, yy)], (ACTIVE_RED if i % 2 else SIGNAL_RED) + (255,), width=4 - (i % 2))
            g.line([(0, yy + 4), (W, yy + 4)], (HOT_RED if i % 2 else ACTIVE_RED) + (255,), width=2)
            g.blur(2).alpha(0.8)
            img.alpha_composite(g.layer)
        draw_silhouette_rgba(img, cx, cy, 1.0)

    elif conflict == 'power':
        # rising red field from below, person above it
        g = RGBA()
        g.polygon([(0, H), (0, 360), (W, 180), (W, H)], fill=ACTIVE_RED + (255,))
        g.blur(90).alpha(0.6)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.line([(0, 330), (W, 160)], HOT_RED + (255,), width=2)
        g2.blur(4).alpha(0.7)
        img.alpha_composite(g2.layer)
        draw_silhouette_rgba(img, cx, cy - 40, 1.15)

    elif conflict == 'attack':
        # red wedge approaching the silhouette from lower-left
        red_glow_bg(img, cx, cy, 520, 430, DEEP_RED, 0.35)
        g = RGBA()
        g.polygon([(0, H), (cx - 60, cy + 40), (cx - 40, cy + 220), (0, H + 200)], fill=HOT_RED + (255,))
        g.polygon([(0, H - 40), (cx - 120, cy + 80), (cx - 90, cy + 300), (0, H + 40)], fill=ACTIVE_RED + (255,))
        g.blur(26).alpha(0.7)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.polygon([(0, H - 10), (cx - 100, cy + 30), (cx - 80, cy + 260)], fill=HOT_RED + (255,))
        g2.blur(14).alpha(0.5)
        img.alpha_composite(g2.layer)
        draw_silhouette_rgba(img, cx, cy, 0.95)

    elif conflict == 'provenance':
        # the person and his copy: two layers, source ahead
        red_glow_bg(img, cx, cy, 520, 440, ACTIVE_RED, 0.3)
        draw_silhouette_rgba(img, cx + 190, cy + 60, 1.0, alpha=0.35)
        draw_silhouette_rgba(img, cx - 40, cy - 20, 0.9, alpha=0.8)
        g = RGBA()
        g.line([(cx - 250, cy + 40), (cx + 60, cy + 40)], ACTIVE_RED + (255,), width=3)
        g.blur(4).alpha(0.8)
        img.alpha_composite(g.layer)
        g2 = RGBA()
        g2.ellipse((cx + 100, cy + 0, cx + 260, cy + 120), fill=SIGNAL_RED + (255,))
        g2.blur(40).alpha(0.6)
        img.alpha_composite(g2.layer)
        draw_silhouette_rgba(img, cx - 200, cy + 10, 1.0)

    elif conflict == 'memory':
        # museum / memory: layered traces of former voices fading backwards
        red_glow_bg(img, cx, cy, 560, 450, ACTIVE_RED, 0.45)
        for i, off in enumerate((-340, -220, -100)):
            g = RGBA()
            x = W / 2 + off
            g.ellipse((x - 300, 0, x + 300, H), fill=SIGNAL_RED + (255,))
            g.ellipse((x - 150, 60, x + 150, H - 60), fill=(HOT_RED if i == 2 else ACTIVE_RED) + (255,))
            g.blur(70).alpha(0.22 + i * 0.1)
            img.alpha_composite(g.layer)
        draw_silhouette_rgba(img, cx + 140, cy + 40, 0.8, alpha=0.35)
        draw_silhouette_rgba(img, cx + 40, cy + 15, 0.9, alpha=0.55)
        draw_silhouette_rgba(img, cx - 60, cy, 0.95, alpha=0.8)
        g = RGBA()
        g.line([(W / 2 - 380, cy + 330), (W / 2 + 380, cy + 330)], ACTIVE_RED + (255,), width=3)
        g.blur(4).alpha(0.5)
        img.alpha_composite(g.layer)

    else:
        red_glow_bg(img, cx, cy, 480, 400, ACTIVE_RED, 0.2)
        draw_silhouette_rgba(img, cx, cy, 1.0)

    out = Image.alpha_composite(img, Image.new('RGBA', (W, H), (0, 0, 0, 0)))
    out = out.convert('RGB')
    return out


def guids_from_csv():
    guids = []
    if not os.path.exists(ITEMS_CSV):
        return guids
    with open(ITEMS_CSV, 'r', encoding='utf-8-sig') as f:
        for row in f:
            row = row.rstrip('\r\n')
            if not row or row.startswith('TITLE~~~') or row.startswith('DESC~~~'):
                continue
            p = row.split('~~~')
            if len(p) >= 6 and p[4]:
                guids.append(p[4])
    return guids


def img_name_for(guid: str):
    with open(ITEMS_CSV, 'r', encoding='utf-8-sig') as f:
        for row in f:
            row = row.rstrip('\r\n')
            if not row or row.startswith('TITLE~~~') or row.startswith('DESC~~~'):
                continue
            p = row.split('~~~')
            if len(p) >= 6 and p[4] == guid:
                return p[5]
    return guid


def main():
    ap = argparse.ArgumentParser(description='RED FIELD cover generator')
    ap.add_argument('--verify', action='store_true',
                    help='report asset state (OK/REGEN); exit 1 if anything stale')
    ap.add_argument('--rebuild', action='store_true',
                    help='regenerate only stale assets (default)')
    ap.add_argument('--force', action='store_true',
                    help='full rebuild of all assets')
    ap.add_argument('--guid', default='', help='limit to a single slot guid')
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    targets = [args.guid] if args.guid else guids_from_csv()

    if args.verify:
        man = load_manifest()
        stale = 0
        for g in targets:
            name = img_name_for(g)
            if needs_regeneration(g, man):
                stale += 1
                print('REGEN ' + name)
            else:
                print('OK    ' + name)
        print('VERIFY stale=' + str(stale) + ' total=' + str(len(targets)))
        return 1 if stale else 0

    if args.force:
        for g in targets:
            try:
                ensure_asset(g, force=True)
            except Exception as e:
                print('COVER_ERR ' + g + ' :: ' + str(e))
        return 0

    for g in targets:
        try:
            ensure_asset(g)
        except Exception as e:
            print('COVER_ERR ' + g + ' :: ' + str(e))
    return 0


if __name__ == '__main__':
    sys.exit(main())