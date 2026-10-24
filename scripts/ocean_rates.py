"""One attributed public FBX weekly reading or an approved written quote per lane."""

import json
from datetime import date, datetime
from decimal import Decimal
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'user_config.json').read_text(encoding='utf-8')) if (ROOT/'user_config.json').exists() else {}
DATA_FILE=ROOT/CONFIG.get('ocean_rates_file','ocean-rates.json')
SIZES=('20ft','40ft')
TERMINAL='https://terminal.freightos.com/'
FBX_REGIONS={
    'FBX01':('china-east-asia','north-america-west-coast'),
    'FBX03':('china-east-asia','north-america-east-coast'),
    'FBX11':('china-east-asia','north-europe'),
    'FBX13':('china-east-asia','mediterranean'),
}
FALLBACK_COPY={
    'en':('Ocean rates for this lane: quote required. ','Start a sourcing request.'),
    'es':('Tarifas marítimas para esta ruta: cotización necesaria. ','Inicie una solicitud de abastecimiento.'),
    'fr':('Tarifs maritimes pour cette route : devis nécessaire. ','Faites une demande d’approvisionnement.'),
    'zh':('本航线海运费：需要询价。','提交采购需求。'),
    'hi':('इस मार्ग के समुद्री मालभाड़े के लिए मूल्य का अनुरोध आवश्यक है। ','खरीद का अनुरोध भेजें।'),
}

def owner_today():
    return datetime.now(ZoneInfo(CONFIG.get('timezone','America/Toronto'))).date()

def amount(value):
    number=Decimal(str(value))
    if not number.is_finite() or number<=0:
        raise ValueError('A rate must be a positive finite amount.')
    return number

def public_url(value,hosts):
    parsed=urlsplit(value or '')
    host=parsed.hostname or ''
    return parsed.scheme=='https' and not parsed.username and any(host==allowed or host.endswith('.'+allowed) for allowed in hosts)

def validate(data,today=None):
    today=today or owner_today()
    if data.get('schema_version')!=2:
        raise ValueError('Unsupported rate-file version.')
    if data.get('policy',{}).get('monthly_averages_allowed') is not False:
        raise ValueError('Monthly averages need a separate written Freightos approval review.')
    if data.get('observations') or data.get('dated_quotes'):
        raise ValueError('Publish one reviewed record, not an index history or private quote collection.')
    seen=set()
    for row in data['rates']:
        lane=data['lanes'].get(row.get('lane'))
        if not lane or row['lane'] in seen:
            raise ValueError('Unknown lane or duplicate reading for a lane.')
        seen.add(row['lane'])
        if not row.get('source_url') or not row.get('last_checked'):
            raise ValueError('Every record needs a source URL and check date.')
        values=[size for size in SIZES if row.get(size+'_usd') is not None]
        if not values:
            if row.get('kind')!='quote_required':
                raise ValueError('Missing figures must be labelled quote required.')
            continue
        for size in values:
            amount(row[size+'_usd'])
        if row.get('currency')!='USD':
            raise ValueError('Ocean-rate examples must identify USD.')
        if row.get('kind')=='weekly_index_reading':
            if row.get('source')!='freightos_fbx' or values!=['40ft'] or row.get('monthly_average'):
                raise ValueError('Only one direct 40ft FBX weekly reading is permitted; no Drewry, SCFI, ratios or averages.')
            expected=FBX_REGIONS.get(row.get('index_lane'))
            if not expected or (lane.get('origin_region'),lane.get('destination_region'))!=expected or lane.get('index_lane')!=row['index_lane']:
                raise ValueError('The FBX regional route does not match this guide.')
            if not public_url(row['source_url'],['freightos.com']) or row.get('attribution_url')!=TERMINAL:
                raise ValueError('FBX needs its primary reading source and a Freightos Terminal attribution link.')
            if row.get('reported_40ft_usd')!=row['40ft_usd']:
                raise ValueError('Quote the reported weekly value exactly; do not derive another number.')
            published=date.fromisoformat(row['publication_date'])
            reported=date.fromisoformat(row['reading_date'])
            if reported>published or published>today:
                raise ValueError('Reading and publication dates must be verified and not in the future.')
        elif row.get('kind')=='written_quote':
            if row.get('source')!='cargo_global_written_quote' or row.get('publication_approved') is not True or not row.get('quote_reference'):
                raise ValueError('A written quote needs its reference and explicit publication approval.')
            if not public_url(row['source_url'],['flashcargoglobal.com']) or date.fromisoformat(row['reading_date'])>today:
                raise ValueError('A written quote needs a dated public evidence summary without customer information.')
            if row.get('scope')!='port_to_port' or [row.get('origin_region'),row.get('destination_region')]!=[lane.get('origin_region'),lane.get('destination_region')] or not lane.get('origin_region') or not lane.get('destination_region'):
                raise ValueError('A written quote must match the route and stated service scope.')
        else:
            raise ValueError('Unapproved price basis. Monthly averages, Drewry and SCFI figures are not published.')
    for path,lane in data['page_lanes'].items():
        if not path.startswith('/') or lane not in data['lanes']:
            raise ValueError('Invalid guide-to-lane mapping.')
    return data

