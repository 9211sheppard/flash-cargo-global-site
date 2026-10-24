"""Synthetic local fixtures test calculations, never published price evidence."""

import copy
from datetime import date
import unittest

from ocean_rates import load, month_closed, monthly_average, publication_dates, round_usd, validate


class OceanRateTests(unittest.TestCase):
    def rows(self):
        return [{'lane':'TEST_PORTS','size':'40ft','source':'TEST_INDEX','usd':amount,'reading_date':day,'source_url':'https://example.com/LOCAL_TEST','date_pulled':'2026-10-01'} for day,amount in zip(publication_dates('2026-09',3),[1000,1100,1200,1300])]

    def mean(self,rows,**changes):
        options={'month':'2026-09','lane':'TEST_PORTS','size':'40ft','source':'TEST_INDEX','expected_dates':publication_dates('2026-09',3),'today':date(2026,10,24)}
        options.update(changes)
        return monthly_average(rows,**options)

    def test_rounding_is_nearest_fifty_without_bankers_rounding(self):
        self.assertEqual(round_usd('1125'),1150)
        self.assertEqual(round_usd('1124.99'),1100)
        for value in [-1,0,'NaN','Infinity']:
            with self.assertRaises(ValueError):
                round_usd(value)

    def test_full_month_uses_the_weekly_arithmetic_mean(self):
        self.assertEqual(self.mean(self.rows()),1150)

    def test_missing_weeks_and_wrong_lane_size_or_source_cannot_make_a_price(self):
        self.assertIsNone(self.mean(self.rows()[:-1]))
        for field,value in [('lane','OTHER'),('size','20ft'),('source','OTHER')]:
            self.assertIsNone(self.mean(self.rows(),**{field:value}))

    def test_duplicates_do_not_weight_a_week_twice(self):
        self.assertEqual(self.mean(self.rows()+[self.rows()[0]]),1150)
        changed={**self.rows()[0],'usd':9999}
        with self.assertRaises(ValueError):
            self.mean(self.rows()+[changed])

    def test_open_month_is_not_published_as_complete(self):
        self.assertFalse(month_closed('2026-10',date(2026,10,24)))
        self.assertTrue(month_closed('2026-10',date(2026,11,1)))
        self.assertIsNone(self.mean(self.rows(),today=date(2026,9,30)))

    def test_unlicensed_or_unmatched_numeric_cells_are_rejected(self):
        data=load()
        data['rates'][0]['40ft_usd']=1150
        with self.assertRaises(ValueError):
            validate(data)

    def test_current_data_has_no_unsourced_prices_or_restricted_observations(self):
        data=load()
        for row in data['rates']:
            for size in ('20ft','40ft'):
                if row[size+'_usd'] is not None:
                    self.assertIn(size,row['evidence'])
        self.assertTrue(all(data['sources'][row['source']].get('publication_allowed') for row in data['observations']))

    def test_dated_twenty_foot_quote_needs_permission_and_its_own_evidence(self):
        data=load()
        row=data['rates'][0]
        data['lanes'][row['lane']].update(origin_region='LOCAL_TEST_ORIGIN',destination_region='LOCAL_TEST_DESTINATION')
        data['sources']['LOCAL_TEST_QUOTE']={'name':'LOCAL TEST ONLY','source_url':'https://example.com/LOCAL_TEST','hosts':['example.com'],'sizes':['20ft'],'publication_allowed':True,'kind':'dated_quote'}
        row['20ft_usd']=1300
        row['evidence']['20ft']={'kind':'dated_quote','source':'LOCAL_TEST_QUOTE','lane':row['lane'],'size':'20ft','currency':'USD','origin_region':'LOCAL_TEST_ORIGIN','destination_region':'LOCAL_TEST_DESTINATION','quote_date':'2026-09-17','source_url':'https://example.com/LOCAL_TEST','quoted_amount_usd':1290,'publication_approved':True}
        validate(data)
        row['evidence']['20ft']['destination_region']='OTHER_TEST_REGION'
        with self.assertRaisesRegex(ValueError,'different port region'):
            validate(data)
        row['evidence']['20ft']['destination_region']='LOCAL_TEST_DESTINATION'
        row['evidence']['20ft']['publication_approved']=False
        with self.assertRaises(ValueError):
            validate(data)

    def test_index_region_must_match_before_a_monthly_price_can_publish(self):
        data=load()
        row=data['rates'][0]
        source=data['sources']['drewry_wci']
        source['publication_allowed']=True
        lane=data['lanes'][row['lane']]
        lane.update(index_lane='shanghai-los-angeles',origin_region='OTHER_TEST_REGION',destination_region='los-angeles-long-beach')
        values=[{**value,'lane':'shanghai-los-angeles','source':'drewry_wci','source_url':'https://www.drewry.co.uk/LOCAL_TEST_ONLY'} for value in self.rows()]
        row['40ft_usd']=1150
        row['evidence']['40ft']={'kind':'weekly_index_average','lane':row['lane'],'source':'drewry_wci','expected_reading_dates':publication_dates('2026-09',3),'observations':values}
        with self.assertRaisesRegex(ValueError,'different port region'):
            validate(data)
        lane['origin_region']='shanghai-ningbo'
        validate(data)


if __name__=='__main__':
    unittest.main()
