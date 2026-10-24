"""Regression checks for the published sourcing and duplicate-site cleanup."""

import json
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OLD_HOST = 'flash-cargo-global.old-sun-35f9.workers.dev'
FORM_HOST = 'flash-cargo-form.old-sun-35f9.workers.dev'


def page(path):
    return BeautifulSoup((ROOT / path).read_text(encoding='utf-8'), 'html.parser')


class SourcingAuditTests(unittest.TestCase):
    def test_sourcing_is_the_raw_html_default(self):
        for path in ('index.html', 'contact/index.html'):
            soup = page(path)
            form = soup.select_one('[data-inquiry-form]')
            sourcing = form.select_one('[data-sourcing-fields]')
            self.assertNotIn('hidden', sourcing.attrs)
            self.assertNotIn('disabled', sourcing.attrs)
            self.assertTrue(form.select_one('[value="sourcing"]').has_attr('checked'))
            self.assertTrue(form.select_one('[data-freight-fields]').has_attr('hidden'))
            freight = form.select_one('textarea[name="freight_needs"]')
            self.assertTrue(freight.has_attr('disabled'))
            self.assertFalse(freight.has_attr('required'))
            self.assertFalse(form.select_one('[data-sourcing-summary]').has_attr('disabled'))
            self.assertIn(FORM_HOST, form['action'])
            self.assertIsNotNone(form.select_one('[name="website"]'))
            self.assertIsNotNone(form.select_one('[name="form_started_at"]'))

    def test_launch_freight_page_is_noindex_and_not_listed(self):
        path = 'freight-research/air-vs-ocean-for-product-launch/index.html'
        self.assertIn('noindex', page(path).select_one('meta[name="robots"]')['content'])
        urls = {node.text for node in ET.parse(ROOT / 'sitemap.xml').findall('.//{*}loc')}
        self.assertNotIn('https://flashcargoglobal.com/freight-research/air-vs-ocean-for-product-launch/', urls)

    def test_country_hub_and_legacy_article_titles_are_distinct(self):
        paths = ['freight-research/index.html', 'freight-research/en/index.html']
        paths += ['freight-research/' + slug + '/index.html' for slug in ('air-vs-ocean-for-product-launch', 'buyer-purchase-order-to-freight-plan', 'factory-ready-date-vs-cargo-ready-date', 'italy-clothing-manufacturer-export-to-australia', 'manufacturer-commercial-invoice-before-freight-quote')]
        titles, headings = [], []
        for path in paths:
            soup = page(path)
            titles.append(soup.title.get_text(strip=True))
            headings.append(soup.h1.get_text(' ', strip=True))
        self.assertEqual(len(set(titles)), 7)
        self.assertEqual(len(set(headings)), 7)

    def test_removed_internal_status_copy(self):
        for path in ('index.html', 'contact/index.html', 'privacy-policy/index.html', 'llms.txt'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertIsNone(re.search(r'not (?:currently )?enabled|not yet (?:been )?established|this release', text, re.I))

    def test_research_hub_is_sourcing_first(self):
        soup = page('freight-research/index.html')
        self.assertIn('sourcing', soup.select_one('meta[name="description"]')['content'])
        self.assertFalse(any('freight' in h.get_text().lower() for h in soup.select('.wide-grid h3')))
        self.assertFalse(any('air-vs-ocean-for-product-launch' in a['href'] for a in soup.select('a[href]')))
        def contacts(value):
            if isinstance(value, dict):
                if 'contactType' in value:
                    yield value['contactType']
                for child in value.values():
                    yield from contacts(child)
            elif isinstance(value, list):
                for child in value:
                    yield from contacts(child)
        found = [contact for script in soup.select('script[type="application/ld+json"]') for contact in contacts(json.loads(script.string))]
        self.assertTrue(found)
        self.assertEqual(set(found), {'Product sourcing request'})

    def test_policy_drops_old_site_but_keeps_intake(self):
        for path in ROOT.rglob('*.html'):
            if path.relative_to(ROOT).parts[0] in ('output', 'content'):
                continue
            policy = page(path.relative_to(ROOT)).select_one('meta[http-equiv="Content-Security-Policy"]')['content']
            self.assertNotIn('static.wixstatic.com', policy)
            self.assertNotIn(OLD_HOST, policy)
            self.assertIn(FORM_HOST, policy)
        policy = (ROOT / '_headers').read_text()
        self.assertNotIn('static.wixstatic.com', policy)
        self.assertNotIn(OLD_HOST, policy)

    def test_security_contact_is_contact_page(self):
        self.assertEqual((ROOT / '.well-known/security.txt').read_text().splitlines()[0], 'Contact: https://flashcargoglobal.com/contact/')

    def test_no_held_lane_guide_enters_sitemap(self):
        urls = [node.text for node in ET.parse(ROOT / 'sitemap.xml').findall('.//{*}loc')]
        self.assertFalse(any('/buyers/' in url for url in urls))


if __name__ == '__main__':
    unittest.main()