def load(today=None):
    return validate(json.loads(DATA_FILE.read_text(encoding='utf-8')),today)

def display_amount(value):
    if value is None:
        return 'Quote required'
    number=amount(value)
    return 'US$'+(format(number,',.0f') if number==number.to_integral_value() else format(number,',.2f'))

def render_table(data,lane_id,language='en',today=None):
    language=language.split('-')[0]
    row=next((entry for entry in data['rates'] if entry['lane']==lane_id),None)
    if row is None:
        raise ValueError('Missing rate record.')
    if all(row.get(size+'_usd') is None for size in SIZES):
        text,cta=FALLBACK_COPY.get(language,FALLBACK_COPY['en'])
        return '<p class="ocean-rates" data-ocean-rates data-rate-lane="'+escape(lane_id,quote=True)+'">'+escape(text)+'<a class="text-link" href="/contact/#buyer-request">'+escape(cta)+'</a></p>'
    if language!='en':
        raise ValueError('Numeric readings need reviewed localized attribution before a translated guide can show them.')
    lane=data['lanes'][lane_id]
    weekly=row['kind']=='weekly_index_reading'
    heading='One weekly ocean reading.' if weekly else 'A dated written quote.'
    caption='Index context only, not a delivered quote. Origin and destination charges, duty, tax, insurance and final delivery are not established by this reading.' if weekly else 'One written port-to-port quote for the stated scope, not an index or a monthly average. Final quote required.'
    label=('Weekly update dated ' if weekly else 'Written quote dated ')+row['reading_date']
    note='<p>Source: <a href="'+TERMINAL+'">Freightos Baltic Index (FBX)</a>. <a href="'+escape(row['source_url'],quote=True)+'">Read the publisher’s update</a>. Published <time datetime="'+row['publication_date']+'">'+row['publication_date']+'</time>. This is one reported weekly reading, not a monthly average or a Cargo Global price.</p>' if weekly else '<p>Source: <a href="'+escape(row['source_url'],quote=True)+'">Cargo Global written quote '+escape(row['quote_reference'])+'</a>. The quoted scope and date apply; it is not a current-rate promise.</p>'
    return '<section class="ocean-rates" data-ocean-rates data-rate-lane="'+escape(lane_id,quote=True)+'"><h2>'+heading+'</h2><p>'+escape(lane['label'])+'</p><div class="table-scroll"><table><caption>'+caption+'</caption><thead><tr><th scope="col">Reading</th><th scope="col">20ft container (USD)</th><th scope="col">40ft container (USD)</th></tr></thead><tbody><tr><th scope="row"><time datetime="'+row['reading_date']+'">'+escape(label)+'</time></th><td>'+display_amount(row.get('20ft_usd'))+'</td><td>'+display_amount(row.get('40ft_usd'))+'</td></tr></tbody></table></div>'+note+'<p class="small">Last checked: <time datetime="'+row['last_checked'][:10]+'">'+row['last_checked'][:10]+'</time>. Final quote required.</p><p><a class="text-link" href="/contact/#buyer-request">Start a sourcing request</a></p></section>'
