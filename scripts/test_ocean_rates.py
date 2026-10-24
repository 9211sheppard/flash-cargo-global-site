"""Local mutations check that unapproved or derived rates cannot publish."""

import copy
import unittest
from datetime import date

from ocean_rates import amount, display_amount, load, render_table, validate


class OceanRateTests(unittest.TestCase):
    def data(self):
        return copy.deepcopy(load(today=date(2026,10,24)))

    def reading(self,data):
        return next(row for row in data['rates'] if row['kind']=='weekly_index_reading')

    def test_exact_amounts_are_not_rounded_or_derived(self):
        self.assertEqual(display_amount(8126),'US$8,126')
        self.assertEqual(display_amount('1125.25'),'US$1,125.25')
        self.assertEqual(display_amount(None),'Quote required')
        for value in [-1,0,'NaN','Infinity']:
            with self.assertRaises(ValueError):
                amount(value)

    def test_current_readings_have_primary_sources_and_no_monthly_history(self):
        data=self.data()
        readings=[row for row in data['rates'] if row['kind']=='weekly_index_reading']
        self.assertEqual({row['index_lane']:row['40ft_usd'] for row in readings},{'FBX01':8126,'FBX03':9700,'FBX11':3442,'FBX13':3927})
        self.assertFalse(data.get('observations'))
        self.assertFalse(data.get('dated_quotes'))
        self.assertTrue(all(row['20ft_usd'] is None for row in readings))
        for row in data['rates']:
            self.assertTrue(row['source_url'])
            self.assertTrue(row['last_checked'])

    def test_unapproved_sources_ratios_and_averages_are_rejected(self):
        for changes in [{'source':'drewry_wci'},{'source':'sse_scfi'},{'20ft_usd':4063},{'monthly_average':True},{'40ft_usd':8150},{'kind':'monthly_average'}]:
            data=self.data()
            self.reading(data).update(changes)
            with self.assertRaises(ValueError):
                validate(data,today=date(2026,10,24))

    def test_regional_coverage_must_match_the_guide(self):
        data=self.data()
        row=self.reading(data)
        data['lanes'][row['lane']]['destination_region']='mediterranean'
        with self.assertRaisesRegex(ValueError,'regional route'):
            validate(data,today=date(2026,10,24))

    def test_primary_source_attribution_and_dates_are_required(self):
        for changes in [{'source_url':'https://unrelated.example/rate'},{'attribution_url':'https://example.com/'},{'reading_date':'2026-11-01'},{'publication_date':'2026-11-01'}]:
            data=self.data()
            self.reading(data).update(changes)
            with self.assertRaises(ValueError):
                validate(data,today=date(2026,10,24))

    def test_duplicate_and_missing_records_do_not_pass(self):
        data=self.data()
        data['rates'].append(copy.deepcopy(data['rates'][0]))
        with self.assertRaises(ValueError):
            validate(data)
        data=self.data()
        data['rates'][0]['source_url']=''
        with self.assertRaises(ValueError):
            validate(data)

    def test_written_quotes_require_explicit_approval_and_matching_scope(self):
        data=self.data()
        row=self.reading(data)
        lane=data['lanes'][row['lane']]
        row.update(kind='written_quote',source='cargo_global_written_quote',quote_reference='LOCAL_TEST_ONLY',publication_approved=True,source_url='https://flashcargoglobal.com/LOCAL_TEST_ONLY/',scope='port_to_port',origin_region=lane['origin_region'],destination_region=lane['destination_region'],**{'20ft_usd':1234})
        validate(data,today=date(2026,10,24))
        row['publication_approved']=False
        with self.assertRaises(ValueError):
            validate(data,today=date(2026,10,24))
        row['publication_approved']=True
        row['scope']='delivered'
        with self.assertRaises(ValueError):
            validate(data,today=date(2026,10,24))

    def test_weekly_display_has_one_reading_and_full_attribution(self):
        data=self.data()
        row=self.reading(data)
        html=render_table(data,row['lane'])
        self.assertEqual(html.count('<tbody><tr>'),1)
        self.assertIn('https://terminal.freightos.com/',html)
        self.assertIn('Freightos Baltic Index (FBX)',html)
        self.assertIn('not a monthly average',html)
        self.assertIn('Published <time datetime="2026-10-21"',html)
        self.assertIn('Weekly update dated 2026-10-20',html)
        self.assertIn('Quote required',html)
        with self.assertRaises(ValueError):
            render_table(data,row['lane'],'hi')

    def test_empty_rates_collapse_to_one_request_line(self):
        data=self.data()
        row=next(row for row in data['rates'] if row['kind']=='quote_required')
        html=render_table(data,row['lane'])
        self.assertNotIn('<table',html)
        self.assertIn('Ocean rates for this lane: quote required. ',html)
        self.assertIn('Start a sourcing request.</a>',html)


if __name__=='__main__':
    unittest.main()
