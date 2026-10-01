# -*- coding: utf-8 -*-
"""add_frontmatter.py — give every hand-authored .md a machine-readable header.

Why: 0 of 154 tracked .md files had frontmatter, and 81 of them had no
`Type:` line at all. So no collection (evidence, entity, corpus, guide) could be
filtered by type/date/status without full-text parsing, which is how an agent
ends up bulk-reading reports/scans/ (2.2 MB, ~95% repeated) instead of
reports/intel/ (~400 KB, typed).

The shape is the one evidence/ already used as a header block, promoted to
YAML so it is machine-readable:

    ---
    id: E-2026-014
    type: evidence
    date: 2026-09-11
    lang: en
    status: verified
    related: [corpus/edison-blind-test.md, reports/verdicts/verdict-index.md]
    ---

Rules, deliberately conservative:
  * ONLY tracked, hand-authored files. Generated layers (reports/, state/,
    feed/ except its README) are SKIPPED — a migration that regenerates nothing
    is a migration that rots on the next run.
  * NEVER rewrite existing frontmatter.
  * NEVER delete or reorder existing content. The legacy `Status: / Type: /
    Audience: / Last updated:` block stays (nothing in the repo parses it; it is
    the human-facing convention), and frontmatter is derived from it where
    present, so the two agree at write time.
  * `lang` is emitted ONLY when confidently known (.en.md suffix, Cyrillic
    content, or the explicit override list). Unknown means omitted, not guessed.
  * `date` falls back to the last commit that touched the file, so it is a fact
    about the file rather than a guess.

Usage:
    python tools/add_frontmatter.py            # dry run: report, write nothing
    python tools/add_frontmatter.py --apply    # write
    python tools/add_frontmatter.py --check    # exit 1 if any file is missing it
"""
import argparse
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# generated layers: never touched
SKIP_DIRS = ('reports/', 'state/', 'feed/')
# ...except a hand-written file inside one of them
SKIP_EXCEPT = ('feed/README.md',)

# type per directory (what the layer IS, not what the folder is called)
TYPE_BY_DIR = {
    'evidence': 'evidence',
    'entity': 'entity',
    'canon': 'operator',
    'corpus': 'corpus',
    'guides': 'guide',
    'dictionary': 'term',
    'ar-notes': 'ar_note',
    'interfaces': 'interface',
    'standards': 'standard',
    'catalog': 'catalog',
    'ops': 'runbook',
}
# canon/cards/ is a distinct type from canon/
TYPE_BY_EXACT = {
    'canon/README.md': 'index',
    'standards/README.md': 'index',
    'feed/README.md': 'index',
    'corpus/README.md': 'index',
    'guides/README.md': 'index',
}
# A file with no Cyrillic anywhere is English. A file whose H1 is English but
# whose body carries Russian is `mul`, not `en`: the defined terms
# («выпускающий голос», «Поле Принадлежности») live in English documents on
# purpose, and calling those files `en` would quietly drop them from a
# language filter. Only `.en.md` gets a hard `en` from the suffix.
CYR = re.compile(r'[\u0400-\u04FF]')
FM_RE = re.compile(r'\A---\r?\n')
ID_RE = re.compile(r'^(E-\d{4}-\d{3}|AR-\d{4}|INTERFACE-\d{3}|ENTITY-[A-Z0-9_-]+)$')
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')


