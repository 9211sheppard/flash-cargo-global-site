"""Build buyer-first audience paths without changing existing URL/title identities."""

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'audience-rollout'
BASE = 'https://flashcargoglobal.com'
ACTION = 'https://flash-cargo-form.old-sun-35f9.workers.dev/contact-request'
NAV = [('Source Products', '/sourcing/'), ('Guides', '/freight-research/'), ('For Suppliers', '/suppliers/'), ('Delivery', '/delivery/'), ('Contact', '/contact/')]
SOURCES = {
    'cbp': ('US importer responsibilities', 'https://www.help.cbp.gov/s/article/Article-1169?language=en_US'),
    'cbsa': ('Canadian duty and tax calculation', 'https://www.cbsa-asfc.gc.ca/import/guide-3-eng.html'),
    'fda': ('Food-facility registration and fees', 'https://www.fda.gov/food/guidance-regulation-food-and-dietary-supplements/questions-regarding-whether-food-facilities-are-required-pay-registration-fees-and-private'),
    'cfia': ('Canadian food-business licensing', 'https://inspection.canada.ca/en/food-licences/food-business-activities'),
}


def settings():
    return json.loads((ROOT / 'content' / 'audience-settings.json').read_text(encoding='utf-8'))


def header():
    links = ''.join(f'<a href="{href}"' + (' class="nav-request"' if title == 'Contact' else '') + f'>{title}</a>' for title, href in NAV)
    return '<header class="site-header"><nav class="site-nav" aria-label="Primary"><a class="wordmark" href="/"><span class="wordmark-flash">flash</span> <span class="wordmark-main">CARGO GLOBAL</span></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-menu" title="Open navigation"><span aria-hidden="true">&#9776;</span><span class="sr-only">Open navigation</span></button><div class="nav-menu" id="primary-menu">' + links + '</div></nav></header>'


def footer():
    return '<footer class="site-footer"><div><a class="footer-brand" href="/">CARGO GLOBAL</a><p>Serving buyers across the US, Canada and Mexico</p></div><nav aria-label="Footer"><a href="/sourcing/">Source products</a><a href="/freight-research/">Guides</a><a href="/suppliers/">For suppliers</a><a href="/delivery/">Delivery</a><a href="/contact/">Contact</a><a href="/terms/">Terms</a><a href="/privacy-policy/">Privacy</a></nav><p class="legal">&copy; 2026 Flash Cargo Global. All rights reserved.</p></footer>'


def field(label, name, required=False, kind='text', options=None, wide=False, hint='', maxlength=300, minimum='0.001'):
    attrs = f' name="{name}"' + (' required' if required else '')
    if options:
        control = '<select' + attrs + '>' + ''.join(f'<option value="{escape(value, quote=True)}">{escape(text)}</option>' for value, text in options) + '</select>'
    elif kind == 'textarea':
        control = f'<textarea{attrs} rows="4" maxlength="{maxlength}"></textarea>'
    else:
        numeric = f' min="{minimum}" step="any" inputmode="decimal"' if kind == 'number' else ''
        control = f'<input{attrs} type="{kind}" maxlength="{maxlength}"{numeric}>'
    return '<label' + (' class="wide"' if wide else '') + f'>{escape(label)}' + (f'<span class="field-note">{escape(hint)}</span>' if hint else '') + control + '</label>'


def form_open(audience, title):
    return f'<form class="contact-form" data-request-form data-audience="{audience}" method="post" action="{ACTION}" aria-label="{escape(title, quote=True)}"><input type="hidden" name="form_version" value="2"><input type="hidden" name="request_type" value="{audience}"><input type="hidden" name="form_started_at" value=""><input type="hidden" name="javascript_enabled" value="no"><label class="hidden-field" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>'


def private_reply():
    return field('Reply email (private)', 'email', True, 'email', wide=True, hint='Used to respond to this request. Not displayed publicly.', maxlength=254)


def form_close(button):
    return '<p class="field-note wide">We reply within one business day. A request is not an order or payment authorization. <a href="/privacy-policy/">Privacy</a></p><button class="button primary wide" type="submit">' + button + ' <span aria-hidden="true">&#8599;</span></button></form>'


