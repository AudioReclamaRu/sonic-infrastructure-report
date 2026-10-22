# cover_ai.py - AI cover pipeline: unique prompt per article + FLUX render + aesthetic audit.
# Usage:
#   python feed\cover_ai.py --guid UID            (write image_prompt into concepts.json)
#   python feed\cover_ai.py --guid UID --render   (prompt + render candidate PNG)
#   python feed\cover_ai.py --all                 (fill missing image_prompt for all concepts)
# Candidates go to feed/images/candidates/ until promoted by manifest version bump.
import argparse
import base64
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(REPO, 'feed')
CONCEPTS_FILE = os.path.join(FEED, 'concepts.json')
CAND_DIR = os.path.join(FEED, 'images', 'candidates')
W, H = 1200, 630
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

TEXT_URL = 'https://text.pollinations.ai/openai'
IMAGE_BASE = 'https://image.pollinations.ai/prompt/'
HORDE_BASE = 'https://stablehorde.net/api/v2'
HORDE_MODEL = 'AlbedoBase XL (SDXL)'
HORDE_AGENT = 'sonic-cover-infra/1.0'

SYSTEM = (
    'You are the art director of Audio-Reclama.ru, an audio advertising media channel. '
    'You write image-generation prompts for article cover photos in the house style RED FIELD.\n'
    'Style contract (mandatory, every prompt):\n'
    '- near-black background field, cinematic darkness, subtle dark-red gradient allowed, no other bg colors;\n'
    '- ONE concrete hero object or minimal scene, quiet editorial photography, realistic materials, '
    'high detail, soft rim light, shallow depth of field, moody atmosphere;\n'
    '- exactly ONE red accent (glow, line, tick, thread, mark) that carries the story meaning; '
    'it must be a clearly visible saturated bright red glow or line, never thin, never dark, '
    'always the brightest colored element; always write the word "red" for it;\n'
    '- no white surfaces, no clutter, no logos, no watermark;\n'
    '- absolutely no text, no letters, no numbers, no typography in the image (say "no text" in the prompt);\n'
    '- landscape 1200x630 banner composition, rule of thirds, generous negative space on the left/right;\n'
    '- the object must be a physical metaphor of the article shift described in visual_object.\n'
    'Return ONLY a JSON object {"image_prompt": "..."} with the prompt in English, 55-105 words, '
    'starting directly with the scene description and ending with "No text."'
)


def load_concepts():
    with io.open(CONCEPTS_FILE, encoding='utf-8') as fh:
        return json.load(fh)


def save_concepts(concepts):
    with io.open(CONCEPTS_FILE, 'w', encoding='utf-8') as fh:
        json.dump(concepts, fh, ensure_ascii=False, indent=2)
        fh.write('\n')


def _http(url, data=None, headers=None, timeout=120):
    h = {'User-Agent': UA}
    if data is not None:
        h['Content-Type'] = 'application/json'
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    last = ''
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = str(e)
            if i < 2:
                time.sleep(30 if '402' in last else 4 * (i + 1))
    raise RuntimeError('http failed: ' + last[:200])


def llm_json(user_text):
    payload = json.dumps({
        'model': 'openai',
        'messages': [{'role': 'system', 'content': SYSTEM},
                     {'role': 'user', 'content': user_text}],
        'temperature': 0.9,
        'max_tokens': 2500,
    }).encode('utf-8')
    body = _http(TEXT_URL, data=payload, timeout=180).decode('utf-8', 'replace')
    content = ''
    reasoning = ''
    try:
        msg = json.loads(body)['choices'][0]['message']
        content = (msg.get('content') or '') if isinstance(msg.get('content'), str) else ''
        reasoning = msg.get('reasoning') or ''
    except Exception:
        content = body
    prompt = ''
    m = re.search(r'\{.*\}', content, re.S)
    if m:
        try:
            prompt = (json.loads(m.group(0)).get('image_prompt') or '').strip()
        except Exception:
            prompt = ''
    if len(prompt.split()) < 20 and reasoning:
        quoted = re.findall(r'"([^"]{80,})"', reasoning)
        quoted += re.findall(r"'([^']{80,})'", reasoning)
        cands = [q for q in quoted
                 if 'no text' in q.lower() and len(q.split()) >= 35]
        if cands:
            prompt = max(cands, key=lambda q: len(q)).replace("'red'", 'red').strip()
    if len(prompt.split()) < 20:
        raise RuntimeError('no image_prompt in LLM reply: ' + (content or reasoning)[:200])
    return {'image_prompt': prompt}


