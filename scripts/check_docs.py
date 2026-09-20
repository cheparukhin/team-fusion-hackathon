#!/usr/bin/env python3
"""Check versioned Markdown links, app entry assets and evidence-restore references.

Uses the Git index, so ignored/restored files cannot hide broken clean-clone links.
External URLs and historical paths inside frozen JSON receipts are not fetched.
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def tracked_files(root):
    return set(filter(None, subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')))


def headings(path):
    anchors, counts = set(), {}
    for line in path.read_text().splitlines():
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if not match:
            continue
        title = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', match[1])
        slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(f'{slug}-{count}' if count else slug)
    return anchors


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'} and value:
                self.urls.append(value)


def check(root=ROOT):
    tracked = tracked_files(root)
    errors, external, checked = [], set(), 0
    metadata = root / 'preservation/controller-20260920'
    data = json.loads((metadata / 'data-files.json').read_text())
    aliases = json.loads((metadata / 'aliases.json').read_text())
    assets = {row['path']: row for row in data + aliases}

    def link(source, target):
        nonlocal checked
        url = urlsplit(target.strip('<>').split(' "')[0])
        if url.scheme or url.netloc:
            external.add(target)
            return
        if not url.path and not url.fragment:
            return
        destination = (source.parent / unquote(url.path)).resolve() if url.path else source.resolve()
        if not destination.is_relative_to(root.resolve()):
            errors.append({'file': str(source.relative_to(root)), 'target': target, 'error': 'outside repository'})
            return
        name = destination.relative_to(root.resolve()).as_posix()
        exists = name in tracked or any(p.startswith(name.rstrip('/') + '/') for p in tracked)
        if not exists:
            reason = 'release-only artifact: link to restore instructions and show its path as code' if name in assets else 'not versioned or missing'
            errors.append({'file': str(source.relative_to(root)), 'target': target, 'error': reason})
        elif url.fragment and destination.suffix == '.md' and unquote(url.fragment) not in headings(destination):
            errors.append({'file': str(source.relative_to(root)), 'target': target, 'error': 'missing Markdown heading'})
        checked += 1

    markdown = sorted(name for name in tracked if name.endswith('.md'))
    for name in markdown:
        path = root / name
        if not path.is_file():
            errors.append({'file': name, 'error': 'tracked Markdown missing from working tree'})
            continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            link(path, target)
    for name in ['dashboard/index.html', 'demo/index.html', 'demo/review/index.html']:
        parser = Assets()
        parser.feed((root / name).read_text())
        for target in parser.urls:
            link(root / name, target)

    cached_hashes = {}
    def sha(name):
        if name not in cached_hashes:
            cached_hashes[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
        return cached_hashes[name]

    for row in aliases:
        source = row['source']
        if source not in tracked and source not in assets:
            errors.append({'file': 'aliases.json', 'target': source, 'error': 'restore source missing'})
        elif source in tracked and sha(source) != row['sha256']:
            errors.append({'file': 'aliases.json', 'target': source, 'error': 'versioned restore source changed'})
    for row in data:
        if row['path'] in tracked and sha(row['path']) != row['sha256']:
            errors.append({'file': 'data-files.json', 'target': row['path'], 'error': 'versioned evidence conflicts with restore archive'})
    return {'status': 'failed' if errors else 'passed', 'markdown_files': len(markdown),
            'local_links_and_assets_checked': checked, 'external_urls_not_fetched': len(external),
            'restore_aliases_checked': len(aliases), 'errors': errors}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, indent=2))
    sys.exit(result['status'] != 'passed')
