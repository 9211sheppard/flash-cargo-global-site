"""Validate one rate file and render evidence-backed monthly ocean tables."""

import calendar
import json
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / 'user_config.json'
CONFIG = json.loads(CONFIG_PATH.read_text(encoding='utf-8')) if CONFIG_PATH.exists() else {}
DATA_FILE = ROOT / CONFIG.get('ocean_rates_file', 'ocean-rates.json')
SIZES = ('20ft', '40ft')


def owner_today():
    return datetime.now(ZoneInfo(CONFIG.get('timezone', 'America/Toronto'))).date()


def round_usd(value):
    amount = Decimal(str(value))
    if not amount.is_finite() or amount <= 0:
        raise ValueError('A rate must be a positive finite USD amount.')
    return int((amount / 50).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 50)


def month_closed(month, today):
    year, number = map(int, month.split('-'))
    return date(year, number, calendar.monthrange(year, number)[1]) < today


def publication_dates(month, weekday):
    year, number = map(int, month.split('-'))
    return [date(year, number, day).isoformat() for day in range(1, calendar.monthrange(year, number)[1] + 1) if date(year, number, day).weekday() == weekday]


def monthly_average(observations, *, month, lane, size, source, expected_dates, today):
    if not month_closed(month, today) or not expected_dates:
        return None
    selected = {}
    for item in observations:
        if item.get('lane') != lane or item.get('size') != size or item.get('source') != source or not item.get('reading_date', '').startswith(month + '-'):
            continue
        if item['reading_date'] in selected:
            if selected[item['reading_date']]['usd'] != item['usd']:
                raise ValueError('Conflicting weekly readings require review.')
            continue
        selected[item['reading_date']] = item
    if set(selected) != set(expected_dates):
        return None
    return round_usd(sum(Decimal(str(row['usd'])) for row in selected.values()) / len(selected))


def validate(data, today=None):
    today = today or owner_today()
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported ocean-rate data version.')
    sources = data['sources']
    lanes = data['lanes']
    for key, source in sources.items():
        if urlsplit(source['source_url']).scheme != 'https' or not source.get('name'):
            raise ValueError(f'Invalid source: {key}')
    for reading in data.get('observations', []):
        source=sources.get(reading.get('source'),{})
        if not source.get('publication_allowed') or reading.get('size') not in source.get('lane_sizes',{}).get(reading.get('lane'),[]):
            raise ValueError('Restricted or unmatched observations cannot be published in the rate file.')
        if not reading.get('source_url') or not reading.get('date_pulled'):
            raise ValueError('Every weekly observation needs a source and capture date.')
        round_usd(reading['usd'])
    for quote in data.get('dated_quotes', []):
        source=sources.get(quote.get('source'),{})
        if not quote.get('publication_approved') or quote.get('scope')!='port_to_port' or not source.get('publication_allowed') or source.get('kind')!='dated_quote':
            raise ValueError('Unapproved quote details cannot be published in the public rate file.')
    seen = set()
    for row in data['rates']:
        identity = (row['lane'], row['month'])
        if identity in seen:
            raise ValueError('Duplicate lane/month record.')
        seen.add(identity)
        if row['lane'] not in lanes or not row.get('source_url') or not row.get('date_pulled'):
            raise ValueError('Missing rate provenance.')
        date.fromisoformat(row['month'] + '-01')
        for size in SIZES:
            value = row[size + '_usd']
            if value is None:
                continue
            if not month_closed(row['month'], today):
                raise ValueError('An open month cannot have a completed monthly average.')
            evidence = row.get('evidence', {}).get(size)
            if not evidence:
                raise ValueError('A numeric price needs size-specific evidence.')
            source = sources.get(evidence.get('source'))
            if not source or not source.get('publication_allowed') or size not in source['sizes'] or evidence.get('lane') != row['lane']:
                raise ValueError('An index cannot be converted to another size or lane.')
            lane = lanes[row['lane']]
            if evidence.get('kind') == 'dated_quote':
                if size != '20ft' or evidence.get('size')!='20ft' or evidence.get('currency')!='USD' or source.get('kind') != 'dated_quote' or not evidence.get('publication_approved') or not evidence.get('quote_date', '').startswith(row['month'] + '-'):
                    raise ValueError('A quote needs explicit publication approval, a date and the correct size.')
                date.fromisoformat(evidence['quote_date'])
                if not evidence.get('source_url') or value != round_usd(evidence['quoted_amount_usd']) or not lane.get('origin_region') or not lane.get('destination_region'):
                    raise ValueError('A dated quote must retain its evidence and shipment scope.')
                if [evidence.get('origin_region'),evidence.get('destination_region')] != [lane['origin_region'],lane['destination_region']]:
                    raise ValueError('The quote belongs to a different port region.')
                parsed=urlsplit(evidence['source_url'])
                if parsed.scheme!='https' or parsed.username or not any(parsed.hostname==allowed or (parsed.hostname or '').endswith('.'+allowed) for allowed in source['hosts']):
                    raise ValueError('The approved quote must cite its declared public evidence source.')
                continue
            mapping = source.get('lane_sizes', {}).get(lane.get('index_lane'))
            if not mapping or size not in mapping or not lane.get('origin_region') or not lane.get('destination_region'):
                raise ValueError('A numeric benchmark needs a reviewed port-region and index-lane match.')
            if source.get('lane_regions',{}).get(lane['index_lane']) != [lane['origin_region'],lane['destination_region']]:
                raise ValueError('The benchmark belongs to a different port region.')
            if evidence.get('kind') != 'weekly_index_average':
                raise ValueError('Quote publication needs a separately approved evidence path.')
            expected = publication_dates(row['month'], source['publication_weekday'])
            if evidence.get('expected_reading_dates') != expected:
                raise ValueError('The monthly series must account for every normal publication date.')
            observations = evidence.get('observations', [])
            for reading in observations:
                if not reading.get('source_url') or not reading.get('date_pulled') or not reading.get('reading_date'):
                    raise ValueError('A weekly reading is missing provenance.')
                host = urlsplit(reading['source_url']).hostname or ''
                if urlsplit(reading['source_url']).scheme!='https' or urlsplit(reading['source_url']).username or not any(host == allowed or host.endswith('.' + allowed) for allowed in source['hosts']):
                    raise ValueError('Weekly data must come from its declared primary source.')
            computed = monthly_average(observations, month=row['month'], lane=lane['index_lane'], size=size, source=evidence['source'], expected_dates=expected, today=today)
            if computed is None or value != computed:
                raise ValueError('Published amount does not match a complete rounded monthly average.')
    for path, lane in data['page_lanes'].items():
        if not path.startswith('/') or lane not in lanes:
            raise ValueError('Invalid page/lane mapping.')
    return data