def write_prompt(guid):
    concepts = load_concepts()
    c = concepts.get(guid)
    if not c:
        raise SystemExit('no concept for ' + guid)
    article = {k: c.get(k) for k in
               ('headline', 'demo', 'explain', 'consequence',
                'visual_object', 'demo_shift', 'object_type', 'cover_test')}
    article['cover_prompt_existing'] = c.get('cover_prompt', '')
    base = ('Article for the cover:\n' +
            json.dumps(article, ensure_ascii=False, indent=2) +
            '\n\nWrite the unique image_prompt for THIS article.')
    last = ''
    prompt = ''
    problems = []
    for i in range(3):
        user = base
        if last:
            user += ('\n\nYour previous attempt was rejected by the linter: ' + last +
                     '. Fix exactly that and keep 55-105 words.')
        try:
            out = llm_json(user)
            prompt = (out.get('image_prompt') or '').strip()
            problems = lint_prompt(prompt, concepts, guid)
            if not problems:
                break
            last = ', '.join(problems)
        except Exception as e:
            last = str(e)[:160]
        time.sleep(5)
    if not prompt:
        raise RuntimeError('prompt failed: ' + last)
    if problems:
        raise RuntimeError('lint failed after retries: ' + ', '.join(problems))
    c['image_prompt'] = prompt
    save_concepts(concepts)
    return prompt


def lint_prompt(prompt, concepts, guid):
    problems = []
    words = prompt.split()
    if not (40 <= len(words) <= 130):
        problems.append('words=%d' % len(words))
    low = prompt.lower()
    if 'no text' not in low:
        problems.append('missing_no_text')
    if 'black' not in low and 'dark' not in low and 'night' not in low:
        problems.append('missing_dark_field')
    if not re.search(r'\bred\b', low):
        problems.append('missing_red_accent')
    prev = []
    for g, c in concepts.items():
        if g == guid:
            continue
        p = (c.get('image_prompt') or '')
        if p:
            prev.append(set(re.findall(r'[a-z]{3,}', p.lower())))
    if prev:
        cur = set(re.findall(r'[a-z]{3,}', low))
        worst = max(len(cur & p) / max(1, len(cur | p)) for p in prev)
        if worst > 0.55:
            problems.append('not_unique jaccard=%.2f' % worst)
    return problems


def horde_submit(prompt, seed):
    payload = {
        'prompt': prompt + ', best quality, highly detailed',
        'params': {'width': 1216, 'height': 640, 'steps': 30,
                   'sampler_name': 'k_euler', 'cfg_scale': 6, 'seed': str(seed)},
        'nsfw': False, 'models': [HORDE_MODEL],
        'r2': True, 'shared': False,
    }
    body = _http(HORDE_BASE + '/generate/async',
                 data=json.dumps(payload).encode('utf-8'),
                 headers={'apikey': '0000000000', 'Client-Agent': HORDE_AGENT},
                 timeout=60)
    out = json.loads(body)
    if 'id' not in out:
        raise RuntimeError('horde submit: ' + str(out)[:200])
    return out['id']


def horde_wait(jid, timeout=540):
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(10)
        try:
            chk = json.loads(_http(HORDE_BASE + '/generate/check/' + jid, timeout=40))
        except Exception:
            continue
        if chk.get('faulted'):
            raise RuntimeError('horde job faulted')
        if not chk.get('done'):
            continue
        status = json.loads(_http(HORDE_BASE + '/generate/status/' + jid, timeout=60))
        gens = status.get('generations') or []
        if not gens:
            raise RuntimeError('horde done but no generation')
        imgref = gens[0].get('img') or ''
        if imgref.startswith('http'):
            return _http(imgref, timeout=120)
        return base64.b64decode(imgref)
    raise RuntimeError('horde timeout %ds' % timeout)


