"""Reconcile the sourcing guide experience after legacy generators run."""

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'guide-experience'
BASE = 'https://flashcargoglobal.com'
BUYER_REQUEST = '/contact/#buyer-request'
HOME_TITLE = 'Cargo Global | Sourcing & Delivery to the US, Canada and Mexico'
BUYER_DESCRIPTION = 'Align purchase order details, supplier documents and delivery requirements before starting a sourcing request.'
REQUEST_FAQ_ROUTES = {'/freight-research/factory-ready-date-vs-cargo-ready-date/', '/freight-research/italy-clothing-manufacturer-export-to-australia/', '/freight-research/manufacturer-commercial-invoice-before-freight-quote/', '/freight-research/buyer-purchase-order-to-freight-plan/'}
GUIDE_FAMILIES = {'guides', 'freight-research', 'planning', 'resources'}


def content_fingerprint(soup):
    main = BeautifulSoup(str(soup.main), 'html.parser')
    for node in main.select('script,style,time,[data-ocean-rates],.source-checked'):
        node.decompose()
    return hashlib.sha256(main.get_text(' ',strip=True).encode('utf-8')).hexdigest()


def official_source(url):
    host=urlsplit(url).hostname or ''
    suffixes=('.gov','.gc.ca','.gov.au','.gov.in','.gov.br','.gob.mx','.europa.eu','.go.jp','.gov.cn','.gov.vn','.gov.tr','.gouv.fr','.gob.ar','.gob.cl','.gov.co')
    providers=('drewry.co.uk','freightos.com','sse.net.cn','canada.ca','europa.eu','iccwbo.org','wcoomd.org','iata.org','imo.org')
    return urlsplit(url).scheme=='https' and (host.endswith(suffixes) or any(host==domain or host.endswith('.'+domain) for domain in providers))


def check_new_page_review(current, soup, review):
    if review.get('review_status')!='verified' or review.get('content_sha256')!=content_fingerprint(soup) or not review.get('facts'):
        raise ValueError(f'Publication blocked: official evidence review missing for {current}')
    for fact in review['facts']:
        if not fact.get('claim') or not fact.get('verified') or not official_source(fact.get('source_url','')) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',fact.get('checked_on','')):
            raise ValueError(f'Publication blocked: incomplete fact evidence for {current}')


def enforce_publication_gate():
    baseline=json.loads((ROOT/'content/audience-baseline.json').read_text(encoding='utf-8'))
    existing={row['path'] for row in baseline}|{'/suppliers/','/delivery/','/landed-cost-calculator/'}
    evidence_path=ROOT/'content/publication-evidence.json'
    reviews=json.loads(evidence_path.read_text(encoding='utf-8'))['reviewed_pages'] if evidence_path.exists() else {}
    for path in documents():
        current=route(path)
        if current not in existing:
            check_new_page_review(current,load_page(path),reviews.get(current,{}))


def documents():
    return sorted(path for path in ROOT.rglob('*.html') if path.relative_to(ROOT).parts[0] not in {'output', 'content'})


def route(path):
    relative = path.relative_to(ROOT).as_posix()
    return '/' + (relative[:-10] if relative.endswith('index.html') else relative)


def load_page(path):
    return BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')


def inventory():
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for path in documents():
        soup = load_page(path)
        family = path.relative_to(ROOT).parts[0]
        if family not in GUIDE_FAMILIES:
            continue
        rows.append({
            'path': route(path), 'file': path.relative_to(ROOT).as_posix(),
            'language': soup.html.get('lang', 'en'),
            'title': soup.title.get_text(' ', strip=True),
            'h1': soup.h1.get_text(' ', strip=True),
            'article': bool(soup.select_one('article.guide-article')),
            'old_ctas': sum('freight inquiry' in a.get_text(' ', strip=True).lower() for a in soup.select('a')),
            'raw_source_lines': len(soup.find_all(string=re.compile(r'source_url\s*:', re.I))),
            'source_url': BASE + route(path), 'last_checked': now,
        })
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'guide-inventory.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def jsonld_nodes(soup):
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        nodes = data.get('@graph', [data]) if isinstance(data, dict) else data
        if isinstance(nodes, list):
            yield script, data, nodes


def source_date(soup):
    for element in soup.select('.updated, .last-checked, time[datetime]'):
        match = re.search(r'\d{4}-\d{2}-\d{2}', element.get('datetime', '') + element.get_text(' ', strip=True))
        if match:
            return match.group()
    return None