def load(today=None):
    return validate(json.loads(DATA_FILE.read_text(encoding='utf-8')), today)


COPY = {
    'en': ('Approx. ocean freight', 'Month', '20ft container (USD)', '40ft container (USD)', 'Quote required', 'Approximate port-to-port ocean freight, monthly average. Excludes origin and destination charges, duty, tax, insurance and delivery.', 'Want an exact landed cost? Start a sourcing request', 'Final quote required.', 'Sources checked', 'Last checked', 'A matching full-month series is not verified. Ports and service scope must be confirmed.', 'The month has not closed; a completed monthly average is not available.'),
    'es': ('Flete marítimo aproximado', 'Mes', 'Contenedor de 20 pies (USD)', 'Contenedor de 40 pies (USD)', 'Cotización necesaria', 'Flete marítimo aproximado de puerto a puerto, promedio mensual. No incluye gastos de origen o destino, aranceles, impuestos, seguro ni entrega.', '¿Necesita el costo total exacto? Inicie una solicitud de abastecimiento', 'Se requiere cotización final.', 'Fuentes consultadas', 'Última consulta', 'No hay una serie mensual completa verificada para esta ruta. Deben confirmarse los puertos y el alcance.', 'El mes no ha terminado; todavía no hay un promedio mensual completo.'),
    'fr': ('Fret maritime indicatif', 'Mois', 'Conteneur de 20 pieds (USD)', 'Conteneur de 40 pieds (USD)', 'Devis nécessaire', 'Fret maritime indicatif de port à port, moyenne mensuelle. Hors frais d’origine et de destination, droits, taxes, assurance et livraison.', 'Besoin du coût total exact ? Faites une demande d’approvisionnement', 'Devis final nécessaire.', 'Sources consultées', 'Dernière consultation', 'Aucune série mensuelle complète correspondant à cette route n’est vérifiée. Les ports et le périmètre doivent être confirmés.', 'Le mois n’est pas terminé ; une moyenne mensuelle complète n’est pas disponible.'),
    'zh': ('海运费参考', '月份', '20英尺集装箱（美元）', '40英尺集装箱（美元）', '需要询价', '港到港海运费参考，按月平均。不含起运港和目的港费用、关税、税费、保险和送货费用。', '需要准确的到岸总成本？提交采购需求', '最终价格需要另行报价。', '已查阅来源', '最近查阅日期', '尚无经过核实且适用于本航线的完整月度数据。需要先确认港口和服务范围。', '本月尚未结束，暂不能提供完整月度平均值。'),
    'hi': ('समुद्री मालभाड़े का अनुमान', 'महीना', '20 फुट का कंटेनर (USD)', '40 फुट का कंटेनर (USD)', 'मूल्य के लिए अनुरोध करें', 'बंदरगाह से बंदरगाह तक समुद्री मालभाड़े का अनुमान, मासिक औसत। इसमें मूल और गंतव्य स्थान के शुल्क, सीमा शुल्क, कर, बीमा और अंतिम डिलीवरी शामिल नहीं हैं।', 'सटीक कुल लागत चाहिए? खरीद का अनुरोध भेजें', 'अंतिम मूल्य के लिए अलग से अनुरोध आवश्यक है।', 'देखे गए स्रोत', 'अंतिम जाँच', 'इस मार्ग के लिए पूरे महीने के सत्यापित आँकड़े उपलब्ध नहीं हैं। बंदरगाह और सेवा का दायरा तय करना आवश्यक है।', 'महीना अभी समाप्त नहीं हुआ है; पूरे महीने का औसत उपलब्ध नहीं है।'),
}