def _decode_cover(raw):
    img = Image.open(io.BytesIO(raw)).convert('RGB')
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    return img


def render_image(prompt, seed, attempts=3):
    last = 'no attempt'
    for i in range(attempts):
        try:
            jid = horde_submit(prompt, seed + i * 977)
            img = _decode_cover(horde_wait(jid))
            problems = audit(img)
            if problems is None:
                return img
            last = 'horde audit %s (attempt %d)' % (problems, i + 1)
        except Exception as e:
            last = 'horde: ' + str(e)[:160]
        print('  attempt %d %s' % (i + 1, last))
        time.sleep(10)
    print('  horde exhausted (%s), trying sana fallback' % last[:80])
    for i in range(attempts):
        params = {'width': W, 'height': H, 'model': 'sana', 'seed': seed + i * 977,
                  'nologo': 'true', 'referrer': 'sonic-infrastructure'}
        url = IMAGE_BASE + urllib.parse.quote(prompt) + '?' + urllib.parse.urlencode(params)
        try:
            body = _http(url, timeout=200)
        except Exception as e:
            last = 'sana http: ' + str(e)[:120]
            print('  sana attempt %d %s' % (i + 1, last))
            if '402' in str(e) or '503' in str(e):
                time.sleep(30)
            continue
        if body[:3] == b'\xff\xd8\xff' or body[:8] == b'\x89PNG\r\n\x1a\n':
            img = _decode_cover(body)
            problems = audit(img)
            if problems is None:
                return img
            last = 'sana audit %s (attempt %d)' % (problems, i + 1)
        else:
            last = 'sana not an image (attempt %d)' % (i + 1)
        print('  sana attempt %d %s' % (i + 1, last))
        time.sleep(10)
    raise RuntimeError('render failed: ' + last)


def audit(img):
    problems = []
    arr = np.asarray(img).astype(np.int16)
    lum = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2])
    if lum.mean() > 105:
        problems.append('too_bright mean=%.0f' % lum.mean())
    red = ((arr[..., 0] > 110) & (arr[..., 0] - arr[..., 1] > 45) &
           (arr[..., 0] - arr[..., 2] > 45))
    if red.sum() < 350:
        problems.append('no_red_accent px=%d' % int(red.sum()))
    white = ((arr[..., 0] > 215) & (arr[..., 1] > 215) & (arr[..., 2] > 215))
    if white.mean() > 0.12:
        problems.append('too_much_white')
    return ','.join(problems) if problems else None


def dhash(img, size=17):
    g = img.convert('L').resize((size + 1, size), Image.LANCZOS)
    a = np.asarray(g).astype(np.int16)
    bits = a[:, 1:] > a[:, :-1]
    return ''.join('1' if b else '0' for row in bits for b in row)


def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--guid')
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--prompt-only', action='store_true')
    ap.add_argument('--reprompt', action='store_true')
    args = ap.parse_args()

    if args.all:
        concepts = load_concepts()
        done = skipped = 0
        for guid in sorted(concepts):
            if (concepts[guid].get('image_prompt') or '').strip():
                skipped += 1
                continue
            try:
                p = write_prompt(guid)
                print('PROMPT OK  %-58s %s' % (guid[:58], p[:70] + '...'))
                done += 1
            except Exception as e:
                print('PROMPT FAIL %-58s %s' % (guid[:58], str(e)[:120]))
        print('written=%d skipped=%d' % (done, skipped))
        return 0

    if not args.guid:
        ap.error('--guid required')
    prompt = '' if args.reprompt else load_concepts()[args.guid].get('image_prompt') or ''
    if not prompt:
        prompt = write_prompt(args.guid)
    print('PROMPT:', prompt)
    if args.prompt_only:
        return 0
    seed = int(re.sub(r'\D', '', args.guid) or 0)
    img = render_image(prompt, seed)
    os.makedirs(CAND_DIR, exist_ok=True)
    name = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', args.guid)
    out = os.path.join(CAND_DIR, name + '.png')
    img.save(out, 'PNG')
    print('CANDIDATE:', out, 'mean_audit=OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
