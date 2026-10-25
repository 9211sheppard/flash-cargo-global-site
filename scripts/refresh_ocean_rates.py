"""Refresh one reviewed public FBX weekly reading, never calculate index averages."""

import argparse
import csv
import json
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from ocean_rates import DATA_FILE, ROOT, FBX_REGIONS, TERMINAL, owner_today, validate
from trust_rollout_content import LANES

OUT=ROOT/'output/ocean-rates'

def verify_public_reading(record):
    row={'source_url':record['source_url'],'status':'unavailable','http_status':'','detail':'','last_checked':datetime.now(timezone.utc).isoformat()}
    patterns={
        'FBX01':r'at\s+\$([\d,]+)/FEU\s+to the West Coast',
        'FBX03':r'to\s+\$([\d,]+)/FEU\s+for the East Coast',
        'FBX11':r'N\.\s*Europe[^$]{0,150}\$([\d,]+)/FEU',
        'FBX13':r'Mediterranean[^$]{0,100}\$([\d,]+)/FEU',
    }
    try:
        response=requests.get(record['source_url'],timeout=20)
        row['http_status']=response.status_code
        if response.status_code!=200:
            row.update(status='blocked' if response.status_code in {401,403,429} else 'unavailable',detail='Skip this retrieval; no login or paid API.')
            return False,row
        text=BeautifulSoup(response.text,'html.parser').get_text(' ',strip=True)
        for key in ('report_date','publication_date'):
            day=datetime.fromisoformat(record[key])
            label=day.strftime('%B')+' '+str(day.day)+', '+str(day.year)
            if label not in text:
                raise ValueError('The configured report dates are not both present in the primary article.')
        if record.get('period_basis')!='week_before_report' or 'last week' not in text.lower():
            raise ValueError('The reading must be identified as the week before the dated report.')
        for reading in record['readings']:
            match=re.search(patterns[reading['index_lane']],text)
            if not match or int(match.group(1).replace(',',''))!=reading['40ft_usd']:
                raise ValueError('A primary reading does not match the reviewed source record.')
        row.update(status='verified',detail='Four unmodified public weekly readings and both report dates matched the primary article.')
        return True,row
    except (requests.RequestException,ValueError) as error:
        row['detail']=str(error)[:240]
        return False,row

def refresh(data,record,verified,checked):
    from build_trust_rollout import retired_target
    lanes=data['lanes']
    mapping={path:lane for path,lane in data['page_lanes'].items() if not retired_target(path)}
    previous={row['lane']:row for row in data.get('rates',[])} if data.get('schema_version')==2 else {}
    configured={row['index_lane']:row for row in record['readings']}
    for item in LANES:
        origin,destination=FBX_REGIONS[item['fbx']]
        lanes[item['lane_id']]={'label':item['index_label'],'guide_slugs':[item['slug']],'origin_region':origin,'destination_region':destination,'index_lane':item['fbx']}
        mapping['/freight-research/'+item['slug']+'/']=item['lane_id']
    rates=[]
    for lane_id,lane in lanes.items():
        row={'lane':lane_id,'kind':'quote_required','20ft_usd':None,'40ft_usd':None,'source_url':'https://flashcargoglobal.com/contact/#buyer-request','last_checked':checked}
        index=lane.get('index_lane')
        if index in configured and verified:
            reading=configured[index]
            row.update(kind='weekly_index_reading',source='freightos_fbx',currency='USD',index_lane=index,report_date=record['report_date'],period_basis=record['period_basis'],publication_date=record['publication_date'],attribution_url=TERMINAL,reported_40ft_usd=reading['40ft_usd'],source_url=reading['source_url'])
            row['40ft_usd']=reading['40ft_usd']
        elif index in configured and previous.get(lane_id,{}).get('kind')=='weekly_index_reading':
            row=previous[lane_id]
        rates.append(row)
    output={'schema_version':2,'policy':{'monthly_averages_allowed':False,'drewry_scfi_figures_allowed':False,'fbx_container_size':'40ft','fbx_use':'Market context only. This index reading is not used to price, settle or compare your order.','mode':'One unmodified public FBX weekly reading with attribution, or an explicitly approved dated written quote.'},'sources':{'freightos_fbx':{'name':'Freightos Baltic Index (FBX)','source_url':TERMINAL,'public_update_url':record['source_url'],'terms_url':record['terms_url'],'reuse_basis':record['reuse_basis']}},'lanes':lanes,'cost_hubs':[path for path in data.get('cost_hubs',[]) if not retired_target(path)],'page_lanes':dict(sorted(mapping.items())),'rates':rates,'last_checked':checked}
    return validate(output)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture-only',action='store_true')
    args=parser.parse_args()
    data=json.loads(DATA_FILE.read_text(encoding='utf-8'))
    record=json.loads((ROOT/'content/fbx-public-reading.json').read_text(encoding='utf-8'))
    if not record.get('reviewed'):
        raise SystemExit('Review the public primary reading and its reuse terms first.')
    automated,check=verify_public_reading(record)
    manual=record.get('reviewed') is True and record.get('last_checked')==owner_today().isoformat() and bool(record.get('verification_method'))
    verified=automated or manual
    OUT.mkdir(parents=True,exist_ok=True)
    for name,rows in [('source-checks.csv',[check]),('source-errors.csv',[] if automated else [check])]:
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(check));writer.writeheader();writer.writerows(rows)
    checked=datetime.now(timezone.utc).isoformat() if automated else record['last_checked']
    data=refresh(data,record,verified,checked)
    DATA_FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields=['lane','kind','report_date','period_basis','publication_date','reading_date','20ft_usd','40ft_usd','source_url','last_checked']
    with (OUT/'single-readings.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(data['rates'])
    if not args.capture_only:
        from build_cargo_global import main as build
        build()
    print(json.dumps({'automated_primary_check':automated,'dated_manual_primary_review':manual,'numeric_readings':sum(row['40ft_usd'] is not None for row in data['rates']),'mapped_pages':len(data['page_lanes'])}))

if __name__=='__main__':
    main()
