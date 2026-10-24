"""Collect public weekly evidence; refresh only completed monthly series."""

import argparse
import csv
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from ocean_rates import DATA_FILE, ROOT, SIZES, monthly_average, owner_today, publication_dates, round_usd, validate

OUT = ROOT / 'output' / 'ocean-rates'


def fetch_sources(data):
    rows, pages = [], {}
    session = requests.Session()
    session.headers['User-Agent'] = 'CargoGlobalPublicSourceReview/1.0 (+https://flashcargoglobal.com/contact/)'
    for key, source in data['sources'].items():
        for url in dict.fromkeys([source['source_url'], source.get('access_url', source['source_url'])]):
            now = datetime.now(timezone.utc).isoformat()
            try:
                response = session.get(url, timeout=20)
                status = 'available' if response.status_code == 200 else 'blocked' if response.status_code in {401, 403, 429} else 'unavailable'
                rows.append({'source':key,'source_url':url,'status':status,'http_status':response.status_code,'detail':'Public page retrieval only; no login, credentials or paid API.','last_checked':now})
                if response.status_code == 200:
                    pages[(key, url)] = response.text
            except requests.RequestException as exc:
                rows.append({'source':key,'source_url':url,'status':'unavailable','http_status':'','detail':type(exc).__name__,'last_checked':now})
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, selected in [('source-checks.csv', rows), ('source-errors.csv', [row for row in rows if row['status'] != 'available'])]:
        with (OUT / filename).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(selected)
    return rows, pages


def collect_drewry(html, url, checked):
    text = BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)
    match = re.search(r'Our detailed assessment for \w+,\s*(\d{1,2} [A-Za-z]{3} \d{4})', text)
    if not match:
        return []
    reading = datetime.strptime(match.group(1), '%d %b %Y').date()
    if reading > owner_today():
        return []
    rows = []
    for destination in ('Los Angeles', 'New York', 'Rotterdam', 'Genoa'):
        pattern = r'Shanghai to ' + re.escape(destination) + r'[^$]{0,110}\$([\d,]+)\s+per\s+40ft\s+container'
        values = re.findall(pattern, text)
        if len(set(values)) != 1:
            continue
        rows.append({'lane':'shanghai-' + destination.lower().replace(' ', '-'),'size':'40ft','usd':int(values[0].replace(',', '')),'reading_date':reading.isoformat(),'source':'drewry_wci','source_url':url,'date_pulled':checked})
    return rows