MONTH_NAMES = {
    'en': ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'),
    'es': ('ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'),
    'fr': ('janv.','févr.','mars','avr.','mai','juin','juil.','août','sept.','oct.','nov.','déc.'),
    'hi': ('जनवरी','फ़रवरी','मार्च','अप्रैल','मई','जून','जुलाई','अगस्त','सितंबर','अक्टूबर','नवंबर','दिसंबर'),
}

QUOTE_NOTE = {
    'en': '20ft figure: dated quote, not a monthly index average.',
    'es': 'Importe de 20 pies: cotización fechada, no un promedio mensual del índice.',
    'fr': 'Montant de 20 pieds : devis daté, et non moyenne mensuelle d’un indice.',
    'zh': '20英尺金额来自注明日期的报价，并非月度指数平均值。',
    'hi': '20 फुट की राशि दिनांकित प्रस्ताव से है, मासिक सूचकांक के औसत से नहीं।',
}


def month_label(month, language):
    year, number = map(int, month.split('-'))
    if language == 'zh':
        return f'{year}年{number}月'
    return MONTH_NAMES.get(language, MONTH_NAMES['en'])[number-1] + ' ' + str(year)


def render_table(data, lane_id, language='en', today=None):
    today = today or owner_today()
    language = language.split('-')[0]
    words = COPY.get(language, COPY['en'])
    heading, header_month, twenty_label, forty_label, quote_required, caption, cta, final_quote, sources_checked, last_checked, closed_reason, open_reason = words
    lane = data['lanes'][lane_id]
    label = lane.get('labels', {}).get(language, lane['label'])
    rows = sorted((row for row in data['rates'] if row['lane'] == lane_id), key=lambda row: row['month'])[-6:]
    if not rows:
        raise ValueError('Missing monthly rate rows.')
    body, notes = [], []
    for row in rows:
        prices = [quote_required if row[size + '_usd'] is None else '≈ US$' + format(row[size + '_usd'], ',') for size in SIZES]
        body.append('<tr><th scope="row"><time datetime="' + row['month'] + '">' + escape(month_label(row['month'], language)) + '</time></th>' + ''.join('<td>' + escape(price) + '</td>' for price in prices) + '</tr>')
        source_links = []
        for source_id in row['checked_sources']:
            source = data['sources'][source_id]
            source_links.append('<a href="' + escape(source['source_url'], quote=True) + '">' + escape(source['name']) + '</a>')
        reason = closed_reason if month_closed(row['month'], today) else open_reason
        if any(row[size + '_usd'] is not None for size in SIZES):
            reason = ''
        quote = row.get('evidence', {}).get('20ft', {})
        if quote.get('kind') == 'dated_quote':
            reason += ' ' + QUOTE_NOTE.get(language, QUOTE_NOTE['en']) + ' ' + quote['quote_date']
        notes.append('<p class="rate-source-note" data-rate-month="' + row['month'] + '"><strong>' + row['month'] + ':</strong> ' + escape(reason) + ' ' + escape(sources_checked) + ': ' + ' · '.join(source_links) + '. ' + escape(last_checked) + ': <time datetime="' + escape(row['date_pulled'][:10], quote=True) + '">' + escape(row['date_pulled'][:10]) + '</time>.</p>')
    return '<section class="ocean-rates" data-ocean-rates data-rate-lane="' + escape(lane_id, quote=True) + '"><h2>' + escape(heading) + '</h2><p class="rate-route">' + escape(label) + '</p><div class="table-scroll"><table><caption>' + escape(caption) + '</caption><thead><tr>' + ''.join('<th scope="col">' + escape(text) + '</th>' for text in (header_month, twenty_label, forty_label)) + '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div>' + ''.join(notes) + '<p class="small">' + escape(final_quote) + '</p><p><a class="text-link" href="/contact/#buyer-request">' + escape(cta) + '</a></p></section>'