def buyer_form():
    result = form_open('buyer_sourcing', 'Buyer sourcing request') + private_reply()
    result += field('Company (optional)', 'company_name', wide=True)
    result += '<fieldset class="sourcing-fields wide" data-sourcing-fields><legend>What would you like to source?</legend>'
    result += field('Product', 'product_name', True, wide=True, maxlength=160)
    result += field('Quantity', 'quantity', True, 'number')
    result += field('Unit', 'quantity_unit', True, options=[('pieces', 'Pieces'), ('cartons', 'Cartons'), ('kg', 'Kg'), ('tonnes', 'Tonnes')])
    result += field('Target price (optional)', 'target_price', kind='number')
    result += field('Price basis', 'price_basis', options=[('per_unit', 'Per unit'), ('total_order', 'Total order')])
    result += field('Currency', 'target_price_currency', options=[('USD', 'USD'), ('CAD', 'CAD')])
    result += field('Preferred supplier country (optional)', 'origin_preference', maxlength=100)
    result += field('Destination country', 'delivery_country', True, maxlength=100)
    result += field('Destination city', 'delivery_city', True, maxlength=120)
    result += field('Province or state (if applicable)', 'delivery_region', maxlength=100)
    result += field('Postal code (if applicable)', 'delivery_postal_code', maxlength=24)
    result += field('Timeline', 'timeline', True, wide=True, hint='Required date or a flexible time window.', maxlength=160)
    result += field('Specifications', 'product_specs', kind='textarea', wide=True, hint='Describe the requirements or provide a photo/specification link below.', maxlength=3000)
    result += field('Photo or specification link', 'spec_link', kind='url', wide=True, hint='A web link is enough; do not share confidential or unrelated files.', maxlength=600)
    return result + '</fieldset>' + form_close('Start a sourcing request')


def supplier_form():
    result = form_open('supplier_application', 'Supplier application') + private_reply()
    result += field('Company name', 'company_name', True)
    result += field('Country', 'supplier_country', True, maxlength=100)
    result += field('Products', 'supplier_products', True, 'textarea', wide=True, maxlength=2500)
    result += field('HS codes, if known', 'hs_codes', wide=True, maxlength=300)
    result += field('Minimum order quantity', 'minimum_order', True, maxlength=200, hint='Include the unit and whether mixed products are allowed.')
    result += field('Monthly capacity', 'monthly_capacity', True, maxlength=200, hint='State the product, quantity and unit; distinguish current spare capacity.')
    result += field('Certifications, registrations or conformity documents', 'certifications', True, 'textarea', wide=True, hint='Document, issuer, scope and expiry; say none where applicable. Registration is not product approval.', maxlength=2000)
    result += field('Current export markets', 'export_markets', True, wide=True, maxlength=600)
    result += field('Company website', 'company_website', True, 'url', wide=True, maxlength=600)
    result += field('Sample availability', 'sample_availability', True, options=[('', 'Select an option'), ('available', 'Available; terms to be agreed'), ('on_request', 'Available on request'), ('not_available', 'Not currently available')], wide=True)
    result += '<label class="check-label wide"><input type="checkbox" name="agree_vetting" value="yes" required><span>I agree to the review of my company and supporting documents before any buyer introduction.</span></label>'
    sitekey = settings().get('turnstile_sitekey')
    if sitekey:
        result += f'<div class="cf-turnstile wide" data-sitekey="{escape(sitekey, quote=True)}" data-action="supplier_application" data-size="flexible" data-theme="light"></div>'
    result += '<noscript><p class="field-note wide">Without browser scripting, you will review and confirm this application on the next page. It receives a separate manual verification before any introduction.</p></noscript>'
    return result + form_close('Apply as a supplier')


