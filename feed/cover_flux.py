# -*- coding: utf-8 -*-
"""FLUX cover renderer via public Hugging Face Spaces (no API key).

Primary: black-forest-labs/FLUX.1-schnell (4 steps, fast, good prompt adherence).
Fallback: multimodalart/FLUX.1-merged (dev-based, 8 steps).
Fallback 2: Stable Horde (Juggernaut XL) when Spaces are down.

Usage:
  python feed/cover_flux.py --prompt "..." --out-name joe-rogan --audit
  python feed/cover_flux.py --guid <guid> --audit          # prompt from concepts.json image_prompt
"""
import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys
import time

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(REPO, 'feed')
CONCEPTS_FILE = os.path.join(FEED, 'concepts.json')
CAND_DIR = os.path.join(FEED, 'images', 'candidates')
W, H = 1200, 630
GEN_W, GEN_H = 1200, 640

PROXY_HTTP = 'http://127.0.0.1:10809'
CURL = r'C:\Windows\System32\curl.exe'
HORDE_BASE = 'https://stablehorde.net/api/v2'
HORDE_MODEL = 'Juggernaut XL'

os.environ.setdefault('HTTP_PROXY', PROXY_HTTP)
os.environ.setdefault('HTTPS_PROXY', PROXY_HTTP)
os.environ.setdefault('NO_PROXY', '127.0.0.1,localhost')

SPACES = [
    ('black-forest-labs/FLUX.1-schnell',
     dict(num_inference_steps=4)),
    ('multimodalart/FLUX.1-merged',
     dict(num_inference_steps=8, guidance_scale=3.5)),
]


def load_concepts():
    with io.open(CONCEPTS_FILE, encoding='utf-8') as f:
        return json.load(f)


def audit(img):
    problems = []
    a = np.asarray(img).astype(np.int16)
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
    if lum.mean() > 120:
        problems.append('too_bright mean=%.0f' % lum.mean())
    red = ((a[..., 0] > 110) & (a[..., 0] - a[..., 1] > 45) &
           (a[..., 0] - a[..., 2] > 45))
    if red.sum() < 350:
        problems.append('no_red_accent px=%d' % int(red.sum()))
    white = ((a[..., 0] > 215) & (a[..., 1] > 215) & (a[..., 2] > 215))
    if white.mean() > 0.12:
        problems.append('too_much_white')
    return ','.join(problems) if problems else None


def _crop_resize(img):
    if img.size != (GEN_W, GEN_H):
        img = img.resize((GEN_W, GEN_H), Image.LANCZOS)
    top = (GEN_H - H) // 2
    return img.crop((0, top, W, top + H))


def flux_space(prompt, seed, space, extra, timeout_note=''):
    from gradio_client import Client
    c = Client(space, verbose=False)
    kw = dict(seed=int(seed), randomize_seed=False, width=GEN_W, height=GEN_H)
    kw.update(extra)
    res = c.predict(prompt=prompt, api_name='/infer', **kw)
    path = res[0] if isinstance(res, tuple) else res
    if isinstance(path, dict):
        path = path.get('path')
    return Image.open(path).convert('RGB')


def horde(prompt, seed, timeout=600):
    def http(url, data=None, headers=None, t=90):
        args = [CURL, '-s', '-x', 'socks5h://127.0.0.1:10808', '--max-time', str(t),
                '-w', '\n%{http_code}']
        if headers:
            for k, v in headers.items():
                args += ['-H', k + ': ' + v]
        if data is not None:
            args += ['--data-binary', data]
        args.append(url)
        p = subprocess.run(args, capture_output=True)
        b = p.stdout
        code = ''
        if b'\n' in b:
            b, code = b.rsplit(b'\n', 1)
        return code.decode(), b

    payload = {
        'prompt': prompt,
        'params': {'width': GEN_W, 'height': GEN_H, 'steps': 28,
                   'sampler_name': 'k_euler', 'cfg_scale': 5.5, 'seed': str(seed)},
        'nsfw': False, 'models': [HORDE_MODEL], 'r2': True, 'shared': False,
    }
    code, body = http(HORDE_BASE + '/generate/async', json.dumps(payload).encode(),
                      {'apikey': '0000000000', 'Client-Agent': 'sonic-cover/2.0',
                       'Content-Type': 'application/json'})
    if code not in ('200', '202'):
        raise RuntimeError('horde submit ' + code + ': ' + body[:120])
    jid = json.loads(body)['id']
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(10)
        c2, b2 = http(HORDE_BASE + '/generate/check/' + jid, t=40)
        try:
            chk = json.loads(b2)
        except Exception:
            continue
        if chk.get('faulted'):
            raise RuntimeError('horde faulted')
        if chk.get('done'):
            c3, b3 = http(HORDE_BASE + '/generate/status/' + jid, t=60)
            gens = json.loads(b3).get('generations') or []
            if not gens:
                raise RuntimeError('horde no generation')
            ref = gens[0].get('img') or ''
            if ref.startswith('http'):
                c4, raw = http(ref, t=180)
                return Image.open(io.BytesIO(raw)).convert('RGB')
            return Image.open(io.BytesIO(base64.b64decode(ref))).convert('RGB')
    raise RuntimeError('horde timeout')


def render(prompt, seed, use_audit=False, attempts=3):
    last = 'none'
    for i in range(attempts):
        for space, extra in SPACES:
            try:
                img = _crop_resize(flux_space(prompt, seed + i * 131, space, extra))
                if not use_audit or audit(img) is None:
                    return img, '%s seed=%d' % (space, seed + i * 131)
                last = 'flux audit %s' % audit(img)
            except Exception as e:
                last = 'flux %s: %s' % (space.split('/')[-1], str(e)[:120])
            print('  attempt %d %s' % (i + 1, last))
            time.sleep(3)
    print('  flux exhausted (%s), horde fallback' % last[:100])
    for i in range(2):
        try:
            img = _crop_resize(horde(prompt, seed + i * 977))
            if not use_audit or audit(img) is None:
                return img, 'horde %s seed=%d' % (HORDE_MODEL, seed + i * 977)
            last = 'horde audit %s' % audit(img)
        except Exception as e:
            last = 'horde: ' + str(e)[:120]
        print('  horde attempt %d %s' % (i + 1, last))
    raise RuntimeError('render failed: ' + last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--guid')
    ap.add_argument('--prompt')
    ap.add_argument('--out-name')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--audit', action='store_true')
    ap.add_argument('--to-feed', action='store_true', help='also write feed/images/<name>.png')
    args = ap.parse_args()

    prompt = args.prompt
    name = args.out_name
    if args.guid:
        c = load_concepts().get(args.guid) or {}
        prompt = prompt or c.get('image_prompt') or c.get('cover_prompt')
        name = name or re.sub(r'-\d{4}-\d{2}-\d{2}$', '', args.guid)
    if not prompt:
        ap.error('need --prompt or --guid with image_prompt')
    if not name:
        name = 'cover_' + str(int(time.time()))
    name = re.sub(r'[^A-Za-z0-9._-]+', '-', name)

    print('PROMPT:', prompt)
    img, src = render(prompt, args.seed, args.audit)
    os.makedirs(CAND_DIR, exist_ok=True)
    out = os.path.join(CAND_DIR, name + '.png')
    img.save(out, 'PNG')
    print('CANDIDATE:', out, 'via', src, 'audit', audit(img) or 'OK')
    if args.to_feed:
        dst = os.path.join(FEED, 'images', name + '.png')
        img.save(dst, 'PNG')
        print('FEED:', dst)
    return 0


if __name__ == '__main__':
    sys.exit(main())