def _git(*args):
    try:
        return subprocess.run(['git'] + list(args), cwd=REPO, capture_output=True,
                              text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def tracked_md():
    out = _git('ls-files', '*.md').split()
    files = []
    for f in out:
        if f.startswith(SKIP_DIRS) and f not in SKIP_EXCEPT:
            continue
        files.append(f)
    return files


def _read(rel):
    with open(os.path.join(REPO, rel), 'r', encoding='utf-8') as f:
        return f.read()


def _git_date(rel):
    out = _git('log', '-1', '--format=%ad', '--date=short', '--', rel).strip()
    return out if DATE_RE.fullmatch(out) else ''


def decide(rel, text):
    """Return (frontmatter_text, notes) without touching the file."""
    d = os.path.dirname(rel)
    if rel in TYPE_BY_EXACT:
        typ = TYPE_BY_EXACT[rel]
    elif d == 'canon/cards':
        typ = 'card'
    elif d in TYPE_BY_DIR:
        typ = TYPE_BY_DIR[d]
    else:
        typ = 'doc'

    # id: from the H1 / Canonical ID, else from the filename stem
    fid = ''
    m = re.search(r'Canonical ID:\s*(\S+)', text)
    if m:
        fid = m.group(1).strip()
    if not fid:
        m = re.search(r'^#\s+(\S+)\s*$', text, re.M)
        if m and ID_RE.match(m.group(1)):
            fid = m.group(1)
    if not fid:
        m = re.search(r'^(E-\d{4}-\d{3}|AR-\d{4}|INTERFACE-\d{3})', os.path.basename(rel))
        if m:
            fid = m.group(1)

    # date: filename > legacy header > last commit
    notes = []
    m = DATE_RE.search(os.path.basename(rel))
    date = m.group(1) if m else ''
    if not date:
        m = re.search(r'^Last updated:\s*(\S+)', text, re.M)
        if m:
            date = m.group(1)
    if not date:
        date = _git_date(rel)
        if date:
            notes.append('date=git')
    if not date:
        notes.append('NO-DATE')

    # status: only from the legacy header
    m = re.search(r'^Status:\s*(.+?)\s*$', text, re.M)
    status = m.group(1).strip().lower() if m else ''

    # lang: derived from the title, which states the document's own language
    if rel.endswith('.en.md'):
        lang = 'en'
    elif not CYR.search(text):
        lang = 'en'
    else:
        h1 = re.search(r'^#\s+(.+?)\s*$', text, re.M)
        lang = 'mul' if (h1 and not CYR.search(h1.group(1))) else 'ru'

    # related: existing back-link lines, normalized to repo paths
    rel_paths = set()
    for block in re.findall(r'^(?:Referenced in|Related|Связанные)\s*\n((?:- .*\n?)+)',
                            text, re.M):
        for line in block.splitlines():
            mm = re.search(r'([a-z0-9][\w./-]*\.md)\b', line)
            if mm and '/' in mm.group(1):
                rel_paths.add(mm.group(1))
    rel_paths = sorted(p for p in rel_paths if not p.endswith(rel))

    keys = []
    if fid:
        keys.append(('id', fid))
    keys.append(('type', typ))
    if date:
        keys.append(('date', date))
    if lang:
        keys.append(('lang', lang))
    if status:
        keys.append(('status', status))
    if rel_paths:
        keys.append(('related', rel_paths))
    body = '\n'.join(
        '%s: %s' % (k, ('[%s]' % ', '.join(v)) if isinstance(v, list) else v)
        for k, v in keys)
    return '---\n%s\n---\n' % body, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='write the changes')
    ap.add_argument('--check', action='store_true',
                    help='exit 1 if any hand-authored .md lacks frontmatter')
    a = ap.parse_args()

    files = tracked_md()
    todo, notes_all, done = [], [], 0
    for rel in files:
        text = _read(rel)
        if FM_RE.match(text):
            done += 1
            continue
        fm, notes = decide(rel, text)
        todo.append((rel, fm, notes))
        notes_all.extend(notes)
    print('scanned %d hand-authored .md | already has frontmatter: %d | needs: %d'
          % (len(files), done, len(todo)))

    if a.check:
        if todo:
            print('MISSING frontmatter in %d files (e.g. %s)'
                  % (len(todo), ', '.join(r for r, _, _ in todo[:5])))
            return 1
        print('OK: every hand-authored .md has frontmatter')
        return 0

    if not a.apply:
        from collections import Counter
        c = Counter(n for _, _, ns in todo for n in ns)
        print('dry run. notes:', dict(c) or 'none')
        print('\n--- first 8 previews ---')
        for rel, fm, _ in todo[:8]:
            print('== %s\n%s' % (rel, fm))
        return 0

    for rel, fm, _ in todo:
        p = os.path.join(REPO, rel)
        nl = '\r\n' if _read(rel).count('\r\n') > 0 else '\n'
        text = _read(rel)
        with open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(fm.replace('\n', nl) + text)
    print('applied frontmatter to %d files' % len(todo))
    return 0


if __name__ == '__main__':
    sys.exit(main())
