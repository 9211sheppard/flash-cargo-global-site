"""Check the trust rollout without treating templates as customer proof."""
import csv
import json
import unittest
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from guide_experience import ROOT, documents, route
from build_trust_rollout import retired_target
from trust_rollout_content import ANTI_PHISHING, BANK_CHANGE_POLICY, FBX_CONTEXT, PROCESS_LINE, PAYMENT_RULES, TEMPLATES, LANES


def page(path):
    return BeautifulSoup((ROOT/path.strip('/')/'index.html').read_text(encoding='utf-8'),'html.parser')


class TrustRolloutTests(unittest.TestCase):
    def test_payment_rules_are_mirrored_and_process_is_exact(self):
        for current in ('how-payment-works','terms'):
            text=page(current).get_text(' ',strip=True)
            for _,rule in PAYMENT_RULES:
                self.assertIn(rule,text)
            self.assertIn(BANK_CHANGE_POLICY,text)
            self.assertIn('balance only after sample approval and any agreed pre-shipment inspection.',text)
            self.assertNotIn('balance only after sample approval and the pre-shipment inspection.',text)
        for current in ('how-payment-works','about','sourcing'):
            self.assertIn(PROCESS_LINE,page(current).get_text(' ',strip=True))

    def test_every_form_has_payment_link_and_matching_verification(self):
        count=0
        for path in documents():
            soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            self.assertIn(ANTI_PHISHING,soup.footer.get_text(' ',strip=True))
            for form in soup.select('[data-request-form]'):
                count+=1
                action=form.select_one('[name=request_type]')['value']
                widget=form.select_one('[data-request-verification]')
                self.assertEqual(widget['data-action'],action)
                self.assertTrue(form.select_one('button[type=submit]').has_attr('disabled'))
                self.assertIsNotNone(form.select_one('a[href="/how-payment-works/"]'))
        self.assertEqual(count,4)

    def test_templates_are_blank_and_explicitly_labelled(self):
        soup=page('sourcing')
        self.assertIn('not completed orders',soup.select_one('#sample-documents').get_text())
        for filename,title,fields in TEMPLATES:
            with (ROOT/'assets'/(filename+'.csv')).open(encoding='utf-8-sig') as handle:
                rows=list(csv.DictReader(handle))
            self.assertEqual(len(rows),len(fields))
            self.assertTrue(all(row['your_entry']=='' and row['source_url'] and row['last_checked'] for row in rows))
        self.assertIn('No customs brokerage licence is claimed',soup.get_text())

    def test_retired_routes_are_immediate_canonical_redirects_without_old_content(self):
        retired=0
        for path in documents():
            soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
            target=retired_target(route(path))
            if target:
                retired+=1
                self.assertEqual(soup.select_one('meta[http-equiv=refresh]')['content'],'0; url=https://flashcargoglobal.com'+target)
                self.assertEqual(soup.select_one('link[rel=canonical]')['href'],'https://flashcargoglobal.com'+target)
                self.assertEqual(soup.select_one('meta[name=robots]')['content'],'noindex, follow')
                self.assertFalse(soup.select('[data-ocean-rates]'))
                self.assertFalse(soup.select('script[type="application/ld+json"]'))
            else:
                for anchor in soup.select('a[href]'):
                    parsed=urlsplit(anchor['href'])
                    if not parsed.netloc or parsed.netloc=='flashcargoglobal.com':
                        self.assertIsNone(retired_target(parsed.path))
        self.assertEqual(retired,28)

    def test_four_index_routes_have_single_weekly_readings_and_no_prohibited_sources(self):
        for lane in LANES:
            soup=page('freight-research/'+lane['slug'])
            rates=soup.select_one('[data-ocean-rates]')
            self.assertEqual(len(rates.select('tbody tr')),1)
            self.assertIn('Freightos Baltic Index (FBX)',rates.get_text())
            self.assertIsNotNone(rates.select_one('a[href="https://terminal.freightos.com/"]'))
            self.assertNotRegex(rates.get_text(),'Drewry|SCFI|month-to-date')
            self.assertEqual(len(rates.select('tbody td')),1)
            self.assertNotIn('20ft',soup.main.get_text())
            self.assertNotIn('benchmark',soup.get_text().lower())
            self.assertNotIn('comparing a quote with the reading',soup.get_text())
            self.assertIn(FBX_CONTEXT,soup.get_text())
            self.assertEqual(rates.select_one('tbody th').get_text(),'FBX weekly reading for the week before 20 Oct 2026, as reported by Freightos on 21 Oct 2026')
            self.assertIn(lane['index_label'],rates.get_text())

    def test_discovery_file_and_hub_match_the_market_context_policy(self):
        text=(ROOT/'llms.txt').read_text(encoding='utf-8')
        self.assertIn('https://flashcargoglobal.com/how-payment-works/',text)
        for lane in LANES:
            self.assertIn('https://flashcargoglobal.com/freight-research/'+lane['slug']+'/',text)
        hub=page('freight-research').get_text(' ',strip=True)
        self.assertNotIn('benchmark',hub.lower())
        self.assertIn(FBX_CONTEXT,hub)
        self.assertNotIn('freight inquiry',str(page('freight-research/air-vs-ocean-for-product-launch')).lower())


if __name__=='__main__':
    unittest.main()