def delivery_form():
    result = form_open('delivery_only', 'Delivery-only request') + private_reply()
    result += field('Company (optional)', 'company_name', wide=True)
    result += field('Goods', 'product_name', True, wide=True, maxlength=160)
    result += field('Quantity and unit', 'delivery_quantity', True, maxlength=200)
    result += field('Packed dimensions and weight', 'packed_details', True, maxlength=600)
    result += field('Origin country and city', 'origin_location', True, maxlength=200)
    result += field('Destination country', 'delivery_country', True, maxlength=100)
    result += field('Destination city', 'delivery_city', True, maxlength=120)
    result += field('Province or state / postal code', 'delivery_region', maxlength=160)
    result += field('Timeline', 'timeline', True, maxlength=160)
    result += field('Delivery and handling requirements', 'delivery_requirements', True, 'textarea', wide=True, maxlength=3000)
    result += field('Photo or specification link (optional)', 'spec_link', kind='url', wide=True, maxlength=600)
    return result + form_close('Request delivery')


def request_section():
    return '<section class="section request-section" id="contact"><div class="section-intro"><p class="kicker">Start with the product</p><h2>What are you looking for?</h2><p>Share your requirements, target price and destination. We reply within one business day.</p></div>' + buyer_form() + '</section>'


def calculator():
    controls = field('Currency for every amount', 'comparison_currency', True, options=[('USD', 'USD'), ('CAD', 'CAD')])
    controls += field('Comparison quantity', 'comparison_quantity', True, 'number')
    labels = [
        ('Product cost', 'goods_cost'), ('Samples and inspection', 'samples_inspection'),
        ('Origin packing and handling', 'origin_packing'), ('Transport', 'transport_cost'),
        ('Insurance', 'insurance_cost'), ('Confirmed duty amount', 'duty_cost'),
        ('Confirmed tax amount', 'tax_cost'), ('Clearance services', 'clearance_cost'),
        ('Final delivery', 'final_delivery'), ('Other agreed costs', 'other_costs'),
    ]
    for label, name in labels:
        controls += field(label, name, True, 'number', minimum='0')
    return '<section class="section cost-tool" aria-labelledby="cost-tool-title" data-cost-calculator><h2 id="cost-tool-title">Your quoted costs.</h2><p>Use confirmed amounts in one currency. Enter zero only when a cost is confirmed as included elsewhere or not applicable. An unknown amount remains quote required.</p><fieldset class="cost-inputs"><legend class="sr-only">Quoted order costs</legend>' + controls + '</fieldset><div class="cost-actions"><button class="button primary" type="button" data-calculate>Calculate total <span aria-hidden="true">&#8599;</span></button><button class="cost-reset" type="button" data-reset-costs title="Clear quoted costs">Reset</button></div><output class="cost-result" data-cost-result aria-live="polite" aria-atomic="true">Quote required</output><noscript><p>The calculation needs browser scripting. You can still read the method and official example below, or send a <a href="/contact/#buyer-request">sourcing request</a>.</p></noscript></section>'


def supplier_cta(origin, language):
    countries = {
        'en': {'india': 'India', 'china': 'China', 'brazil': 'Brazil', 'italy': 'Italy', 'mexico': 'Mexico', 'turkey': 'Turkey', 'vietnam': 'Vietnam'},
        'es': {'india': 'India', 'china': 'China', 'brazil': 'Brasil', 'italy': 'Italia', 'mexico': 'México', 'turkey': 'Turquía', 'vietnam': 'Vietnam'},
        'fr': {'india': 'Inde', 'china': 'Chine', 'brazil': 'Brésil', 'italy': 'Italie', 'mexico': 'Mexique', 'turkey': 'Turquie', 'vietnam': 'Vietnam'},
        'zh': {'india': '印度', 'china': '中国', 'brazil': '巴西', 'italy': '意大利', 'mexico': '墨西哥', 'turkey': '土耳其', 'vietnam': '越南'},
        'hi': {'india': 'भारत', 'china': 'चीन', 'brazil': 'ब्राज़ील', 'italy': 'इटली', 'mexico': 'मेक्सिको', 'turkey': 'तुर्की', 'vietnam': 'वियतनाम'},
    }
    language = language if language in countries else 'en'
    name = countries[language][origin]
    text = {
        'en': (f'Manufacturer in {name}? ', 'Reach buyers in the USA, Canada and Mexico', '. Every supplier is reviewed before an introduction.'),
        'es': (f'¿Fabrica en {name}? ', 'Presente su empresa a compradores de Estados Unidos, Canadá y México', '. Revisamos a cada proveedor antes de una presentación.'),
        'fr': (f'Vous fabriquez en {name} ? ', 'Présentez votre entreprise aux acheteurs des États-Unis, du Canada et du Mexique', '. Chaque fournisseur est évalué avant une mise en relation.'),
        'zh': (f'您是在{name}生产的制造商吗？', '向美国、加拿大和墨西哥的买家介绍您的企业', '。每家供应商都须经过审核后才能获得引荐。'),
        'hi': (f'क्या आप {name} में निर्माता हैं? ', 'अमेरिका, कनाडा और मेक्सिको के खरीदारों के लिए अपनी कंपनी का परिचय दें', '। किसी खरीदार से परिचय कराने से पहले हर आपूर्तिकर्ता की समीक्षा की जाती है।'),
    }[language]
    return f'<p class="supplier-secondary">{escape(text[0])}<a href="/suppliers/">{escape(text[1])}</a>{escape(text[2])}</p>'


