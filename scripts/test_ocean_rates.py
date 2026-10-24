"""Synthetic local fixtures test calculations, never published price evidence."""

import copy
from datetime import date
import unittest

from ocean_rates import load, month_closed, monthly_average, publication_dates, round_usd, validate, render_table


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

    def test_twenty_foot_prices_must_come_directly_from_scfi(self):
        data=load()
        row=data['rates'][0]
        data['lanes'][row['lane']].update(index_lane='shanghai-europe',origin_region='shanghai-ningbo',destination_region='north-europe')
        data['sources']['sse_scfi']['publication_allowed']=True
        days=publication_dates('2026-09',4)
        values=[{**value,'lane':'shanghai-europe','size':'20ft','source':'sse_scfi','reading_date':day,'source_url':'https://en.sse.net.cn/LOCAL_TEST_ONLY'} for value,day in zip(self.rows(),days)]
        row['20ft_usd']=1150
        row['evidence']['20ft']={'kind':'weekly_index_average','source':'sse_scfi','lane':row['lane'],'expected_reading_dates':days,'observations':values}
        validate(data)
        row['evidence']['20ft']['source']='drewry_wci'
        data['sources']['drewry_wci']['publication_allowed']=True
        with self.assertRaises(ValueError):
            validate(data)
        row['evidence']['20ft']['source']='LOCAL_TEST_QUOTE'
        with self.assertRaises(ValueError):
            validate(data)

    def test_index_region_must_match_before_a_monthly_price_can_publish(self):
        data=load()
        row=data['rates'][0]
        source=data['sources']['drewry_wci']
        source['publication_allowed']=True
        lane=data['lanes'][row['lane']]
        lane.update(index_lane='shanghai-los-angeles',origin_region='shanghai-ningbo',destination_region='north-europe')
        values=[{**value,'lane':'shanghai-los-angeles','source':'drewry_wci','source_url':'https://www.drewry.co.uk/LOCAL_TEST_ONLY'} for value in self.rows()]
        row['40ft_usd']=1150
        row['evidence']['40ft']={'kind':'weekly_index_average','lane':row['lane'],'source':'drewry_wci','expected_reading_dates':publication_dates('2026-09',3),'observations':values}
        with self.assertRaisesRegex(ValueError,'different port region'):
            validate(data)
        lane['destination_region']='los-angeles-long-beach'
        validate(data)

    def test_month_to_date_needs_every_reading_through_its_cutoff(self):
        rows=self.rows()[:3]
        args={'expected_dates':publication_dates('2026-09',3)[:3],'today':date(2026,9,17),'as_of':'2026-09-17'}
        self.assertEqual(self.mean(rows,**args),1100)
        self.assertIsNone(self.mean(rows[:-1],**args))
        self.assertIsNone(self.mean(rows,**{**args,'as_of':'2026-09-24'}))

    def test_october_numeric_series_requires_month_to_date_label_and_cutoff(self):
        data=load()
        row=next(row for row in data['rates'] if row['month']=='2026-10')
        data['rates']=[row]
        data['lanes'][row['lane']].update(index_lane='shanghai-los-angeles',origin_region='shanghai-ningbo',destination_region='los-angeles-long-beach')
        data['sources']['drewry_wci']['publication_allowed']=True
        days=[day for day in publication_dates('2026-10',3) if day<='2026-10-24']
        values=[{**value,'lane':'shanghai-los-angeles','source':'drewry_wci','reading_date':day,'source_url':'https://www.drewry.co.uk/LOCAL_TEST_ONLY'} for value,day in zip(self.rows(),days)]
        row.update(period='month_to_date',as_of='2026-10-24',**{'40ft_usd':1150})
        row['evidence']['40ft']={'kind':'weekly_index_average','source':'drewry_wci','lane':row['lane'],'as_of':'2026-10-24','expected_reading_dates':days,'observations':values}
        validate(data,today=date(2026,10,24))
        html=render_table(data,row['lane'],today=date(2026,10,24))
        self.assertIn('Oct 2026 (month-to-date)',html)
        self.assertIn('month-to-date: 2026-10-24',html)
        row['evidence']['40ft'].pop('as_of')
        with self.assertRaisesRegex(ValueError,'cutoff'):
            validate(data,today=date(2026,10,24))

    def test_empty_rates_collapse_to_one_request_line(self):
        data=load()
        html=render_table(data,next(iter(data['lanes'])))
        self.assertNotIn('<table',html)
        self.assertIn('Ocean rates for this lane: quote required. ',html)
        self.assertIn('Start a sourcing request.</a>',html)


if __name__=='__main__':
    unittest.main()