def clean_sources(soup):
    reviewed = source_date(soup)
    language = soup.html.get('lang','en').split('-')[0]
    labels = {'en':'Link last checked: ','es':'Enlace consultado: ','fr':'Lien vérifié le : ','zh':'链接最近检查日期：','hi':'लिंक की अंतिम जाँच: '}
    checked_label = labels.get(language, labels['en'])
    for note in soup.select('.source-checked'):
        if note.contents and isinstance(note.contents[0],str):
            note.contents[0].replace_with(' ' + checked_label)
    records = OUT / 'source-link-checks.csv'
    checked = {}
    if records.exists():
        with records.open(encoding='utf-8-sig', newline='') as handle:
            checked = {row['source_url']: row for row in csv.DictReader(handle)}
    removed = 0
    for text in list(soup.find_all(string=re.compile(r'source_url\s*:', re.I))):
        parent = text.parent
        if parent.name in {'script', 'style'}:
            continue
        if parent.name in {'span', 'p'} and parent.get_text(' ', strip=True).lower().startswith('source_url:') and not parent.find('a'):
            previous = parent.previous_sibling
            if getattr(previous, 'name', None) == 'br':
                previous.decompose()
            parent.decompose()
            removed += 1
    for anchor in soup.select('main li a[href^="https://"], main li a[href^="http://"]'):
        if 'flashcargoglobal.com' in anchor['href']:
            continue
        item = anchor.find_parent('li')
        if not item or item.find('time'):
            continue
        last_checked = checked.get(anchor['href'], {}).get('last_checked', reviewed)
        if not last_checked:
            continue
        last_checked = last_checked[:10]
        note = soup.new_tag('small', attrs={'class': 'source-checked'})
        note.append(' ' + checked_label)
        stamp = soup.new_tag('time', datetime=last_checked)
        stamp.string = last_checked
        note.append(stamp)
        item.append(note)
    return removed


def update_schemas(soup, current):
    targeted = {'/sourcing/', '/suppliers/', '/delivery/', '/contact/', '/landed-cost-calculator/'}
    if current not in targeted:
        return
    graph = next(jsonld_nodes(soup), None)
    if not graph:
        raise ValueError(f'Missing base schema: {current}')
    script, data, nodes = graph
    nodes[:] = [node for node in nodes if node.get('@type') not in {'FAQPage', 'Service', 'WebApplication'}]
    if current == '/contact/':
        for node in nodes:
            if node.get('@type') == 'WebPage':
                node['@type'] = 'ContactPage'
        data['@graph'] = nodes
        script.string = json.dumps(data, ensure_ascii=False)
        return
    questions = []
    for detail in soup.select('.faq-list details'):
        summary = detail.find('summary')
        answer = ' '.join(p.get_text(' ', strip=True) for p in detail.find_all('p'))
        if summary and answer:
            questions.append({'@type': 'Question', 'name': summary.get_text(' ', strip=True), 'acceptedAnswer': {'@type': 'Answer', 'text': answer}})
    if not questions:
        raise ValueError(f'No visible FAQs: {current}')
    nodes.append({'@type': 'FAQPage', '@id': BASE + current + '#faq', 'mainEntity': questions})
    if current == '/landed-cost-calculator/':
        nodes.append({'@type': 'WebApplication', '@id': BASE + current + '#worksheet', 'name': 'Cargo Global landed-cost worksheet', 'url': BASE + current, 'applicationCategory': 'BusinessApplication', 'operatingSystem': 'Any', 'isAccessibleForFree': True, 'description': soup.select_one('meta[name="description"]')['content'], 'provider': {'@id': BASE + '/#organization'}})
    else:
        names = {'/sourcing/': 'Curated product sourcing', '/suppliers/': 'Supplier capability review', '/delivery/': 'Door-to-door delivery coordination'}
        nodes.append({'@type': 'Service', '@id': BASE + current + '#service', 'name': names[current], 'serviceType': names[current], 'url': BASE + current, 'description': soup.select_one('meta[name="description"]')['content'], 'provider': {'@id': BASE + '/#organization'}})
    data['@graph'] = nodes
    script.string = json.dumps(data, ensure_ascii=False)


