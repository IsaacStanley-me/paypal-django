#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-translate empty msgstr entries in locale/*/LC_MESSAGES/django.po using an external translation API.

- Preserves existing translations and comments.
- Skips plural forms and entries with Python/Django placeholders to avoid breaking them.
- Provider selectable via env vars: TRANSLATE_PROVIDER in {libretranslate, deepl, google}
- Config via env vars:
  - LibreTranslate: TRANSLATE_API_URL (e.g. https://libretranslate.com), optional TRANSLATE_API_KEY
  - DeepL: TRANSLATE_API_KEY (required), optional TRANSLATE_API_URL (default https://api.deepl.com)
  - Google (Cloud Translate v2): TRANSLATE_API_KEY (required)

Usage:
  TRANSLATE_PROVIDER=libretranslate TRANSLATE_API_URL=https://libretranslate.com \
  python tools/auto_translate_po.py --source en --limit 100

Arguments:
  --source <code>   Source language code of msgid (default: en)
  --limit <N>       Max number of entries to translate per file (0=all; default: 0)
  --dry-run         Parse and report counts, no writes
  --langs <codes>   Comma-separated target language codes to process (default: all in locale/*)
"""

import os
import sys
import json
import glob
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, List

BASE_DIR = Path(__file__).resolve().parents[1]
LOCALE_DIR = BASE_DIR / 'locale'

PLACEHOLDER_MARKERS = ['%(', '%s', '%d', '{', '}', '{{', '}}']


def has_placeholders(text: str) -> bool:
    t = text or ''
    return any(m in t for m in PLACEHOLDER_MARKERS)


def translate_libretranslate(text: str, target: str, source: str) -> str:
    url = os.environ.get('TRANSLATE_API_URL', 'https://libretranslate.com')
    api_key = os.environ.get('TRANSLATE_API_KEY', '')
    endpoint = url.rstrip('/') + '/translate'
    data = {
        'q': text,
        'source': source,
        'target': target,
        'format': 'text',
    }
    if api_key:
        data['api_key'] = api_key
    body = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
        if isinstance(payload, dict) and 'translatedText' in payload:
            return payload['translatedText']
        raise RuntimeError(f'Unexpected LibreTranslate response: {payload}')


def translate_deepl(text: str, target: str, source: str) -> str:
    # DeepL uses target_lang like FR, ES; convert to upper
    api_key = os.environ.get('TRANSLATE_API_KEY')
    if not api_key:
        raise RuntimeError('DeepL selected but TRANSLATE_API_KEY not set')
    base = os.environ.get('TRANSLATE_API_URL', 'https://api.deepl.com')
    endpoint = base.rstrip('/') + '/v2/translate'
    data = urllib.parse.urlencode({
        'auth_key': api_key,
        'text': text,
        'source_lang': source.upper(),
        'target_lang': target.upper(),
        'preserve_formatting': '1',
    }).encode('utf-8')
    req = urllib.request.Request(endpoint, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
        tr = payload.get('translations', [{}])[0].get('text')
        if tr:
            return tr
        raise RuntimeError(f'Unexpected DeepL response: {payload}')


def translate_google(text: str, target: str, source: str) -> str:
    # Simple free API is not officially available; support a generic translate.googleapis.com route with key
    api_key = os.environ.get('TRANSLATE_API_KEY')
    if not api_key:
        raise RuntimeError('Google selected but TRANSLATE_API_KEY not set')
    qs = urllib.parse.urlencode({
        'q': text,
        'target': target,
        'source': source,
        'key': api_key,
        'format': 'text',
    })
    url = f'https://translation.googleapis.com/language/translate/v2?{qs}'
    with urllib.request.urlopen(url, timeout=20) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
        tr = payload.get('data', {}).get('translations', [{}])[0].get('translatedText')
        if tr:
            return tr
        raise RuntimeError(f'Unexpected Google response: {payload}')


def get_translator():
    provider = os.environ.get('TRANSLATE_PROVIDER', 'libretranslate').lower()
    if provider == 'libretranslate':
        return translate_libretranslate, 'libretranslate'
    if provider == 'deepl':
        return translate_deepl, 'deepl'
    if provider == 'google':
        return translate_google, 'google'
    raise RuntimeError(f'Unsupported TRANSLATE_PROVIDER: {provider}')


def parse_po_entries(lines: List[str]) -> List[Tuple[int, int]]:
    """
    Return list of (start_index, end_index) line indices that form a single entry (from first comment/msgid to following blank line).
    """
    entries = []
    start = 0
    in_entry = False
    for i, line in enumerate(lines):
        if not in_entry:
            if line.startswith('#') or line.startswith('msgid') or not line.strip():
                start = i
                in_entry = True
        if in_entry and line.strip() == '' and i > start:
            entries.append((start, i))
            in_entry = False
    if in_entry:
        entries.append((start, len(lines)))
    return entries


def extract_msgid_msgstr(block: List[str]) -> Tuple[Optional[int], Optional[int], str, str]:
    msgid_idx = None
    msgstr_idx = None
    msgid_val = ''
    msgstr_val = ''
    for idx, line in enumerate(block):
        if line.startswith('msgid '):
            msgid_idx = idx
            msgid_val = line.split(' ', 1)[1].strip()
        elif line.startswith('msgstr '):
            msgstr_idx = idx
            msgstr_val = line.split(' ', 1)[1].strip()
    return msgid_idx, msgstr_idx, msgid_val, msgstr_val


def is_simple_quoted_scalar(s: str) -> bool:
    # Accept only one-line strings like "\"Text\""
    return s.startswith('"') and s.endswith('"') and '\n' not in s


def unquote(s: str) -> str:
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.encode('utf-8').decode('unicode_escape')


def quote(s: str) -> str:
    s = s.replace('"', '\\"')
    return '"' + s + '"'


def process_po_file(po_path: Path, source_lang: str, limit: int, translator_func) -> Tuple[int, int, int]:
    content = po_path.read_text(encoding='utf-8')
    lines = content.splitlines(True)  # keepends
    entries = parse_po_entries(lines)

    changed = 0
    skipped = 0
    total_candidates = 0

    for (start, end) in entries:
        block = lines[start:end]
        # Ignore header block (msgid "")
        midx, sidx, mid, ms = extract_msgid_msgstr(block)
        if midx is None or sidx is None:
            continue
        if not is_simple_quoted_scalar(mid) or not is_simple_quoted_scalar(ms):
            # Skip multiline and plural forms for safety
            skipped += 1
            continue
        msgid_text = unquote(mid)
        msgstr_text = unquote(ms)
        if msgid_text == '' or msgstr_text != '':
            continue
        # Detect target language from folder name
        # .../locale/<lang>/LC_MESSAGES/django.po
        try:
            lang = po_path.parts[-3]
        except Exception:
            skipped += 1
            continue

        total_candidates += 1
        if has_placeholders(msgid_text):
            skipped += 1
            continue
        if limit and changed >= limit:
            continue
        try:
            translated = translator_func(msgid_text, target=lang, source=source_lang)
            # Update msgstr line while preserving indentation
            prefix = block[sidx].split('msgstr', 1)[0]
            block[sidx] = f"{prefix}msgstr {quote(translated)}\n"
            lines[start:end] = block
            changed += 1
        except Exception as e:
            print(f"WARN: {po_path} failed to translate '{msgid_text}': {e}")
            skipped += 1

    if changed:
        po_path.write_text(''.join(lines), encoding='utf-8')
    return changed, skipped, total_candidates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='en')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--langs', default='')
    args = ap.parse_args()

    translator, provider_name = get_translator()

    targets = []
    if args.langs:
        targets = [x.strip() for x in args.langs.split(',') if x.strip()]
    else:
        for p in (LOCALE_DIR.glob('*/LC_MESSAGES/django.po')):
            targets.append(p.parts[-3])
        targets = sorted(set(targets))

    print(f"Provider: {provider_name}")
    print(f"Locales to process: {targets}")

    po_files = []
    for lang in targets:
        p = LOCALE_DIR / lang / 'LC_MESSAGES' / 'django.po'
        if p.exists():
            po_files.append(p)

    total_changed = total_skipped = total_candidates = 0
    for po in po_files:
        print(f"Processing {po} ...")
        if args.dry_run:
            content = po.read_text(encoding='utf-8')
            lines = content.splitlines(True)
            entries = parse_po_entries(lines)
            candidates = 0
            for (start, end) in entries:
                block = lines[start:end]
                midx, sidx, mid, ms = extract_msgid_msgstr(block)
                if midx is None or sidx is None:
                    continue
                if not is_simple_quoted_scalar(mid) or not is_simple_quoted_scalar(ms):
                    continue
                if unquote(mid) and unquote(ms) == '':
                    candidates += 1
            print(f"  Candidates (simple entries): {candidates}")
            continue
        changed, skipped, candidates = process_po_file(po, args.source, args.limit, translator)
        print(f"  Changed: {changed}, Skipped: {skipped}, Candidates: {candidates}")
        total_changed += changed
        total_skipped += skipped
        total_candidates += candidates

    print(f"Done. Total changed: {total_changed}, skipped: {total_skipped}, candidates: {total_candidates}")
    if total_changed == 0:
        print("Note: No entries updated. Ensure there are empty msgstr and provider/env are set.")


if __name__ == '__main__':
    main()
