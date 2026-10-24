"""Regression checks for requested guide wording, citations and truthful markup."""

import json
import re
import unittest

from bs4 import BeautifulSoup

from guide_experience import BASE, HOME_TITLE, ROOT, check_new_page_review, documents, enforce_publication_gate, jsonld_nodes, route
from ocean_rates import load


class GuideExperienceTests(unittest.TestCase):
    def test_unreviewed_new_pages_are_blocked(self):
        with self.assertRaises(ValueError):
            check_new_page_review('/lanes/UNREVIEWED/',BeautifulSoup('<main><p>Unreviewed claim.</p></main>','html.parser'),{})
        enforce_publication_gate()
    def test_old_copy_and_raw_source_lines_do_not_reappear(self):
        changed=0
        for path in documents():
            soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            for anchor in soup.select('main a'):
                text=anchor.get_text(' ',strip=True)
                self.assertNotIn('Start a freight inquiry',text)
                if text=='Start a sourcing request':
                    self.assertEqual(anchor['href'],'/contact/#buyer-request')
                    changed+=1
            for script,data,nodes in jsonld_nodes(soup):
                for node in nodes:
                    if node.get('@type')=='BreadcrumbList':
                        self.assertFalse(any('Freight Research' in part.get('name','') for part in node['itemListElement']))
            for node in soup.select('script,style'):
                node.decompose()
            self.assertNotIn('source_url:',soup.get_text())
            self.assertNotIn('Freight Research',soup.get_text())
        self.assertGreaterEqual(changed,75)

    def test_requested_title_heading_and_descriptions(self):
        home=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
        self.assertEqual(home.title.text,HOME_TITLE)
        delivery=BeautifulSoup((ROOT/'delivery/index.html').read_text(encoding='utf-8'),'html.parser')
        self.assertEqual(delivery.h1.text,'Delivered to Your Door.')
        for relative in ['freight-research/index.html','freight-research/buyer-purchase-order-to-freight-plan/index.html']:
            soup=BeautifulSoup((ROOT/relative).read_text(encoding='utf-8'),'html.parser')
            self.assertNotIn('freight inquiry',soup.select_one('meta[name="description"]')['content'].lower())

    def test_schemas_match_visible_questions(self):
        wanted={'sourcing':'Service','suppliers':'Service','delivery':'Service','landed-cost-calculator':'WebApplication','contact':'ContactPage'}
        for name,kind in wanted.items():
            soup=BeautifulSoup((ROOT/name/'index.html').read_text(encoding='utf-8'),'html.parser')
            nodes=[node for _,_,part in jsonld_nodes(soup) for node in part]
            self.assertIn(kind,[node['@type'] for node in nodes])
            if name=='contact':
                continue
            faqs=[node for node in nodes if node.get('@type')=='FAQPage']
            self.assertEqual(len(faqs),1)
            visible=[(detail.summary.get_text(' ',strip=True),' '.join(p.get_text(' ',strip=True) for p in detail.find_all('p'))) for detail in soup.select('.faq-list details')]
            encoded=[(q['name'],q['acceptedAnswer']['text']) for q in faqs[0]['mainEntity']]
            self.assertEqual(encoded,visible)

    def test_normal_citation_links_retain_a_checked_date(self):
        for path in documents():
            soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            for anchor in soup.select('main li a[href^="https://"], main li a[href^="http://"]'):
                if 'flashcargoglobal.com' not in anchor['href']:
                    self.assertIsNotNone(anchor.find_parent('li').find('time'),f'{route(path)}: {anchor["href"]}')

    def test_every_mapped_lane_and_cost_page_has_the_shared_table(self):
        data=load()
        self.assertGreaterEqual(len(data['page_lanes']),45)
        for current,lane in data['page_lanes'].items():
            soup=BeautifulSoup((ROOT/current.strip('/')/'index.html').read_text(encoding='utf-8'),'html.parser')
            tables=soup.select('[data-ocean-rates]')
            self.assertEqual(len(tables),1,current)
            table=tables[0]
            self.assertEqual(table['data-rate-lane'],lane)
            expected=sorted(row['month'] for row in data['rates'] if row['lane']==lane)[-6:]
            self.assertEqual([time['datetime'] for time in table.select('tbody th time')],expected)
            self.assertEqual(len(table.select('thead th')),3)
            self.assertNotRegex(table.get_text(' ',strip=True),r'\b(live|guaranteed|firm)\b')
            self.assertEqual(table.select_one('.text-link')['href'],'/contact/#buyer-request')
            self.assertEqual(len(table.select('.rate-source-note')),2)


if __name__=='__main__':
    unittest.main()