def apply_experience():
    from ocean_rates import load as load_rates, render_table
    rate_data = load_rates()
    OUT.mkdir(parents=True, exist_ok=True)
    changes = []
    for path in documents():
        soup = load_page(path)
        current = route(path)
        ctas = 0
        for anchor in soup.select('main a'):
            text = anchor.get_text(' ', strip=True)
            if re.fullmatch(r'Start a (?:freight inquiry|sourcing request)(?:\s*[↗→])?', text, re.I):
                anchor.clear()
                anchor.string = 'Start a sourcing request'
                anchor['href'] = BUYER_REQUEST
                ctas += 1
        for text in list(soup.find_all(string=True)):
            if text.parent.name in {'script', 'style'}:
                continue
            replacement = re.sub(r'Freight Research(?: Library)?', 'Sourcing guides', str(text))
            if current in REQUEST_FAQ_ROUTES:
                replacement = re.sub(r'before submitting an online (?:freight inquiry|sourcing request)', 'before starting a sourcing request', replacement, flags=re.I)
            if current == '/freight-research/buyer-purchase-order-to-freight-plan/':
                replacement = re.sub(r'freight inquiry', 'sourcing request', replacement, flags=re.I)
            if replacement != str(text):
                text.replace_with(replacement)
        for script, data, nodes in jsonld_nodes(soup):
            for node in nodes:
                if node.get('@type') == 'BreadcrumbList':
                    for part in node.get('itemListElement', []):
                        if 'freight research' in part.get('name', '').lower():
                            part['name'] = 'Sourcing guides'
                if current in REQUEST_FAQ_ROUTES:
                    for question in node.get('mainEntity', []) if node.get('@type') == 'FAQPage' else []:
                        answer = re.sub(r'before submitting an online (?:freight inquiry|sourcing request)', 'before starting a sourcing request', question['acceptedAnswer']['text'], flags=re.I)
                        question['acceptedAnswer']['text'] = re.sub(r'freight inquiry', 'sourcing request', answer, flags=re.I)
            script.string = json.dumps(data, ensure_ascii=False)
        if current in {'/freight-research/', '/freight-research/buyer-purchase-order-to-freight-plan/'}:
            for meta in soup.select('meta[name="description"], meta[property="og:description"], meta[name="twitter:description"]'):
                meta['content'] = re.sub(r'freight inquiry', 'sourcing request', meta['content'], flags=re.I)
                if current == '/freight-research/buyer-purchase-order-to-freight-plan/':
                    meta['content'] = BUYER_DESCRIPTION
        removed = clean_sources(soup)
        if current == '/':
            soup.title.string = HOME_TITLE
            for meta in soup.select('meta[property="og:title"], meta[name="twitter:title"]'):
                meta['content'] = HOME_TITLE
            for script, data, nodes in jsonld_nodes(soup):
                for node in nodes:
                    if node.get('@type') == 'WebPage':
                        node['name'] = HOME_TITLE
                script.string = json.dumps(data, ensure_ascii=False)
        if current == '/delivery/':
            soup.h1.string = 'Delivered to Your Door.'
        update_schemas(soup, current)
        for previous in soup.select('[data-ocean-rates]'):
            previous.decompose()
        robots = soup.select_one('meta[name="robots"]')
        noindex = robots and 'noindex' in robots.get('content', '').lower()
        if current in rate_data['page_lanes'] and not noindex:
            table = BeautifulSoup(render_table(rate_data, rate_data['page_lanes'][current], soup.html.get('lang', 'en')), 'html.parser').select_one('[data-ocean-rates]')
            container = soup.select_one('article.guide-article, .audience-article .editorial') or soup.main
            if container is soup.main:
                table['class'].append('section')
            faq = container.select_one('.faq-list')
            if faq:
                target = faq.find_parent('section') or faq
                target.insert_before(table)
            else:
                container.append(table)
        path.write_text(str(soup), encoding='utf-8', newline='\n')
        changes.append({'path': current, 'ctas_changed': ctas, 'raw_source_lines_removed': removed, 'source_url': BASE + current, 'last_checked': datetime.now(timezone.utc).isoformat()})
    with (OUT / 'guide-changes.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(changes[0]))
        writer.writeheader()
        writer.writerows(changes)
    return changes


if __name__ == '__main__':
    rows = inventory()
    print(json.dumps({'guide_documents': len(rows), 'articles': sum(row['article'] for row in rows), 'old_ctas': sum(row['old_ctas'] for row in rows), 'pages_with_raw_sources': sum(bool(row['raw_source_lines']) for row in rows)}, ensure_ascii=False))
