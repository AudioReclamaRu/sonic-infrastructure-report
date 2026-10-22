# -*- coding: utf-8 -*-
"""Telegram publisher for long-form markdown articles (HTML formatting).

Reuses the canonical bot token / channel / proxy from publisher.py env.
Sends: 1 photo with a short HTML caption, then the rest as HTML text chunks.
Usage:
  python tools\tg_publish_html.py --md <file.md> --image <file.png> --slug <name>
  python tools\tg_publish_html.py --md <file.md> --image <file.png> --slug <name> --dry-run
"""
import argparse
import html
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import publisher as P  # noqa: E402

STATE = os.path.join(REPO, 'state', 'geo_posts.jsonl')


def esc(s):
    return html.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<i>\1</i>', s)
    s = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', s)
    return s


def table_block(rows):
    out = []
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        if i == 0:
            out.append('<b>' + ' · '.join(inline(c) for c in cells) + '</b>')
            continue
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
            continue
        if len(cells) >= 2:
            head = cells[0]
            rest = ' · '.join(cells[1:])
            out.append('• <b>' + inline(head) + '</b> — ' + inline(rest))
        else:
            out.append('• ' + inline(cells[0]))
    return '\n'.join(out)


def md_to_html(md):
    lines = md.replace('\r\n', '\n').split('\n')
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i])
                i += 1
            out.append(table_block(rows))
            out.append('')
            continue
        if re.fullmatch(r'-{3,}', ln.strip()):
            out.append('')
            i += 1
            continue
        if ln.startswith('### '):
            out.append('<b>' + inline(ln[4:]) + '</b>')
        elif ln.startswith('## '):
            out.append('')
            out.append('<b>' + inline(ln[3:]) + '</b>')
        elif ln.startswith('# '):
            out.append('<b>' + inline(ln[2:]) + '</b>')
        elif re.match(r'^\d+\.\s', ln):
            out.append(re.sub(r'^(\d+)\.\s', r'\1. ', inline(ln)))
        elif ln.startswith('- '):
            out.append('• ' + inline(ln[2:]))
        else:
            out.append(inline(ln))
        i += 1
    text = '\n'.join(out)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_chunks(text, limit=3900):
    if len(text) <= limit:
        return [text]
    chunks = []
    cur = ''
    for para in text.split('\n\n'):
        cand = (cur + '\n\n' + para).strip() if cur else para
        if len(cand) <= limit:
            cur = cand
            continue
        if cur:
            chunks.append(cur)
        while len(para) > limit:
            cut = para.rfind('\n', 0, limit)
            if cut < limit * 0.5:
                cut = para.rfind(' ', 0, limit)
            if cut < limit * 0.5:
                cut = limit
            chunks.append(para[:cut].strip())
            para = para[cut:].strip()
        cur = para
    if cur:
        chunks.append(cur)
    return chunks


def send_photo(chat, token, proxy, api, img, caption):
    fd, capf = tempfile.mkstemp(suffix='.html', prefix='tgcap_')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(caption)
    try:
        ok, out = P.invoke_curl([
            '--max-time', '90', '-s', '-x', proxy,
            '-F', 'chat_id=' + chat,
            '-F', 'caption=<' + capf + ';type=text/plain;charset=utf-8',
            '-F', 'parse_mode=HTML',
            '-F', 'photo=@' + img + ';type=image/png',
            api + '/bot' + token + '/sendPhoto'])
    finally:
        try:
            os.remove(capf)
        except OSError:
            pass
    return out


def send_text(chat, token, proxy, api, text):
    fd, f = tempfile.mkstemp(suffix='.html', prefix='tgmsg_')
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.write(text)
    try:
        ok, out = P.invoke_curl([
            '--max-time', '90', '-s', '-x', proxy,
            '-F', 'chat_id=' + chat,
            '-F', 'text=<' + f + ';type=text/plain;charset=utf-8',
            '-F', 'parse_mode=HTML',
            '-F', 'disable_web_page_preview=true',
            api + '/bot' + token + '/sendMessage'])
    finally:
        try:
            os.remove(f)
        except OSError:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md', required=True)
    ap.add_argument('--image', required=True)
    ap.add_argument('--slug', required=True)
    ap.add_argument('--intro-len', type=int, default=620)
    ap.add_argument('--single', action='store_true',
                    help='send ONE message: photo + whole body as caption (must fit 1024)')
    ap.add_argument('--delete', default='', help='comma-separated message ids to delete first')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    md = io.open(args.md, encoding='utf-8').read()
    body = md_to_html(md)

    if args.single:
        caption = body
        rest = ''
        if len(caption) > 1024:
            print('CAPTION TOO LONG: %d > 1024' % len(caption))
            return 1
    else:
        paras = body.split('\n\n')
        title = paras[0]
        intro = paras[1] if len(paras) > 1 else ''
        rest = '\n\n'.join(paras[2:]).strip()
        caption = title + '\n\n' + intro
        if len(caption) > 1024:
            caption = caption[:1000].rsplit('\n', 1)[0]

    chunks = [c for c in split_chunks(rest) if c]
    print('CAPTION len=%d' % len(caption))
    print(caption)
    print('--- chunks:', [len(c) for c in chunks])
    if args.dry_run:
        for i, c in enumerate(chunks):
            print('=== CHUNK %d ===' % i)
            print(c)
        return 0

    env = P.load_env()
    token = io.open(env['BOT_TOKEN_FILE'], encoding='utf-8').read().strip()
    proxy = env.get('PROXY', 'socks5h://127.0.0.1:10808')
    api = env.get('API', 'https://api.telegram.org')
    chat = P.tg_chat(env)

    for mid in [x.strip() for x in args.delete.split(',') if x.strip()]:
        ok, out = P.invoke_curl([
            '--max-time', '60', '-s', '-x', proxy,
            '-F', 'chat_id=' + chat,
            '-F', 'message_id=' + mid,
            api + '/bot' + token + '/deleteMessage'])
        print('DELETE', mid, (out or '')[:120])

    ids = []
    out = send_photo(chat, token, proxy, api, args.image, caption)
    try:
        r = json.loads(out)
        if not r.get('ok'):
            print('PHOTO FAIL', out[:400])
            return 1
        ids.append(r['result']['message_id'])
    except Exception:
        print('PHOTO FAIL', out[:400])
        return 1
    print('PHOTO OK msg', ids[0])

    for c in chunks:
        out = send_text(chat, token, proxy, api, c)
        try:
            r = json.loads(out)
            if not r.get('ok'):
                print('TEXT FAIL', out[:400])
                return 1
            ids.append(r['result']['message_id'])
            print('TEXT OK msg', r['result']['message_id'])
        except Exception:
            print('TEXT FAIL', out[:400])
            return 1

    rec = {'ts': datetime.now().isoformat(timespec='seconds'), 'slug': args.slug,
           'chat': chat, 'message_ids': ids, 'md': args.md, 'image': args.image}
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with io.open(STATE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print('DONE', json.dumps(rec, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
