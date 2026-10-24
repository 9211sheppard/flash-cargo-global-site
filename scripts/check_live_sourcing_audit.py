"""Check production against the approved sourcing cleanup, without submitting leads."""

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'cargo-global-reposition'
BASE = 'https://flashcargoglobal.com'
OLD = 'flash-cargo-global.old-sun-35f9.workers.dev'
NOW = datetime.now(timezone.utc).isoformat()


def main():
    session = requests.Session()
    rows = []
    def record(check, path, ok, detail):
        rows.append({'check': check, 'status': 'pass' if ok else 'fail', 'detail': detail, 'source_url': BASE + path, 'last_checked': NOW})

    pages = json.loads((OUT / 'release.json').read_text(encoding='utf-8'))
    for entry in pages:
        path = entry['path']
        if not path.endswith('.html') or path.startswith('content/'):
            continue
        route = '/' + (path[:-10] if path.endswith('index.html') else path)
        try:
            response = session.get(BASE + route, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            local = BeautifulSoup(entry['content'], 'html.parser')
            canonical = soup.select_one('link[rel="canonical"]')
            policy = soup.select_one('meta[http-equiv="Content-Security-Policy"]')
            ok = response.status_code == 200 and soup.title and soup.title.text == local.title.text
            ok = ok and soup.h1 and soup.h1.get_text() == local.h1.get_text()
            ok = ok and canonical and canonical['href'] == local.select_one('link[rel="canonical"]')['href']
            ok = ok and policy and OLD not in policy['content'] and 'static.wixstatic.com' not in policy['content']
            ok = ok and soup.select_one('meta[name="robots"]')['content'] == local.select_one('meta[name="robots"]')['content']
            record('page_release', route, bool(ok), f'HTTP {response.status_code}; title, H1, canonical, robots and policy compared with release')
            visible = BeautifulSoup(str(soup.main), 'html.parser')
            for script in visible.select('script,style'):
                script.decompose()
            record('guide_copy', route, 'Start a freight inquiry' not in visible.get_text() and 'source_url:' not in visible.get_text() and 'Freight Research' not in visible.get_text(), 'No obsolete guide CTA, research label or raw source lines in visible page text')
            local_rates = local.select_one('[data-ocean-rates]')
            if local_rates:
                actual_rates = soup.select_one('[data-ocean-rates]')
                record('ocean_rate_block', route, actual_rates is not None and actual_rates.get_text(' ',strip=True)==local_rates.get_text(' ',strip=True) and len(actual_rates.select('table'))==len(local_rates.select('table')), 'Compact request line or numeric table matches the validated rate file')
            if 'noindex' in local.select_one('meta[name="robots"]')['content']:
                record('noindex_without_rates',route,soup.select_one('[data-ocean-rates]') is None,'No rate block on a noindexed page')
            if route in {'/freight-research/factory-ready-date-vs-cargo-ready-date/','/freight-research/italy-clothing-manufacturer-export-to-australia/','/freight-research/manufacturer-commercial-invoice-before-freight-quote/'}:
                expected_answers=[p.get_text(' ',strip=True) for p in local.select('.faq-list details p')]
                actual_answers=[p.get_text(' ',strip=True) for p in soup.select('.faq-list details p')]
                encoded=[q['acceptedAnswer']['text'] for script in soup.select('script[type="application/ld+json"]') for node in json.loads(script.string or script.get_text()).get('@graph',[json.loads(script.string or script.get_text())]) if node.get('@type')=='FAQPage' for q in node['mainEntity']]
                record('sourcing_faq',route,actual_answers==expected_answers==encoded and any(text.endswith('before starting a sourcing request.') for text in actual_answers),'Visible answers and FAQ schema use the requested sourcing wording')
            if route=='/freight-research/buyer-purchase-order-to-freight-plan/':
                record('buyer_description',route,all(meta['content']==local.select_one('meta[name="description"]')['content'] and meta['content'].endswith('before starting a sourcing request.') for meta in soup.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]')),'Requested sourcing description in all description tags')
            kinds={'/sourcing/':'Service','/suppliers/':'Service','/delivery/':'Service','/contact/':'ContactPage','/landed-cost-calculator/':'WebApplication'}
            if route in kinds:
                nodes=[]
                for script in soup.select('script[type="application/ld+json"]'):
                    data=json.loads(script.string or script.get_text())
                    nodes.extend(data.get('@graph',[data]))
                types={node.get('@type') for node in nodes}
                record('requested_schema', route, kinds[route] in types and (route=='/contact/' or 'FAQPage' in types), 'Requested page/service/application and visible FAQ schema are present')
            if route in ('/', '/contact/'):
                form = soup.select_one('[data-request-form][data-audience="buyer_sourcing"]')
                sourcing = form.select_one('[data-sourcing-fields]')
                ok = not sourcing.has_attr('hidden') and not sourcing.has_attr('disabled')
                ok = ok and not form.select_one('textarea[name="freight_needs"]')
                ok = ok and form.select_one('[name="request_type"]')['value'] == 'buyer_sourcing'
                record('raw_form_default', route, bool(ok), 'Buyer form enabled in raw HTML; no obsolete freight textarea')
            if route in ('/', '/contact/', '/privacy-policy/'):
                ok = not re.search(r'not (?:currently )?enabled|not yet (?:been )?established|this release', response.text, re.I)
                record('status_copy_removed', route, ok, 'Removed internal deployment-status phrases')
        except (requests.RequestException, AttributeError, KeyError, TypeError) as exc:
            record('page_release', route, False, str(exc))
    for path in ('/sitemap.xml', '/sitemap-buyers.xml', '/sitemap-suppliers.xml', '/sitemap-delivery.xml', '/llms.txt', '/.well-known/security.txt'):
        response = session.get(BASE + path, timeout=20)
        expected = (ROOT / path.lstrip('/')).read_text(encoding='utf-8')
        record('text_release', path, response.status_code == 200 and response.text.strip() == expected.strip(), f'HTTP {response.status_code}; exact released text')
        if path == '/sitemap.xml':
            index = ET.fromstring(response.content)
            urls = []
            for node in index.findall('.//{*}loc'):
                section = session.get(node.text, timeout=20)
                urls.extend(entry.text for entry in ET.fromstring(section.content).findall('.//{*}loc'))
            record('sitemap_exclusion', path, len(urls) == 79 and len(urls) == len(set(urls)) and not any('/air-vs-ocean-for-product-launch/' in url for url in urls), f'{len(urls)} unique indexed URLs; overlapping freight article excluded')
    fields = ['check', 'status', 'detail', 'source_url', 'last_checked']
    for filename, data in [('live-audit.csv', rows), ('live-audit-errors.csv', [row for row in rows if row['status'] != 'pass'])]:
        with (OUT / filename).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
    errors = [row for row in rows if row['status'] != 'pass']
    print(json.dumps({'checks': len(rows), 'errors': errors}, ensure_ascii=False))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
