# -*- coding: utf-8 -*-
"""make_reports_index.py — generate reports/INDEX.json (machine index for agents).

Why: reports/ held ~35% of the repo and was reachable only through Russian
prose. An agent globbing it hit reports/scans/ (2.4 MB, ~95% repeated) first
and burned its context on zero marginal information.

This builds an explicit index instead: one row per file with kind, date, size,
and the cross-layer links that are cheap to compute (guids found in the text,
evidence IDs, the intel schema actually present). It is regenerated, never
hand-edited, so it cannot drift the way a prose list did.

Usage:
    python tools/make_reports_index.py            # write reports/INDEX.json
    python tools/make_reports_index.py --check    # exit 1 if index is stale

Read-only with respect to every other file.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(REPO, 'reports')
OUT = os.path.join(REPORTS, 'INDEX.json')

# kind per subdirectory, from the layer's actual role (not the folder name)
KIND = {
    'intel': 'signal_rows',
    'scans': 'scan_dump',
    'outreach': 'outreach_draft',
    'signals': 'signal_note',
    'verdicts': 'verdict_log',
    'monitoring': 'registry',
}
ROOT_KIND = 'run_status'

# Kinds the live loop rewrites in place. Their byte size, url count and guid list
# change without a commit, so indexing those numbers made the index stale the
# moment the scanner ran - a check that cries wolf is a check that gets ignored.
# For these the index records WHAT EXISTS, not its current measurements: the
# measurements belong to the runtime, and prose in reports/README.md carries them
# with a measurement date instead.
GENERATED = {'signal_rows', 'scan_dump', 'outreach_draft', 'run_status'}

GUID_RE = re.compile(r'\b([a-z0-9]+(?:-[a-z0-9]+){2,}-\d{4}-\d{2}-\d{2})\b')
EVID_RE = re.compile(r'\bE-\d{4}-\d{3}\b')
URL_RE = re.compile(r'https?://[^\s)\]<>"]+')
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')


def _read(path, limit=None):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read() if limit is None else f.read(limit)
    except OSError:
        return ''


def _intel_rows(path):
    """(row count, union of row keys).

    The union matters: contact_email/contact_page/contact_ready appear on the
    outreach-eligible rows only, never on the first row of a file, so a schema
    read off row[0] reports 15 fields where the series really has 18.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        rows = data.get('rows') or []
        keys = set()
        for r in rows:
            keys.update(r.keys())
        return len(rows), sorted(keys)
    except (OSError, ValueError, AttributeError):
        return None, []


def _tracked(rel):
    """Tracked files only: a clone must not see an index the clone cannot have."""
    try:
        out = subprocess.run(['git', 'ls-files', '--', rel], cwd=REPO,
                             capture_output=True, text=True, timeout=30)
        return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
    except (OSError, subprocess.SubprocessError):
        return []


def build():
    tracked = set(_tracked('reports'))
    rows = []
    warnings = []
    for rel in sorted(tracked):
        # The index does not list itself: adding a row for it would make the file
        # differ from its own output the instant it is committed.
        if rel.replace('\\', '/') == os.path.relpath(OUT, REPO).replace('\\', '/'):
            continue
        abs_path = os.path.join(REPO, rel)
        if not os.path.isfile(abs_path):
            warnings.append('tracked but missing on disk: %s' % rel)
            continue
        parts = rel.split('/')
        sub = parts[1] if len(parts) > 2 else ''
        ext = os.path.splitext(rel)[1].lower()
        kind = KIND.get(sub, ROOT_KIND)
        generated = kind in GENERATED
        text = _read(abs_path, 200000 if ext in ('.md', '.json') else 0)
        name = os.path.basename(rel)
        dates = DATE_RE.findall(name) or DATE_RE.findall(text[:2000])
        row = {
            'path': rel.replace('\\', '/'),
            'kind': kind,
            'date': max(dates) if dates else '',
        }
        if generated:
            row['generated'] = True
        else:
            row['bytes'] = os.path.getsize(abs_path)
            row['guids'] = sorted(set(GUID_RE.findall(text)))
            row['evidence'] = sorted(set(EVID_RE.findall(text)))
            urls = set(URL_RE.findall(text))
            if urls:
                row['url_count'] = len(urls)
        if ext == '.json' and sub == 'intel':
            # Row counts live in --measure, not here: the live loop rewrites
            # even a dated intel file in place, so a stored count goes stale
            # within minutes and teaches everyone to ignore --check.
            pass
        rows.append(row)

    idx = {
        'schema': 'reports-index/1',
        'repo': 'sonic-infrastructure-report',
        'generator': 'tools/make_reports_index.py',
        'tracked_files': len(rows),
        'kinds': sorted({r['kind'] for r in rows}),
        'how_to_read': {
            'signal_rows': 'machine-readable daily fact stream - SEARCH THIS',
            'signal_note': 'dated signal note (RU/EN editorial layer)',
            'verdict_log': 'verdict record (CONFIRMED / RESCHEDULED / SOURCE ERROR)',
            'registry': 'venue/source registry',
            'outreach_draft': 'outreach letters, RU operational layer',
            'scan_dump': 'raw scan dump, MOSTLY REPEATED - do not bulk-read; '
                         'use signal_rows instead',
            'run_status': 'daily run status, runtime artifact',
        },
        'files': rows,
    }
    if warnings:
        idx['warnings'] = warnings
    return idx


def measure(idx):
    """Volume table, printed on demand and never stored: it changes whenever the
    live loop writes, and a stored measurement would make the index stale for no
    navigational reason."""
    from collections import Counter
    agg = {}
    for r in idx['files']:
        a = agg.setdefault(r['kind'], [0, 0, 0])
        a[0] += 1
        a[1] += os.path.getsize(os.path.join(REPO, r['path']))
    print('%-16s %6s %12s' % ('kind', 'files', 'bytes'))
    for k, v in sorted(agg.items()):
        print('%-16s %6d %12d' % (k, v[0], v[1]))

    # The intel schema is measured over EVERY file on disk, not the tracked
    # subset: the live loop adds fields over time, and a schema report that
    # silently shrinks to the last committed day is worse than none.
    files = sorted(glob.glob(os.path.join(REPORTS, 'intel', '*.json')))
    schema, rows = set(), 0
    for p in files:
        n, keys = _intel_rows(p)
        rows += n or 0
        schema.update(keys)
    print('\nintel on disk: %d files, %d rows' % (len(files), rows))
    if schema:
        print('intel row fields (%d): %s' % (len(schema), ', '.join(sorted(schema))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='exit 1 if INDEX.json differs from the build')
    ap.add_argument('--measure', action='store_true',
                    help='print the per-kind volume table and exit')
    a = ap.parse_args()
    idx = build()
    if a.measure:
        measure(idx)
        return 0
    payload = json.dumps(idx, ensure_ascii=False, indent=2) + '\n'
    if a.check:
        try:
            with open(OUT, 'r', encoding='utf-8') as f:
                cur = f.read()
        except OSError:
            print('STALE: reports/INDEX.json missing')
            return 1
        print('OK: index is current' if cur == payload else 'STALE: rerun generator')
        return 0 if cur == payload else 1
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(payload)
    print('wrote %s (%d tracked files, %d bytes)'
          % (os.path.relpath(OUT, REPO), idx['tracked_files'], len(payload)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

