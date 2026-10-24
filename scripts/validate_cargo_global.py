"""Validate static routing, metadata, branding and source-link replacements."""

import csv
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'cargo-global-reposition'
BASE = 'https://flashcargoglobal.com'
NOW = datetime.now(timezone.utc).isoformat()


def main():
    checks = []
    errors = []
    pages = [p for p in ROOT.rglob('*.html') if p.relative_to(ROOT).parts[0] not in ('output', 'content')]
    indexed = set()
    titles_fixed = []
    before = zipfile.ZipFile(OUT / 'before-reposition.zip')
    before_files = set(before.namelist())
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        route = '/' + rel[:-10] if rel.endswith('index.html') else '/' + rel
        soup = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
        failures = []
        title = soup.title.get_text(' ', strip=True) if soup.title else ''
        h1s = soup.find_all('h1')
        canonical = soup.find('link', rel='canonical')
        robots = soup.find('meta', attrs={'name': 'robots'})
        is_indexed = robots and 'noindex' not in robots.get('content', '')
        if is_indexed:
            indexed.add(BASE + route)
        if not title.startswith('Cargo Global | '):
            failures.append('title_prefix')
        if len(h1s) != 1:
            failures.append('h1_count')
        if h1s and h1s[0].get_text().endswith(('...', '…')):
            failures.append('cutoff_heading')
        if not canonical or not canonical.get('href', '').startswith(BASE + '/'):
            failures.append('canonical')
        if not soup.select_one('.wordmark-flash') or not soup.select_one('.wordmark-main'):
            failures.append('wordmark')
        nav_labels = [a.get_text(' ', strip=True).replace('↗', '').strip() for a in soup.select('#primary-menu a')]
        if nav_labels != ['Source Products', 'Guides', 'For Suppliers', 'Delivery', 'Contact']:
            failures.append('navigation')
        visible = BeautifulSoup(str(soup), 'html.parser')
        for el in visible.select('script, style, .wordmark-flash, .legal'):
            el.decompose()
        text = visible.get_text(' ', strip=True)
        if re.search(r'\bFlash\b', text, re.I):
            failures.append('legacy_brand_visible')
        if re.search(r'\bAI\b', text):
            failures.append('prohibited_word')
        if re.search(r'flashcargonetwork\.com|unrelated Flash companies', str(soup), re.I):
            failures.append('network_reference')
        if any(soup.select_one(f'script[src*="{value}"]') for value in ('googletag', 'analytics', 'clarity', 'facebook')):
            failures.append('shared_tracking')
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                json.loads(script.string or script.get_text())
            except json.JSONDecodeError:
                failures.append('invalid_schema')
        for anchor in soup.select('a[href]'):
            href = anchor['href']
            parsed = urlsplit(urljoin(BASE + route, href))
            if parsed.netloc != 'flashcargoglobal.com':
                continue
            target = ROOT / unquote(parsed.path).lstrip('/')
            if target.is_dir():
                target = target / 'index.html'
            if not target.exists():
                failures.append('broken_link:' + href)
            elif parsed.fragment:
                dest = BeautifulSoup(target.read_text(encoding='utf-8-sig'), 'html.parser')
                if not dest.find(id=unquote(parsed.fragment)):
                    failures.append('missing_anchor:' + href)
        if rel in before_files:
            old = BeautifulSoup(before.read(rel).decode('utf-8-sig'), 'html.parser')
            old_title = old.title.get_text(' ', strip=True) if old.title else ''
            old_h1 = old.h1.get_text(' ', strip=True) if old.h1 else ''
            if old_title and old_h1.startswith(old_title) and len(old_title) < len(old_h1):
                titles_fixed.append({'path': route, 'old_title': old_title, 'new_title': title, 'source_url': BASE + route, 'last_checked': NOW})
        entry = {'check': 'page', 'path': route, 'status': 'fail' if failures else 'pass', 'detail': '; '.join(sorted(set(failures))), 'source_url': BASE + route, 'last_checked': NOW}
        checks.append(entry)
        if failures:
            errors.append(entry)
    sitemap = ET.parse(ROOT / 'sitemap.xml')
    if sitemap.getroot().tag.endswith('sitemapindex'):
        listed = set()
        for node in sitemap.findall('.//{*}loc'):
            section_path = ROOT / urlsplit(node.text).path.lstrip('/')
            listed.update(el.text for el in ET.parse(section_path).findall('.//{*}loc'))
    else:
        listed = {el.text for el in sitemap.findall('.//{*}loc')}
    diff = sorted(listed.symmetric_difference(indexed))
    entry = {'check': 'sitemap_indexed_pages', 'path': '/sitemap.xml', 'status': 'fail' if diff else 'pass', 'detail': '; '.join(diff), 'source_url': BASE + '/sitemap.xml', 'last_checked': NOW}
    checks.append(entry)
    if diff:
        errors.append(entry)
    for url in [
        'https://www.abf.gov.au/importing-exporting-and-manufacturing/importing/how-to-import/overview',
        'https://www.ftc.gov/news-events/topics/tools-consumers/apparel-labeling',
        'https://www.customs.go.jp/english/c-answer_e/customsanswer_e.htm',
    ]:
        try:
            response = requests.get(url, timeout=25)
            status = 'pass' if response.status_code == 200 else 'blocked' if response.status_code in (403, 429) else 'fail'
            detail = f'HTTP {response.status_code}; {response.url}'
        except requests.RequestException as exc:
            status, detail = 'blocked', str(exc)
        entry = {'check': 'replacement_source', 'path': '', 'status': status, 'detail': detail, 'source_url': url, 'last_checked': NOW}
        checks.append(entry)
        if status != 'pass':
            errors.append(entry)
    for name, records, fields in [
        ('validation.csv', checks, ['check', 'path', 'status', 'detail', 'source_url', 'last_checked']),
        ('errors.csv', errors, ['check', 'path', 'status', 'detail', 'source_url', 'last_checked']),
        ('repaired-titles.csv', titles_fixed, ['path', 'old_title', 'new_title', 'source_url', 'last_checked']),
    ]:
        with (OUT / name).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    print(json.dumps({'pages': len(pages), 'indexed': len(indexed), 'checks': len(checks), 'errors': len(errors), 'titles_restored': len(titles_fixed)}))
    for error in errors:
        print(json.dumps(error, ensure_ascii=False))


if __name__ == '__main__':
    main()