def schemas(page):
    article = {'@type': 'Article', 'headline': page['h1'], 'description': page['quick_answer'], 'publisher': {'@id': BASE + '/#organization'}, 'mainEntityOfPage': BASE + page['path'], 'citation': [SOURCES[key][1] for key in page['sources']]}
    faq = {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in page['faqs']]}
    how = {'@type': 'HowTo', 'name': page['process_title'], 'step': [{'@type': 'HowToStep', 'position': i, 'name': step[0], 'text': step[1]} for i, step in enumerate(page['steps'], 1)]}
    breadcrumbs = {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Cargo Global', 'item': BASE + '/'}, {'@type': 'ListItem', 'position': 2, 'name': page['h1'], 'item': BASE + page['path']}]}
    return [article, faq, how, breadcrumbs]


def render_page(page, document, day):
    main = f'<article class="audience-article" data-primary-audience="{page["audience"]}"><section class="page-intro"><p class="kicker">{page["kicker"]}</p><h1>{escape(page["h1"])}</h1><p class="quick-answer">{escape(page["quick_answer"])}</p><a class="button primary" href="{page["cta_url"]}">{page["cta"]} <span aria-hidden="true">&#8599;</span></a></section><div class="section editorial">'
    if page['path'] == '/landed-cost-calculator/':
        main = main.replace('<div class="section editorial">', calculator() + '<div class="section editorial">')
    if page['path'] == '/sourcing/':
        main += '<p><a href="/landed-cost-calculator/">Compare confirmed order costs</a> before approving a purchase.</p>'
    for heading, paragraphs in page['sections']:
        anchor = ' id="' + re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-') + '"'
        main += f'<section{anchor}><h2>{escape(heading)}</h2>' + ''.join(f'<p>{escape(p)}</p>' for p in paragraphs) + '</section>'
    main += '<section><h2>' + escape(page['process_title']) + '</h2><ol class="editorial-steps">' + ''.join(f'<li><h3>{escape(title)}</h3><p>{escape(text)}</p></li>' for title, text in page['steps']) + '</ol></section>'
    main += '<section><h2>Official checks before an order</h2><div class="table-scroll"><table class="facts-table"><caption>Product-specific obligations must be checked for the actual order.</caption><thead><tr><th scope="col">Check</th><th scope="col">What the official source establishes</th><th scope="col">Source / last checked</th></tr></thead><tbody>'
    for fact, detail, key in page['facts']:
        title, url = SOURCES[key]
        main += f'<tr><th scope="row">{escape(fact)}</th><td>{escape(detail)}</td><td><a href="{escape(url, quote=True)}">{escape(title)}</a><br><time datetime="{day}">{day}</time></td></tr>'
    main += '</tbody></table></div></section><section><h2>Questions before you begin</h2><div class="faq-list">' + ''.join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in page['faqs']) + '</div></section>'
    main += f'<p><a class="button primary" href="{page["cta_url"]}">{page["cta"]} <span aria-hidden="true">&#8599;</span></a></p></div></article>'
    if page['audience'] == 'supplier':
        main += '<section class="section request-section" id="supplier-application"><div class="section-intro"><p class="kicker">For manufacturers</p><h2>Present your capability.</h2><p>Every supplier is reviewed before any buyer introduction. Applications stay private; there is no public supplier directory.</p></div>' + supplier_form() + '</section>'
    soup = BeautifulSoup(document(page['title'], page['path'], main, extra_schema=schemas(page)), 'html.parser')
    for meta in soup.select('meta[name="description"], meta[property="og:description"]'):
        meta['content'] = page['description']
    if page['path'] == '/landed-cost-calculator/':
        soup.head.append(soup.new_tag('script', type='module', src='/calculator.mjs'))
    if page['audience'] == 'supplier' and settings().get('turnstile_sitekey'):
        script = soup.new_tag('script', src='https://challenges.cloudflare.com/turnstile/v0/api.js', attrs={'async': '', 'defer': ''})
        soup.head.append(script)
    return soup


