"""Focused checks for audience routing, raw forms and ranking-safe publication."""

import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
from audience_page_content import AUDIENCE_PAGES
from build_audience_rollout import NAV, settings, supplier_cta
from build_trust_rollout import retired_target


def soup(path):
    return BeautifulSoup((ROOT / path).read_text(encoding='utf-8'), 'html.parser')


def similarity(a, b):
    def shingles(text):
        words = re.findall(r'\w+', text.lower())
        return {tuple(words[i:i + 5]) for i in range(len(words) - 4)}
    left, right = shingles(a), shingles(b)
    return len(left & right) / min(len(left), len(right)) if left and right else 0


class AudienceTests(unittest.TestCase):
    def test_every_original_url_and_title_is_preserved(self):
        baseline = json.loads((ROOT / 'content/audience-baseline.json').read_text(encoding='utf-8'))
        self.assertEqual(len(baseline), 111)
        for row in baseline:
            self.assertTrue((ROOT / row['file']).exists())
            if retired_target(row['path']):
                self.assertTrue(soup(row['file']).html.has_attr('data-retired-route'))
                continue
            expected = 'Cargo Global | Sourcing & Delivery to the US, Canada and Mexico' if row['path'] == '/' else row['title']
            self.assertEqual(soup(row['file']).title.get_text(' ', strip=True), expected)

    def test_home_has_the_requested_three_paths_and_original_h1(self):
        home = soup('index.html')
        self.assertEqual(home.h1.get_text(' ', strip=True), 'Buy Anything. From Anywhere. Delivered to Your Door.')
        cards = home.select('.audience-paths > a')
        self.assertEqual([card['href'] for card in cards], ['/contact/#buyer-request', '/suppliers/', '/delivery/'])
        self.assertEqual([card.h2.get_text() for card in cards], ["I'm buying", "I'm a manufacturer", 'I need it delivered'])
        self.assertEqual([a.get_text(' ', strip=True) for a in home.select('#primary-menu a')], [name for name, _ in NAV])
        hero = home.select_one('.hero-media')
        self.assertIn('768w', hero['srcset'])
        self.assertTrue((ROOT / 'assets/sourcing-assortment-768.webp').stat().st_size < 40000)
        self.assertFalse(home.select('script:not([src]):not([type="application/ld+json"])'))
        self.assertFalse(home.select_one('.wordmark').has_attr('aria-label'))
        self.assertEqual(home.select_one('.wordmark').get_text(' ', strip=True), 'flash CARGO GLOBAL')
        self.assertNotIn("script-src 'self' 'unsafe-inline'", home.select_one('meta[http-equiv="Content-Security-Policy"]')['content'])

    def test_all_three_form_tags_and_full_raw_fields(self):
        required = {
            'buyer_sourcing': ['product_name', 'quantity', 'quantity_unit', 'target_price', 'origin_preference', 'delivery_country', 'delivery_city', 'timeline', 'product_specs', 'spec_link'],
            'supplier_application': ['company_name', 'supplier_country', 'supplier_products', 'hs_codes', 'minimum_order', 'monthly_capacity', 'certifications', 'export_markets', 'company_website', 'sample_availability', 'agree_vetting'],
            'delivery_only': ['product_name', 'delivery_quantity', 'packed_details', 'origin_location', 'delivery_country', 'delivery_city', 'timeline', 'delivery_requirements'],
        }
        documents = [soup('contact/index.html'), soup('suppliers/index.html')]
        found = {}
        for document in documents:
            for form in document.select('[data-request-form]'):
                tag = form.select_one('[name="request_type"]')['value']
                found[tag] = form
                self.assertEqual(form['method'], 'post')
                self.assertEqual(form['action'], 'https://flash-cargo-form.old-sun-35f9.workers.dev/contact-request')
                self.assertIsNone(form.select_one('[name="phone"], [name="full_name"]'))
                self.assertIsNotNone(form.select_one('[name="email"][type="email"][required]'))
                self.assertIsNotNone(form.select_one('[name="website"]'))
                self.assertIsNotNone(form.select_one('[name="form_started_at"]'))
                self.assertEqual(form.select_one('[name="javascript_enabled"]')['value'], 'no')
        self.assertEqual(set(found), set(required))
        for tag, fields in required.items():
            for name in fields:
                self.assertIsNotNone(found[tag].select_one(f'[name="{name}"]'), f'{tag}: {name}')

    def test_premium_voice_is_selective_and_supported(self):
        home = soup('index.html')
        self.assertIn('We curate a supplier shortlist', home.select_one('.hero-subline').get_text())
        self.assertIn('Personal attention', home.select_one('.sourcing-hero .kicker').get_text())
        self.assertIn('curates supplier options', soup('sourcing/index.html').get_text())
        self.assertIn('one point of contact', soup('about/index.html').get_text())
        self.assertNotRegex(home.get_text(), r'world.?s best|guaranteed savings|exclusive factory access')

    def test_new_hubs_have_real_content_and_markup(self):
        for page in AUDIENCE_PAGES:
            document = soup(page['path'].strip('/') + '/index.html')
            self.assertEqual(len(document.select('h1')), 1)
            self.assertTrue(40 <= len(page['quick_answer'].split()) <= 60)
            text = ' '.join(p for _, paragraphs in page['sections'] for p in paragraphs)
            text += ' ' + ' '.join(q + ' ' + a for q, a in page['faqs'])
            self.assertGreaterEqual(len(text.split()), 1200)
            self.assertTrue(6 <= len(document.select('.faq-list details')) <= 10)
            self.assertLess(len(str(document).encode()), 100000)
            types = {entry.get('@type') for script in document.select('script[type="application/ld+json"]') for entry in json.loads(script.string).get('@graph', [])}
            self.assertTrue({'Organization', 'Article', 'FAQPage', 'HowTo', 'BreadcrumbList'} <= types)
            self.assertEqual(len(document.select('.facts-table tbody tr')), 3)
            self.assertEqual(len(document.select('.facts-table time')), 3)

    def test_new_hub_text_is_not_mass_duplicated(self):
        for index, left in enumerate(AUDIENCE_PAGES):
            a = ' '.join(p for _, paragraphs in left['sections'] for p in paragraphs)
            for right in AUDIENCE_PAGES[index + 1:]:
                b = ' '.join(p for _, paragraphs in right['sections'] for p in paragraphs)
                self.assertLess(similarity(a, b), 0.30)

    def test_sitemaps_partition_all_indexable_pages(self):
        index = ET.parse(ROOT / 'sitemap.xml')
        self.assertTrue(index.getroot().tag.endswith('sitemapindex'))
        listed = [node.text for node in index.findall('.//{*}loc')]
        self.assertEqual(set(listed), {'https://flashcargoglobal.com/sitemap-' + name + '.xml' for name in ('buyers', 'suppliers', 'delivery')})
        urls = []
        for name in ('buyers', 'suppliers', 'delivery'):
            tree = ET.parse(ROOT / f'sitemap-{name}.xml')
            for entry in tree.findall('{*}url'):
                url = entry.find('{*}loc').text
                urls.append(url)
                self.assertRegex(entry.find('{*}lastmod').text, r'^\d{4}-\d{2}-\d{2}$')
                route = url.removeprefix('https://flashcargoglobal.com').strip('/')
                path = route + '/index.html' if route else 'index.html'
                self.assertNotIn('noindex', soup(path).select_one('meta[name="robots"]')['content'])
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(len(urls), 84)
        self.assertFalse(any('/buyers/' in url for url in urls))

    def test_unique_metadata_and_no_public_contact_values(self):
        titles, descriptions = [], []
        for path in ROOT.rglob('*.html'):
            if path.relative_to(ROOT).parts[0] in ('output', 'content'):
                continue
            document = soup(path.relative_to(ROOT))
            if document.html.has_attr('data-retired-route'):
                continue
            titles.append(document.title.get_text(' ', strip=True))
            descriptions.append(document.select_one('meta[name="description"]')['content'])
            self.assertNotRegex(str(document), r'[\w.+-]+@[\w.-]+\.[a-z]{2,}')
            for element in document.select('script, style, .legal, .wordmark-flash'):
                element.decompose()
            visible = document.get_text(' ', strip=True)
            self.assertNotRegex(visible, r'\bAI\b|[\w.+-]+@[\w.-]+\.[a-z]{2,}|flashcargonetwork\.com')
            self.assertNotRegex(visible, r'not (?:currently )?enabled|not yet established|This release')
        self.assertFalse(any(count > 1 for count in Counter(titles).values()))
        self.assertFalse(any(count > 1 for count in Counter(descriptions).values()))

    def test_turnstile_is_really_configured_for_production(self):
        public_key = settings().get('turnstile_sitekey')
        self.assertTrue(public_key, 'Supplier publication is blocked until a real production widget is configured.')
        widget = soup('suppliers/index.html').select_one('.cf-turnstile')
        self.assertEqual(widget['data-sitekey'], public_key)
        self.assertEqual(widget['data-action'], 'supplier_application')
        self.assertNotIn(public_key, ('1x00000000000000000000AA', '2x00000000000000000000AB'))

    def test_confirmation_is_the_requested_copy(self):
        received = soup('thank-you.html')
        self.assertEqual(received.h1.get_text(), 'Received.')
        self.assertIn('We reply within one business day.', received.get_text())

    def test_enquiry_notifications_have_real_delivery_evidence(self):
        self.assertTrue(settings().get('notification_delivery_verified'), 'Inbox delivery must be verified before release, not inferred from saved form records.')

    def test_supplier_introductions_match_language_and_supported_region(self):
        for language, word in [('en', 'Canada'), ('es', 'Canadá'), ('fr', 'Canada'), ('zh', '加拿大'), ('hi', 'कनाडा')]:
            cta = BeautifulSoup(supplier_cta('india', language), 'html.parser')
            self.assertIn(word, cta.get_text())
            self.assertEqual(cta.a['href'], '/suppliers/')
            self.assertNotRegex(cta.get_text(), 'Japan|Australia|Europe')


if __name__ == '__main__':
    unittest.main()