def refresh(data, *, today, checked, pages):
    observations = {(row['source'],row['lane'],row['size'],row['reading_date']):row for row in data['observations']}
    drewry = data['sources']['drewry_wci']
    content = pages.get(('drewry_wci', drewry['source_url']))
    if content and drewry.get('publication_allowed'):
        for row in collect_drewry(content, drewry['source_url'], checked):
            identity = (row['source'],row['lane'],row['size'],row['reading_date'])
            if identity not in observations or observations[identity]['usd'] == row['usd']:
                observations[identity] = row
    data['observations'] = sorted(observations.values(), key=lambda row:(row['reading_date'],row['lane'],row['size']))
    months = set(data['initial_months'])
    year, number = today.year, today.month - 1
    if number == 0:
        year, number = year - 1, 12
    last_closed = f'{year:04d}-{number:02d}'
    cursor = min(months)
    while cursor <= last_closed:
        months.add(cursor)
        year, number = map(int,cursor.split('-'))
        cursor = f'{year+1:04d}-01' if number == 12 else f'{year:04d}-{number+1:02d}'
    months = sorted(months)[-data['retain_months']:]
    previous = {(row['lane'],row['month']):row for row in data['rates']}
    records = []
    for lane_id, lane in data['lanes'].items():
        for month in months:
            row = previous.get((lane_id,month),{'lane':lane_id,'month':month,'20ft_usd':None,'40ft_usd':None,'source':'Quote required; no verified matching complete monthly series.','source_url':drewry['source_url'],'checked_sources':list(data['sources']),'date_pulled':checked,'evidence':{}})
            if all(row[size+'_usd'] is None for size in SIZES):
                row['date_pulled'] = checked
            for size in SIZES:
                if not lane.get('index_lane') or not lane.get('origin_region') or not lane.get('destination_region'):
                    continue
                for source_id, source in data['sources'].items():
                    if not source.get('publication_allowed'):
                        continue
                    if size not in source.get('lane_sizes',{}).get(lane['index_lane'],[]):
                        continue
                    if source.get('lane_regions',{}).get(lane['index_lane']) != [lane['origin_region'],lane['destination_region']]:
                        continue
                    expected = publication_dates(month,source['publication_weekday'])
                    amount = monthly_average(data['observations'],month=month,lane=lane['index_lane'],size=size,source=source_id,expected_dates=expected,today=today)
                    if amount is None:
                        continue
                    values = [value for value in data['observations'] if value['source']==source_id and value['lane']==lane['index_lane'] and value['size']==size and value['reading_date'] in expected]
                    row[size+'_usd'] = amount
                    row['source'] = source['name']
                    row['source_url'] = source['source_url']
                    row['date_pulled'] = checked
                    row['evidence'][size] = {'kind':'weekly_index_average','source':source_id,'lane':lane_id,'expected_reading_dates':expected,'observations':values}
                    break
            if row['20ft_usd'] is None and month < today.strftime('%Y-%m') and lane.get('origin_region') and lane.get('destination_region'):
                quotes = [quote for quote in data.get('dated_quotes', []) if quote.get('lane')==lane_id and quote.get('size')=='20ft' and quote.get('currency')=='USD' and quote.get('origin_region')==lane['origin_region'] and quote.get('destination_region')==lane['destination_region'] and quote.get('quote_date','').startswith(month+'-') and quote.get('publication_approved') and quote.get('scope')=='port_to_port' and data['sources'].get(quote.get('source'),{}).get('publication_allowed')]
                if quotes:
                    quote=max(quotes,key=lambda value:value['quote_date'])
                    source=data['sources'][quote['source']]
                    row['20ft_usd']=round_usd(quote['usd'])
                    row['evidence']['20ft']={'kind':'dated_quote','lane':lane_id,'source':quote['source'],'size':'20ft','currency':'USD','origin_region':quote['origin_region'],'destination_region':quote['destination_region'],'quote_date':quote['quote_date'],'source_url':quote['source_url'],'quoted_amount_usd':quote['usd'],'publication_approved':True}
                    row['source']=source['name']
                    row['source_url']=quote['source_url']
                    if quote['source'] not in row['checked_sources']:
                        row['checked_sources'].append(quote['source'])
            records.append(row)
    data['rates'] = records
    mapping = {}
    for path in (ROOT/'freight-research').rglob('index.html'):
        soup = BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        if not soup.select_one('article.guide-article'):
            continue
        slug = path.parent.name
        for lane_id, lane in data['lanes'].items():
            if slug in lane['guide_slugs']:
                mapping['/'+path.relative_to(ROOT).as_posix()[:-10]] = lane_id
    mapping.update({path:'shipment-specific' for path in data['cost_hubs']})
    data['page_lanes'] = dict(sorted(mapping.items()))
    data['last_checked'] = checked
    return validate(data,today)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-only',action='store_true',help='Collect public evidence without rebuilding the website.')
    args = parser.parse_args()
    data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    restricted = [row for row in data['observations'] if not data['sources'][row['source']].get('publication_allowed')]
    if restricted:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT/'unpublished-research-observations.json').write_text(json.dumps(restricted,ensure_ascii=False,indent=2),encoding='utf-8')
        data['observations'] = [row for row in data['observations'] if data['sources'][row['source']].get('publication_allowed')]
    checks, pages = fetch_sources(data)
    checked = datetime.now(timezone.utc).isoformat()
    data = refresh(data,today=owner_today(),checked=checked,pages=pages)
    DATA_FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields = ['lane','month','20ft_usd','40ft_usd','source','source_url','date_pulled']
    with (OUT/'monthly-rates.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data['rates'])
    if not args.capture_only:
        from build_cargo_global import main as build
        build()
    print(json.dumps({'rates':len(data['rates']),'mapped_pages':len(data['page_lanes']),'public_weekly_readings':len(data['observations']),'numeric_cells':sum(row[size+'_usd'] is not None for row in data['rates'] for size in SIZES),'source_errors':sum(row['status']!='available' for row in checks)}))


if __name__ == '__main__':
    main()