def apply_rollout():
    from build_cargo_global import document, pages, route, write
    from audience_page_content import AUDIENCE_PAGES

    OUT.mkdir(parents=True, exist_ok=True)
    baseline = {row['path']: row for row in json.loads((ROOT / 'content' / 'audience-baseline.json').read_text(encoding='utf-8'))}
    now = datetime.now(timezone.utc).isoformat()
    day = now[:10]
    for page in AUDIENCE_PAGES:
        write(page['path'].strip('/') + '/index.html', str(render_page(page, document, day)))
    home_path = ROOT / 'index.html'
    home = BeautifulSoup(home_path.read_text(encoding='utf-8'), 'html.parser')
    hero = home.select_one('.hero-media')
    hero['srcset'] = '/assets/sourcing-assortment-480.webp 480w, /assets/sourcing-assortment-768.webp 768w, /assets/sourcing-assortment.webp 1536w'
    hero['sizes'] = '100vw'
    cards = '<section class="section audience-paths" aria-label="Choose your next step"><a class="audience-card audience-buyer" href="/contact/#buyer-request"><span class="kicker">For buyers</span><h2>I\'m buying</h2><p>Find the product, compare suppliers and approve an itemized plan.</p><span class="text-link">Start a sourcing request &#8599;</span></a><a class="audience-card" href="/suppliers/"><span class="kicker">For manufacturers</span><h2>I\'m a manufacturer</h2><p>Present your capability for review before a buyer introduction.</p><span class="text-link">For suppliers &#8599;</span></a><a class="audience-card" href="/delivery/"><span class="kicker">For delivery</span><h2>I need it delivered</h2><p>Air, ocean and truck are the final steps in the buying plan.</p><span class="text-link">Delivery handled &#8599;</span></a></section>'
    home.select_one('.region-band').insert_after(BeautifulSoup(cards, 'html.parser'))
    featured = '<section class="section featured-guides"><div class="section-heading"><p class="kicker">Before you buy</p><h2>A better-prepared order.</h2><p>Supplier-country checklists to support specifications, samples and quality decisions.</p></div><div class="wide-grid">' + ''.join(f'<article><h3><a href="{url}">{title}</a></h3><p>{text}</p></article>' for title, text, url in [
        ('Apparel from India', 'Prepare fabric, sizing, labels, samples and your purchase-order brief.', '/freight-research/en/india-apparel-manufacturer-export-to-north-america/'),
        ('Electronics from China', 'Review specifications, battery details, test records and supplier documents.', '/freight-research/en/china-electronics-battery-goods-to-canada/'),
        ('Product sourcing in five languages', 'Choose the language and supplier-country checklist for your preparation.', '/freight-research/'),
    ]) + '</div></section>'
    home.select_one('#faq').insert_before(BeautifulSoup(featured, 'html.parser'))
    home.select_one('#contact').replace_with(BeautifulSoup(request_section(), 'html.parser'))
    write('index.html', str(home))
    contact = '<section class="page-intro"><p class="kicker">For buyers</p><h1>Let’s find what you need.</h1><p>Serving buyers across the US, Canada and Mexico.</p></section><nav class="request-switch" aria-label="Request type"><a href="#buyer-request">Product sourcing</a><a href="#delivery-request">Delivery only</a></nav><section class="section request-section" id="buyer-request"><div class="section-intro"><p class="kicker">Source products</p><h2>Start with your requirements.</h2><p>A considered shortlist, clear approvals and personal coordination through delivery.</p></div>' + buyer_form() + '</section><section class="section request-section" id="delivery-request"><div class="section-intro"><p class="kicker">Delivery only</p><h2>Your goods. The final step.</h2><p>Share the origin, packed goods and destination. Delivery details and quote inclusions are agreed before booking.</p></div>' + delivery_form() + '</section>'
    write('contact/index.html', document('Let’s find what you need.', '/contact/', contact))
    receipt = '<section class="page-intro"><p class="kicker">Request received</p><h1>Received.</h1><p>We reply within one business day.</p><a class="button primary" href="/">Back to Cargo Global</a></section>'
    write('thank-you.html', document('Request Received', '/thank-you.html', receipt, noindex=True))
    proposals = []
    for path in pages():
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        current = route(path)
        parts = current.strip('/').split('/')
        if parts[0] in ('guides', 'freight-research') and len(parts) <= 2:
            soup.main['class'] = list(dict.fromkeys(soup.main.get('class', []) + ['guide-hub']))
            for heading in soup.select('.knowledge-grid article > h3, .wide-grid article > h3'):
                heading.name = 'h2'
        if soup.select_one('header.site-header'):
            soup.select_one('header.site-header').replace_with(BeautifulSoup(header(), 'html.parser'))
        if soup.footer:
            soup.footer.replace_with(BeautifulSoup(footer(), 'html.parser'))
        old = baseline.get(current)
        if old:
            soup.title.string = old['title']
            for meta in soup.select('meta[property="og:title"], meta[name="twitter:title"]'):
                meta['content'] = old['title']
            if len(old['title']) >= 60:
                proposals.append({'path': current, 'current_title': old['title'], 'status': 'awaiting_search_console_review', 'reason': 'Over 59 characters; preserve until impression evidence and a complete shorter wording are reviewed.', 'source_url': BASE + current, 'last_checked': now})
        for meta in soup.select('meta[http-equiv="Content-Security-Policy"]'):
            policy = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; connect-src 'self' https://challenges.cloudflare.com; form-action 'self' https://flash-cargo-form.old-sun-35f9.workers.dev; base-uri 'self'; object-src 'none'"
            meta['content'] = policy
        for script in soup.select('script[src*="cargo-global.js"]'):
            script['src'] = '/cargo-global.js?v=2'
        for css in soup.select('link[rel="stylesheet"]'):
            css['href'] = '/cargo-global.css?v=2'
        for note in list(soup.select('.service-note')):
            note.decompose()
        if not soup.select_one('noscript[data-navigation-fallback]'):
            fallback = soup.new_tag('noscript', attrs={'data-navigation-fallback': ''})
            fallback.append(BeautifulSoup('<style>@media(max-width:800px){.menu-toggle{display:none}.site-nav{align-items:flex-start;flex-wrap:wrap}.nav-menu{display:flex;position:static;border:0;padding:0;flex-direction:row;flex-wrap:wrap;gap:0 20px}.nav-menu a{font-size:14px;padding:8px 0}}</style>', 'html.parser'))
            soup.head.append(fallback)
        if current.startswith('/freight-research/') and '/index.html' not in current and len(current.strip('/').split('/')) >= 2:
            article = soup.select_one('article.guide-article')
            if article and not article.select_one('.supplier-secondary'):
                parts = current.strip('/').split('/')
                slug = parts[-1]
                origin = next((name for code, name in [('india', 'India'), ('china', 'China'), ('brazil', 'Brazil'), ('italy', 'Italy'), ('mexico', 'Mexico'), ('turkey', 'Turkey'), ('vietnam', 'Vietnam')] if slug.startswith(code)), None)
                if origin:
                    article.append(BeautifulSoup(supplier_cta(slug.split('-')[0], soup.html.get('lang', 'en').split('-')[0]), 'html.parser'))
        path.write_text(str(soup), encoding='utf-8', newline='\n')
    privacy = ROOT / 'privacy-policy' / 'index.html'
    soup = BeautifulSoup(privacy.read_text(encoding='utf-8'), 'html.parser')
    first_heading = soup.select_one('article h2')
    if first_heading:
        paragraph = first_heading.find_next_sibling('p')
        paragraph.string = 'Buyer and delivery requests include product requirements, quantities, budget, destination, timeline and a private reply email. Supplier applications include company capability, production country, minimum orders, capacity, documents, export markets, website and sample availability. Personal names and phone numbers are not requested. Submitted information is not published in a public supplier directory. Do not submit payment-card details, passwords, identity documents or unrelated confidential material.'
    article = soup.select_one('article')
    article.append(BeautifulSoup('<h2>Supplier verification and spam protection</h2><p>Supplier forms use Cloudflare Turnstile where browser scripting is available. A verification token is checked by the request handler before a normal supplier submission is accepted. Applications submitted through the no-scripting review path are marked for separate manual verification before any introduction. A timer and a hidden spam-detection field also help protect request handling.</p><p>For the no-scripting review step, a short-lived verification record is kept for up to 30 minutes. It stores a digest of the form values and review timing rather than a public enquiry listing. Request information remains private and is used to review the enquiry and respond through the reply email.</p><h2>Private enquiry notifications</h2><p>Enquiry details can be sent to our internal Microsoft 365 mailbox so that we can review and respond to your request. Cloudflare processes the form and Microsoft processes the internal notification. Your reply address is used for the enquiry, not displayed publicly or added to a public supplier directory. If notification delivery needs another attempt, the saved request remains private while that attempt is made.</p>', 'html.parser'))
    privacy.write_text(str(soup), encoding='utf-8', newline='\n')
    # Metadata for support pages must describe their own purpose, not repeat the homepage.
    descriptions = {
        '/': 'Source products through Cargo Global: compare suppliers, arrange samples and quality checks, and coordinate delivery across the US, Canada and Mexico.',
        '/contact/': 'Send a private sourcing or delivery request with product requirements, quantity, destination, timeline and a reply address.',
        '/about/': 'Learn how Cargo Global coordinates supplier selection, product specifications, samples, quality checks and delivery for North American buyers.',
        '/privacy-policy/': 'How Cargo Global handles private buyer requests and supplier applications, including reply details, request storage and spam protection.',
        '/terms/': 'Read the website and enquiry terms for supplier review, order approval, pricing, inspections, payment stages and delivery coordination.',
        '/thank-you.html': 'Your Cargo Global request has been received. We reply within one business day.',
        '/404.html': 'Find the Cargo Global sourcing page, supplier application, delivery information or online contact form.',
    }
    seen = set()
    for path in pages():
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        current = route(path)
        meta = soup.select_one('meta[name="description"]')
        desc = descriptions.get(current, meta['content'] if meta else '')
        if desc in seen:
            heading = soup.h1.get_text(' ', strip=True)
            desc = f'{heading}: practical product, supplier and order preparation from Cargo Global.'
        seen.add(desc)
        for tag in soup.select('meta[name="description"], meta[property="og:description"], meta[name="twitter:description"]'):
            tag['content'] = desc
        path.write_text(str(soup), encoding='utf-8', newline='\n')
    with (OUT / 'title-review-required.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['path', 'current_title', 'status', 'reason', 'source_url', 'last_checked'])
        writer.writeheader()
        writer.writerows(proposals)
    (OUT / 'build-status.json').write_text(json.dumps({
        'last_checked': now, 'source_url': BASE + '/',
        'website_release': 'staged_not_deployed',
        'turnstile_configured': bool(settings().get('turnstile_sitekey')),
        'titles_preserved': len(baseline), 'title_review_required': len(proposals),
        'new_guides_published': 0, 'indexing_review_required_before_next_guide_batch': True,
        'release_blockers': ([] if settings().get('turnstile_sitekey') else ['Supplier Turnstile key approval/configuration and live challenge test']) + ([] if settings().get('notification_delivery_verified') else ['Microsoft send-mail connection approval and inbox delivery verification']),
        'search_console': 'deferred_by_owner' if settings().get('search_console_deferred_by_owner') else 'awaiting_sign_in',
        'unfinished_checks': ['Search Console impressions and indexing', 'Post-release Lighthouse regression check'],
    }, indent=2), encoding='utf-8')


def split_sitemaps():
    from build_cargo_global import pages, route, write
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', namespace)
    day = datetime.now(timezone.utc).date().isoformat()
    groups = {name: ET.Element(f'{{{namespace}}}urlset') for name in ('buyers', 'suppliers', 'delivery')}
    urls = []
    for path in pages():
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        current = route(path)
        robots = soup.select_one('meta[name="robots"]')
        canonical = soup.select_one('link[rel="canonical"]')
        if not robots or 'noindex' in robots['content'] or not canonical or canonical['href'] != BASE + current:
            continue
        group = 'suppliers' if current.startswith('/suppliers/') else 'delivery' if current.startswith('/delivery/') else 'buyers'
        row = ET.SubElement(groups[group], f'{{{namespace}}}url')
        ET.SubElement(row, f'{{{namespace}}}loc').text = BASE + current
        ET.SubElement(row, f'{{{namespace}}}lastmod').text = day
        urls.append({'audience': group, 'path': current, 'source_url': BASE + current, 'last_checked': day})
    index = ET.Element(f'{{{namespace}}}sitemapindex')
    for name, tree in groups.items():
        ET.indent(tree)
        write(f'sitemap-{name}.xml', '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(tree, encoding='unicode'))
        node = ET.SubElement(index, f'{{{namespace}}}sitemap')
        ET.SubElement(node, f'{{{namespace}}}loc').text = BASE + f'/sitemap-{name}.xml'
        ET.SubElement(node, f'{{{namespace}}}lastmod').text = day
    ET.indent(index)
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(index, encoding='unicode'))
    write('llms.txt', '# Cargo Global\n\nGlobal product sourcing for buyers across the US, Canada and Mexico. Supplier participation is reviewed privately; delivery is the final step of a sourcing order.\n\n## Buyers first\n- [Source products](https://flashcargoglobal.com/sourcing/): Product briefs, supplier vetting, samples, quality checks and purchase approval.\n- [Sourcing guides](https://flashcargoglobal.com/freight-research/): Product and supplier-country preparation in five languages.\n- [Buyer request](https://flashcargoglobal.com/contact/#buyer-request): Share product requirements and a private reply address.\n\n## Suppliers second\n- [For suppliers](https://flashcargoglobal.com/suppliers/): Private manufacturer applications, capability review and vetting before introductions.\n\n## Delivery third\n- [Delivery](https://flashcargoglobal.com/delivery/): Air, full or shared ocean containers, customs coordination and final delivery.\n- [Delivery-only request](https://flashcargoglobal.com/contact/#delivery-request): Goods already sourced; request the delivery step only.\n\n## Company information\n- [About](https://flashcargoglobal.com/about/): The Cargo Global sourcing approach.\n- [Privacy](https://flashcargoglobal.com/privacy-policy/): Private request handling and spam protection.\n- [Terms](https://flashcargoglobal.com/terms/): Enquiries, quotes and order approvals.\n\nLast checked: ' + day + '\nSource: ' + BASE + '/\n')
    machine_file = ROOT / 'llms.txt'
    machine_file.write_text(machine_file.read_text(encoding='utf-8').replace('## Suppliers second', '- [Order-cost worksheet](https://flashcargoglobal.com/landed-cost-calculator/): Compare confirmed component amounts in one currency; unknown charges remain quote required.\n\n## Suppliers second'), encoding='utf-8')
    with (OUT / 'batch-urls.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['audience', 'path', 'source_url', 'last_checked'])
        writer.writeheader()
        writer.writerows(row for row in urls if row['path'] in ('/', '/sourcing/', '/suppliers/', '/delivery/', '/contact/', '/landed-cost-calculator/'))
