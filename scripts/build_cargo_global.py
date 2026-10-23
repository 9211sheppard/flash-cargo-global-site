"""Build the sourcing-first pages and reconcile the existing static library."""

import copy
import csv
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://flashcargoglobal.com'
STAMP = datetime.now(timezone.utc).isoformat()
DAY = STAMP[:10]
OUT = ROOT / 'output' / 'cargo-global-reposition'
OUT.mkdir(parents=True, exist_ok=True)
REGION = 'Serving buyers across the US, Canada and Mexico'
DESCRIPTION = 'Global product sourcing, supplier shortlists, quality checks and door-to-door delivery for buyers across the US, Canada and Mexico.'
FORM_ACTION = 'https://flash-cargo-form.old-sun-35f9.workers.dev/contact-request'
POLICY = "default-src 'self'; img-src 'self' https://static.wixstatic.com data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; form-action 'self' https://flash-cargo-form.old-sun-35f9.workers.dev https://flash-cargo-global.old-sun-35f9.workers.dev; base-uri 'self'; object-src 'none'"
MERGES = {
    '/freight-research/india-apparel-manufacturer-export-to-north-america/': '/freight-research/en/india-apparel-manufacturer-export-to-north-america/',
    '/freight-research/china-electronics-supplier-export-to-canada/': '/freight-research/en/china-electronics-battery-goods-to-canada/',
    '/freight-research/mexico-automotive-parts-to-us-production-shipment/': '/freight-research/en/mexico-automotive-parts-to-us-production/',
    '/freight-research/italy-clothing-manufacturer-export-to-japan/': '/freight-research/en/italy-fashion-samples-to-japan/',
}
SOURCE_REPLACEMENTS = {
    'https://www.abf.gov.au/importing-exporting-and-manufacturing/importing-goods': 'https://www.abf.gov.au/importing-exporting-and-manufacturing/importing/how-to-import/overview',
    'https://www.customs.go.jp/english/c-answer_e/c-answer_e.htm': 'https://www.customs.go.jp/english/c-answer_e/customsanswer_e.htm',
    'https://www.ftc.gov/business-guidance/resources/threading-your-way-through-labeling-requirements-under-textile-wool-acts': 'https://www.ftc.gov/news-events/topics/tools-consumers/apparel-labeling',
}
LOCALES = {
    'en': ('Sourcing guides', 'Supplier preparation and product checklists for buyers comparing specifications, samples, quality requirements and delivery to North America.', 'Sourcing for North America', 'Use this checklist while comparing suppliers, agreeing specifications and planning quality checks. Cargo Global sources products worldwide for buyers across the US, Canada and Mexico.', 'Start a sourcing request'),
    'es': ('Guías de abastecimiento', 'Listas de preparación de proveedores y productos para comparar especificaciones, muestras, calidad y entrega en Norteamérica.', 'Abastecimiento para Norteamérica', 'Utilice esta lista al comparar proveedores, acordar especificaciones y planificar controles de calidad. Cargo Global busca productos en todo el mundo para compradores de Estados Unidos, Canadá y México.', 'Iniciar una solicitud'),
    'fr': ("Guides d’approvisionnement", 'Des listes de préparation pour comparer les fournisseurs, les spécifications, les échantillons, la qualité et la livraison en Amérique du Nord.', "Approvisionnement pour l’Amérique du Nord", 'Utilisez cette liste pour comparer les fournisseurs, définir les spécifications et préparer les contrôles de qualité. Cargo Global recherche des produits dans le monde entier pour les acheteurs aux États-Unis, au Canada et au Mexique.', 'Faire une demande'),
    'zh': ('采购指南', '比较供应商、产品规格、样品、质量要求及北美交付安排的实用清单。', '面向北美买家的采购', '请在比较供应商、确认产品规格和安排质量检查时使用本清单。Cargo Global 为美国、加拿大和墨西哥的买家在全球寻找产品并协调交付。', '提交采购需求'),
    'hi': ('वैश्विक खरीद और आपूर्तिकर्ता मार्गदर्शिकाएँ', 'आपूर्तिकर्ताओं, उत्पाद की विशिष्टताओं, नमूनों, गुणवत्ता जाँच और उत्तरी अमेरिका में डिलीवरी की तुलना के लिए व्यावहारिक जाँच-सूचियाँ।', 'उत्तरी अमेरिका के खरीदारों के लिए खरीद', 'आपूर्तिकर्ताओं की तुलना, उत्पाद की विशिष्टताएँ तय करने और गुणवत्ता जाँच की योजना बनाते समय इस सूची का उपयोग करें। Cargo Global अमेरिका, कनाडा और मेक्सिको के खरीदारों के लिए दुनिया भर से उत्पाद प्राप्त करने और डिलीवरी की व्यवस्था करता है।', 'खरीद अनुरोध शुरू करें'),
}
HUB_LABELS = {
    'guides': {'en': 'Product sourcing guides', 'es': 'Guías de productos y proveedores', 'fr': 'Guides de produits et fournisseurs', 'zh': '产品与供应商指南', 'hi': 'उत्पाद और आपूर्तिकर्ता मार्गदर्शिकाएँ'},
    'freight-research': {'en': 'Supplier-country checklists', 'es': 'Listas de proveedores por país', 'fr': 'Listes de préparation par pays fournisseur', 'zh': '供应国采购清单', 'hi': 'देशवार खरीद और आपूर्तिकर्ता जाँच-सूचियाँ'},
}
FAQS = [
    ('Is there a minimum order?', 'Minimum quantities depend on the product and supplier. Tell us the quantity you have in mind; we confirm supplier minimums, sample options and any tooling or setup costs before you decide.'),
    ('How does payment work?', 'You review the supplier option and an itemized quote before approving a purchase. The quote sets out the currency, payment stages, inclusions and exclusions. Sample, inspection and production costs are confirmed separately where applicable; a request does not place an order.'),
    ('How do you check quality?', 'We agree the specifications and acceptance criteria with you, arrange samples when required, and facilitate an independent pre-shipment inspection where agreed. Factory and sample photos support your review before purchase approval. Inspection scope and any limits are confirmed in writing.'),
    ('How long does delivery take?', 'Timing depends on supplier availability, production, samples, inspection, transport and customs clearance. We confirm a proposed schedule with your quote and keep you updated until delivery. Supplier-shortlist timing is confirmed after reviewing your requirements.'),
    ('Which countries do you buy from?', 'We work through a global supplier network and shortlist options based on the product, specifications, quality requirements and delivery destination. We serve buyers across the US, Canada and Mexico. Availability and applicable import requirements are checked before an order is approved.'),
]
CATEGORIES = [
    ('Industrial parts', 'Dimensions, materials and fit, agreed before production.', '/industries/machinery-industrial-parts-freight/'),
    ('Packaging', 'Materials, print, pack size and a sample you can review.', '/sourcing/#packaging'),
    ('Furniture and fixtures', 'Finishes, measurements and delivery access planned together.', '/industries/furniture-fixtures-white-glove-freight/'),
    ('Apparel and textiles', 'Fabric, sizing, labels and approved samples.', '/guides/en/apparel-textile-export-checklist/'),
    ('Electronics', 'Specifications, test records and product requirements.', '/guides/en/electronics-export-checklist/'),
    ('Food ingredients', 'Composition, documentation and handling requirements.', '/industries/agriculture-food-ingredient-freight/'),
    ('Building materials', 'Grades, finishes, quantities and project requirements.', '/sourcing/#building-materials'),
    ('Anything else, just ask', 'Bring the brief. We will review what is possible.', '/contact/?inquiry=sourcing'),
]


def pages():
    return sorted(p for p in ROOT.rglob('*.html') if p.relative_to(ROOT).parts[0] not in ('output', 'content'))


def route(path):
    value = path.relative_to(ROOT).as_posix()
    return '/' + value[:-10] if value.endswith('index.html') else '/' + value


def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8', newline='\n')


def fragment(text):
    return BeautifulSoup(text, 'html.parser')


def header():
    return '''<header class="site-header"><nav class="site-nav" aria-label="Primary">
<a class="wordmark" href="/" aria-label="Cargo Global home"><span class="wordmark-flash">flash</span><span class="wordmark-main">CARGO GLOBAL</span></a>
<button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-menu" title="Open navigation"><span aria-hidden="true">&#9776;</span><span class="sr-only">Open navigation</span></button>
<div class="nav-menu" id="primary-menu"><a href="/#how-it-works">How It Works</a><a href="/#what-we-source">What We Source</a><a href="/#delivery">Delivery</a><a href="/#faq">FAQ</a><a class="nav-request" href="/contact/?inquiry=sourcing">Start a Request <span aria-hidden="true">&#8599;</span></a></div>
</nav></header>'''


def footer():
    return '''<footer class="site-footer"><div><a class="footer-brand" href="/">CARGO GLOBAL</a><p>Serving buyers across the US, Canada and Mexico</p></div>
<nav aria-label="Footer"><a href="/about/">About Cargo Global</a><a href="/freight-research/">Sourcing guides</a><a href="/contact/">Start a Request</a><a href="/terms/">Terms</a><a href="/privacy-policy/">Privacy</a></nav>
<p class="legal">&copy; 2026 Flash Cargo Global. All rights reserved.</p></footer>'''


def organization():
    return {'@type': 'Organization', '@id': BASE + '/#organization', 'name': 'Cargo Global', 'legalName': 'Flash Cargo Global', 'url': BASE + '/', 'description': DESCRIPTION, 'areaServed': ['US', 'CA', 'MX'], 'contactPoint': {'@type': 'ContactPoint', 'contactType': 'Product sourcing request', 'url': BASE + '/contact/'}, 'knowsAbout': ['Product sourcing', 'Supplier shortlisting', 'Product specifications', 'Samples', 'Pre-shipment inspection', 'Door-to-door delivery']}


def document(title, path, main, noindex=False, extra_schema=None, body_class=''):
    full_title = title if title.startswith('Cargo Global |') else f'Cargo Global | {title}'
    schema = {'@context': 'https://schema.org', '@graph': [organization(), {'@type': 'WebPage', 'name': full_title, 'url': BASE + path, 'about': {'@id': BASE + '/#organization'}}] + (extra_schema or [])}
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(full_title)}</title><meta name="description" content="{escape(DESCRIPTION)}"><meta name="robots" content="{'noindex, follow' if noindex else 'index, follow'}"><link rel="canonical" href="{BASE + path}">
<meta property="og:site_name" content="Cargo Global"><meta property="og:type" content="website"><meta property="og:title" content="{escape(full_title)}"><meta property="og:description" content="{escape(DESCRIPTION)}"><meta property="og:url" content="{BASE + path}"><meta property="og:image" content="{BASE}/assets/sourcing-assortment.jpg"><meta name="twitter:card" content="summary_large_image">
<meta name="referrer" content="strict-origin-when-cross-origin"><meta http-equiv="Content-Security-Policy" content="{POLICY}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/cargo-global.css?v=1"><script src="/cargo-global.js?v=1" defer></script><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script></head>
<body class="{body_class}"><a class="skip-link" href="#main">Skip to main content</a>{header()}<main id="main">{main}</main>{footer()}</body></html>'''


def faq_markup():
    return ''.join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in FAQS)


def interim_form():
    path = ROOT / 'content' / 'interim-inquiry-form.html'
    if path.exists():
        soup = fragment(path.read_text(encoding='utf-8'))
    else:
        soup = BeautifulSoup((ROOT / 'index.html').read_text(encoding='utf-8-sig'), 'html.parser')
        form = soup.select_one('[data-inquiry-form]')
        if not form:
            raise RuntimeError('No existing intake form found; refusing to replace it with an unconnected form.')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(form), encoding='utf-8')
        soup = fragment(str(form))
    form = soup.form
    form['aria-describedby'] = 'request-service-note'
    for el in list(form.find_all(['h3', 'p'], recursive=False)):
        el.decompose()
    form.select_one('[name="full_name"]').attrs.pop('placeholder', None)
    form.select_one('.hidden-field')['aria-hidden'] = 'true'
    choices = form.select_one('.inquiry-kind')
    sourcing_label = choices.select_one('[value="sourcing"]').parent
    freight_label = choices.select_one('[value="freight"]').parent
    freight_label.insert_before(sourcing_label.extract())
    for el in form.select('button[type="submit"]'):
        el.string = 'Submit Request'
    for el in form.select('[name="quantity_unit"] option'):
        el.string = el.get_text().capitalize()
    # Existing private reply fields are retained until the owner chooses their replacement.
    form.select_one('[name="inquiry_type"][value="freight"]').attrs.pop('checked', None)
    form.select_one('[name="inquiry_type"][value="sourcing"]')['checked'] = ''
    if not form.select_one('[name="target_price_currency"] option'):
        existing = form.select_one('[name="target_price_currency"]')
        existing.replace_with(fragment('<label>Currency<select name="target_price_currency"><option value="USD">USD</option><option value="CAD">CAD</option></select></label>'))
        price = form.select_one('[name="target_price"]')
        if price:
            price.parent.contents[0].replace_with('Target price ')
    if not form.select_one('[name="delivery_region"]'):
        country = form.select_one('[name="delivery_country"]').parent
        country.insert_before(fragment('<label>Province or state<input name="delivery_region" maxlength="100" autocomplete="address-level1" required></label>'))
    form.select_one('[name="product_specs"]')['maxlength'] = '1400'
    form.select_one('[name="spec_link"]')['maxlength'] = '500'
    path.write_text(str(form), encoding='utf-8', newline='\n')
    return str(form)


def build_primary_pages():
    existing_form = interim_form()
    request_section = f'''<section class="section request-section" id="contact"><div class="section-intro"><p class="kicker">Start a request</p><h2>What are you looking for?</h2><p>Share the product, quantity, specifications and delivery destination. We reply within one business day.</p><p class="service-note" id="request-service-note">Online requests are stored for review. Automatic email receipts are not currently enabled.</p></div>{existing_form}</section>'''
    steps = [
        ('Tell us what you need', 'Product, quantity, specifications, target price and where it needs to go.'),
        ('We shortlist vetted suppliers', 'We compare relevant options from our supplier network. Shortlist timing is confirmed after review.'),
        ('We check samples and quality', 'Review factory and sample photos. Samples and independent inspection are arranged as agreed.'),
        ('We buy, ship and deliver', 'One itemized landed price, with delivery and the agreed inclusions set out before purchase.'),
    ]
    process = ''.join(f'<li><span class="step-number">0{i}</span><h3>{escape(t)}</h3><p>{escape(d)}</p></li>' for i, (t, d) in enumerate(steps, 1))
    categories = ''.join(f'<a class="category-tile" href="{u}"><span class="category-number">0{i}</span><div><h3>{escape(t)}</h3><p>{escape(d)}</p></div><span class="tile-arrow" aria-hidden="true">&#8599;</span></a>' for i, (t, d, u) in enumerate(CATEGORIES, 1))
    benefits = [
        ('One point of contact', 'A single contact coordinates your order, from the first brief to final delivery.'),
        ('A clear shortlist schedule', 'Supplier-shortlist timing is agreed after we review the product and specifications.'),
        ('See it before approving it', 'Review factory and sample photos before purchase approval. Inspection scope is agreed in advance.'),
        ('One price, including delivery', 'An itemized USD or CAD quote sets out product, delivery and the agreed inclusions and exclusions.'),
        ('Updates until delivery', 'Stay informed as supplier selection, production, inspection and delivery progress.'),
    ]
    benefits_html = ''.join(f'<li><h3>{escape(t)}</h3><p>{escape(d)}</p></li>' for t, d in benefits)
    main = f'''<section class="sourcing-hero"><img class="hero-media" src="/assets/sourcing-assortment.webp" alt="Illustrative assortment of metal parts, packaging, fabric, electronics, rice and building materials" width="1536" height="1024" fetchpriority="high"><div class="hero-content"><p class="kicker">Global sourcing. North American delivery.</p><h1>Buy Anything.<br>From Anywhere.<br>Delivered to Your Door.</h1><p class="hero-subline">Tell us what you need. We find the right supplier, check the quality, buy it and ship it to you across the US, Canada and Mexico.</p><a class="button primary" href="#contact" data-inquiry="sourcing">Start a Sourcing Request <span aria-hidden="true">&#8599;</span></a></div><span class="image-caption">Illustrative product assortment</span></section>
<div class="region-band"><span>{REGION}</span><span>Supplier selection &middot; Quality checks &middot; Door-to-door delivery</span></div>
<section class="section" id="how-it-works"><div class="section-heading"><p class="kicker">How it works</p><h2>From your brief<br>to your door.</h2></div><ol class="process-grid">{process}</ol></section>
<section class="section categories-section" id="what-we-source"><div class="section-heading"><p class="kicker">What we source</p><h2>The right product.<br>The right supplier.</h2><p>For your business, your project or your next order. Product availability and import requirements are confirmed before purchase.</p></div><div class="category-grid">{categories}</div></section>
<section class="section buyers-section"><div class="section-intro"><p class="kicker">Why buyers use us</p><h2>A considered approach<br>to every order.</h2><p>Less chasing. Clear decisions. Careful coordination from supplier selection through delivery.</p></div><ul class="benefit-list">{benefits_html}</ul></section>
<section class="section delivery-section" id="delivery"><p class="kicker">Delivery handled</p><h2>Air, ocean and truck,<br>door to door,<br>with customs handled.</h2><p>Delivery is part of the sourcing plan. We coordinate the route, customs and handoffs for the destination agreed in your quote.</p><p class="small">One itemized landed price in USD or CAD. Inclusions, exclusions and delivery requirements agreed upfront.</p></section>
<section class="section faq-section" id="faq"><div class="section-intro"><p class="kicker">FAQ</p><h2>Before you<br>place an order.</h2></div><div class="faq-list">{faq_markup()}</div></section>{request_section}'''
    faq_schema = {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS]}
    write('index.html', document('Cargo Global | Sourcing & Delivery to North America', '/', main, extra_schema=[faq_schema], body_class='home-page'))
    contact = '''<section class="page-intro"><p class="kicker">Cargo Global</p><h1>Let’s find what<br>you need.</h1><p>Serving buyers across the US, Canada and Mexico.</p></section>''' + request_section
    write('contact/index.html', document('Start a Sourcing Request', '/contact/', contact, body_class='contact-page'))
    sourcing = '''<section class="page-intro"><p class="kicker">Product sourcing</p><h1>A buying partner.<br>From brief to delivery.</h1><p>Tell us what you need. Cargo Global sources through our global supplier network, compares quotes, coordinates samples and quality checks, and delivers to your door.</p><a class="button primary" href="/contact/?inquiry=sourcing">Start a Sourcing Request <span aria-hidden="true">&#8599;</span></a></section>
<section class="section editorial"><h2>Start with a clear product brief</h2><p>Send the product description, quantity and unit, materials, dimensions, reference photos or specifications, target price in USD or CAD, and delivery city, province or state and country. Tell us which details are essential and where alternatives are acceptable.</p><h2>Compare a relevant supplier shortlist</h2><p>We work through our established global supplier network and compare options against your brief. Supplier minimum quantities, sample availability, production lead times and the timing for a shortlist are confirmed after review.</p><h2>Review samples and quality requirements</h2><p>Samples can be arranged before purchase approval. We help agree acceptance criteria and facilitate a pre-shipment inspection by a local independent inspector where included in the order. Scope, fees and the information you will receive are agreed in advance.</p><h2>Approve an itemized landed-price quote</h2><p>Your quote identifies the currency and the agreed product, quality, customs and delivery costs, plus any exclusions. You approve the written quote and payment stages before an order is placed. A website request does not authorize a purchase or commit you to payment.</p><h2>We coordinate the purchase and delivery</h2><p>One point of contact coordinates the order and status updates through delivery across the US, Canada and Mexico. Delivery requirements, access, unloading, appointments and any special handling are checked as part of the plan.</p><h2 id="packaging">Packaging</h2><p>Share the material, pack dimensions, printing requirements, quantity and any contact or product-protection requirements. A sample and artwork approval can be included before production.</p><h2 id="building-materials">Building materials</h2><p>Share the material grade, dimensions, finish, quantity and project destination. Product standards, test documentation and delivery access need to be reviewed before a supplier is approved.</p><a class="text-link" href="/freight-research/">Explore sourcing guides <span aria-hidden="true">&#8599;</span></a></section>'''
    write('sourcing/index.html', document('Product Sourcing, From Brief to Delivery', '/sourcing/', sourcing))
    about = '''<section class="page-intro"><p class="kicker">About Cargo Global</p><h1>Your brief.<br>Our coordination.</h1><p>Cargo Global brings supplier selection, quality checks, buying and delivery into one coordinated sourcing process.</p></section><section class="section editorial"><h2>Global suppliers. North American buyers.</h2><p>We work through an established supplier network worldwide for buyers across the US, Canada and Mexico. Each request starts with the product, quantity, specifications, budget and delivery requirements, not a transport booking.</p><h2>Clear decisions before a purchase</h2><p>We compare relevant suppliers and quotes, coordinate samples when required, and facilitate independent pre-shipment inspections where agreed. You review the specifications, acceptance criteria and an itemized landed-price quote before approving a purchase.</p><h2>One point of contact until delivery</h2><p>Air, ocean, truck and customs coordination support the order. The agreed plan sets out the currency, payment stages, inclusions, exclusions, quality checks and delivery requirements. We provide status updates as the order moves from supplier selection to delivery.</p><a class="button primary" href="/contact/">Start a Sourcing Request <span aria-hidden="true">&#8599;</span></a></section>'''
    write('about/index.html', document('About Our Sourcing Approach', '/about/', about))
    thank_you = '''<section class="page-intro"><p class="kicker">Request received</p><h1>Thank you.<br>Your request is saved.</h1><p>Your details have been saved for review. Automatic email receipts are not currently enabled.</p><a class="button primary" href="/">Back to Cargo Global</a></section>'''
    write('thank-you.html', document('Request Received', '/thank-you.html', thank_you, noindex=True))
    for path, name in [('trust-center/index.html', 'Company Information'), ('official-flash-cargo-global/index.html', 'Official Website'), ('verify-flash-cargo-global/index.html', 'Company Verification')]:
        body = f'<section class="page-intro"><p class="kicker">Cargo Global</p><h1>{name}</h1><p>{DESCRIPTION}</p></section><section class="section editorial"><h2>Our official website</h2><p>The official website is flashcargoglobal.com. Product sourcing, quality checks and delivery requirements are confirmed in a written quote before an order is approved.</p><h2>Start with your requirements</h2><p>{REGION}. Use our online request form to share what you need.</p><a class="button primary" href="/contact/">Start a Request</a></section>'
        write(path, document(name, route(ROOT / path), body, noindex=True))
    write('404.html', document('Page Not Found', '/404.html', '<section class="page-intro"><p class="kicker">Page not found</p><h1>Let’s get you<br>to the right place.</h1><a class="button primary" href="/">Back to Cargo Global</a></section>', noindex=True))


def build_legal_pages():
    privacy = f'''<article class="guide-article legal-copy"><p class="kicker">Privacy</p><h1>Privacy Policy</h1><p class="updated">Updated {DAY}</p><p>Cargo Global uses the information you choose to submit to review product sourcing and delivery requests, prepare quotes and coordinate approved orders.</p>
<h2>Information submitted with a request</h2><p>A request may include product specifications, quantities, a target price and currency, reference links and a delivery location. The current intake form also asks for private contact details to allow follow-up. These details are not published as a business directory or displayed in public enquiry listings. Please do not submit payment-card details, passwords, identity documents, health information or confidential material that is not needed to review the request.</p>
<h2>How request information is used</h2><p>Information is used to assess feasibility, clarify specifications, compare supplier options, prepare a quote and, where you approve an order, coordinate samples, inspections, purchase and delivery. A request is not permission to place an order or charge a payment.</p>
<h2>Hosting and request handling</h2><p>The public website is hosted using GitHub Pages. The request handler runs on Cloudflare Workers and stores submitted enquiries in Cloudflare storage. These providers may process technical information such as an IP address, request time and browser information to operate and protect their services. Existing business mail is provided through Microsoft 365. Automatic form-to-email delivery is not currently enabled.</p>
<h2>Sharing for an approved request or order</h2><p>Product and delivery information may need to be shared with relevant suppliers, inspectors, carriers or customs service providers to assess or fulfil the request. Only information relevant to that work should be shared. Do not include third-party personal information or proprietary documents unless you are authorized to provide them.</p>
<h2>Reference files and links</h2><p>A linked photograph or specification remains subject to the privacy and access settings of the service hosting it. Avoid links that publicly expose unrelated documents. File-upload handling is not enabled in the current intake form.</p>
<h2>Cookies and analytics</h2><p>This release does not include a shared advertising pixel, a Google Analytics tag or a tag-manager container. Hosting and security providers may still process necessary technical data. External source links have their own privacy practices.</p>
<h2>Retention and access</h2><p>Request information should be kept only while it is needed for review, an approved order, applicable recordkeeping or a legitimate security purpose. A fixed retention schedule has not yet been established for the request store. You may ask to access, correct or remove information you submitted through the online contact route, subject to applicable legal requirements and our ability to verify the request.</p>
<h2>Cross-border processing and security</h2><p>Providers and approved order partners may process information outside your country. Access should be limited to people and providers who need it for the request or order. No internet service can promise absolute security. Do not send sensitive documents through the general request form.</p>
<h2>Questions or changes</h2><p>Use the <a href="/contact/">online request page</a> for privacy enquiries. This page may be updated when our services or request-handling arrangements change. The date above identifies the current version.</p></article>'''
    terms = f'''<article class="guide-article legal-copy"><p class="kicker">Terms</p><h1>Website and Request Terms</h1><p class="updated">Updated {DAY}</p><p>These terms explain how Cargo Global’s website and request process work. The written quotation and order-specific agreement set the commercial terms for any purchase or delivery.</p>
<h2>Requests are not orders</h2><p>Submitting a request asks us to review requirements. It does not reserve stock, authorize a supplier purchase, create a delivery booking or authorize payment. An order proceeds only after the relevant quote and approval steps are agreed.</p>
<h2>Product and supplier review</h2><p>Availability, minimum quantities, sample options, production timing and supplier suitability depend on the product and request. You are responsible for providing accurate specifications and identifying any required certifications or acceptance criteria. We confirm the review scope with you; a supplier shortlist is not a guarantee of every product attribute.</p>
<h2>Samples and inspections</h2><p>Samples, factory information and independent inspection can support an approval decision. Sample charges, inspection scope, timing, acceptance criteria and any limitations must be set out in the quote or order agreement. No inspection can guarantee the absence of every defect or establish compliance beyond its agreed scope.</p>
<h2>Price, currency and payment</h2><p>Quotes identify USD or CAD and set out the agreed inclusions and exclusions. Product, samples, tooling, inspection, freight, customs, taxes, unloading and delivery are included only to the extent stated in the quote. Currency conversion, payment stages and any changes must be agreed before purchase. Do not send payment details through the website form.</p>
<h2>Compliance and availability</h2><p>We review requests subject to applicable import, export, product-safety and sanctions requirements. The phrase “Buy Anything” is an invitation to discuss a product, not an offer to source prohibited, counterfeit or otherwise unlawful goods. Products needing permits, testing, registration or special handling require review before acceptance.</p>
<h2>Delivery and changes</h2><p>Production and delivery schedules depend on supplier performance, inspection, transport, customs clearance and destination requirements. Estimated dates are not guaranteed unless the order agreement expressly says otherwise. Access restrictions, appointment requirements, unloading, changes and additional costs should be agreed in writing.</p>
<h2>Cancellations, defects and claims</h2><p>Cancellation, return, warranty, defect and transport-claim arrangements must be set out in the applicable supplier terms and order agreement before you approve the purchase. The website does not promise a general return or refund policy for every sourced product. Any mandatory legal rights continue to apply.</p>
<h2>Guides and external sources</h2><p>Guides are preparation aids, not a substitute for current advice from the responsible authority or a qualified adviser. Rules may change. External sources are independently operated and are not endorsements or evidence of a partnership with Cargo Global.</p>
<h2>Website content and privacy</h2><p>Do not misuse the site, upload unlawful material or submit information you have no right to share. Request handling is described in the <a href="/privacy-policy/">Privacy Policy</a>. Order-specific written terms and applicable law govern any transaction; this general page does not replace them.</p></article>'''
    write('privacy-policy/index.html', document('Privacy Policy', '/privacy-policy/', privacy))
    write('terms/index.html', document('Website and Request Terms', '/terms/', terms))


def is_excluded(path):
    value = route(path)
    if value in MERGES or value in ['/thank-you.html', '/404.html']:
        return True
    return path.relative_to(ROOT).parts[0] in ('planning', 'resources', 'services', 'trust-center', 'official-flash-cargo-global', 'verify-flash-cargo-global')


def rebrand_json(data):
    if isinstance(data, dict):
        out = {}
        for key, value in data.items():
            if key in ('address', 'telephone', 'email', 'foundingDate', 'sameAs'):
                continue
            if key == 'legalName':
                out[key] = 'Flash Cargo Global'
            elif key == 'areaServed':
                out[key] = ['US', 'CA', 'MX']
            elif key in ('logo', 'image') and isinstance(value, str) and 'wixstatic.com' in value:
                out[key] = BASE + '/assets/sourcing-assortment.jpg'
            else:
                out[key] = rebrand_json(value)
        return out
    if isinstance(data, list):
        return [rebrand_json(v) for v in data]
    if isinstance(data, str):
        data = data.replace('Flash Cargo Global', 'Cargo Global').replace('FLASH CARGO GLOBAL', 'CARGO GLOBAL')
        data = data.replace('Serving from North America', REGION)
        data = re.sub(r'\bAI\b', 'intelligence', data)
        for old, new in SOURCE_REPLACEMENTS.items():
            data = data.replace(old, new)
        for old, new in MERGES.items():
            if data in (old, BASE + old):
                data = new if data.startswith('/') else BASE + new
        return data
    return data


def reconcile_library():
    records = []
    for path in pages():
        soup = BeautifulSoup(path.read_text(encoding='utf-8-sig'), 'html.parser')
        current_route = route(path)
        if not soup.head or not soup.body:
            continue
        old_title = soup.title.get_text(' ', strip=True) if soup.title else ''
        for node in list(soup.find_all(string=True)):
            if node.parent.name not in ('script', 'style'):
                value = rebrand_json(str(node))
                if value != str(node):
                    node.replace_with(value)
        for el in soup.find_all(True):
            for key, value in list(el.attrs.items()):
                if isinstance(value, str):
                    el[key] = rebrand_json(value)
        for script in soup.select('script[type="application/ld+json"]'):
            data = rebrand_json(json.loads(script.string or script.get_text()))
            if data.get('@type') == 'Article':
                data['dateModified'] = DAY
                if current_route.startswith('/guides/') and 'apparel-textile' not in current_route:
                    data['citation'] = [u for u in data.get('citation', []) if 'ftc.gov' not in u and 'wearing-apparel' not in u]
            script.string = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        for script in list(soup.select('script[src]')):
            if any(term in script['src'].lower() for term in ('googletag', 'analytics', 'tagmanager', 'facebook', 'clarity', 'beacon.min.js')):
                script.decompose()
        for paragraph in list(soup.find_all(['p', 'li'])):
            if re.search(r'unrelated (Flash )?companies|stale under-construction', paragraph.get_text(), re.I):
                paragraph.decompose()
        for anchor in list(soup.select('a[href]')):
            if 'flashcargonetwork.com' in anchor['href'].lower():
                anchor.unwrap()
            elif current_route.startswith('/guides/') and 'apparel-textile' not in current_route and ('ftc.gov' in anchor['href'] or 'wearing-apparel' in anchor['href']):
                container = anchor.find_parent('li')
                if container:
                    container.decompose()
                else:
                    anchor.decompose()
        if soup.select_one('header.site-header'):
            soup.select_one('header.site-header').replace_with(fragment(header()))
        if soup.select_one('footer'):
            soup.select_one('footer').replace_with(fragment(footer()))
        for link in list(soup.select('link[rel="stylesheet"]')):
            link.decompose()
        soup.head.append(fragment('<link rel="stylesheet" href="/cargo-global.css?v=1">'))
        if not soup.select_one('script[src*="cargo-global.js"]'):
            soup.head.append(fragment('<script src="/cargo-global.js?v=1" defer></script>'))
        policy = soup.find('meta', attrs={'http-equiv': 'Content-Security-Policy'})
        if policy:
            policy['content'] = POLICY
        else:
            soup.head.append(fragment(f'<meta http-equiv="Content-Security-Policy" content="{POLICY}">'))
        for el in list(soup.select('h1, h2, h3')):
            text = el.get_text(' ', strip=True)
            if text.endswith(('...', '…')):
                el.string = text.rstrip('.… ')
        lang = str(soup.html.get('lang', 'en')).split('-')[0]
        locale = LOCALES.get(lang, LOCALES['en'])
        if len(path.relative_to(ROOT).parts) == 3 and path.relative_to(ROOT).parts[0] in ('guides', 'freight-research'):
            if soup.h1:
                soup.h1.string = HUB_LABELS[path.relative_to(ROOT).parts[0]].get(lang, locale[0])
            lead = soup.select_one('.knowledge-hero .lead')
            if lead:
                lead.string = locale[1]
            kicker = soup.select_one('.knowledge-hero .kicker')
            if kicker:
                kicker.string = locale[0]
        if path.relative_to(ROOT).parts[0] == 'industries' and soup.h1:
            mapping = {
                'Industry Freight Planning': 'Product sourcing by category',
                'Machinery and industrial parts freight planning guide': 'Industrial parts sourcing checklist',
                'Furniture fixtures and white glove freight guide': 'Furniture and fixtures sourcing checklist',
                'Agriculture and food ingredient freight planning guide': 'Food ingredient supplier checklist',
                'Apparel and textile manufacturing export freight guide': 'Apparel and textile supplier checklist',
                'Electronics and connected devices freight checklist': 'Electronics supplier checklist',
                'Automotive parts and aftermarket freight planning guide': 'Automotive parts supplier checklist',
                'Consumer products and retail freight planning guide': 'Consumer product supplier checklist',
                'Cosmetics and personal care import freight guide': 'Cosmetics supplier preparation checklist',
            }
            old = soup.h1.get_text(' ', strip=True)
            soup.h1.string = mapping.get(old, old)
        if soup.h1 and current_route not in ('/',):
            title = f'Cargo Global | {soup.h1.get_text(" ", strip=True)}'
            soup.title.string = title
            for meta in soup.select('meta[property="og:title"], meta[name="twitter:title"]'):
                meta['content'] = title
            for script in soup.select('script[type="application/ld+json"]'):
                data = json.loads(script.string or script.get_text())
                entries = data.get('@graph', [data])
                for entry in entries:
                    if entry.get('@type') == 'Article':
                        entry['headline'] = soup.h1.get_text(' ', strip=True)
                    elif entry.get('@type') in ('CollectionPage', 'WebPage'):
                        entry['name'] = soup.h1.get_text(' ', strip=True)
                script.string = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        if current_route == '/':
            soup.title.string = 'Cargo Global | Sourcing & Delivery to North America'
        for meta in soup.select('meta[property="og:site_name"]'):
            meta['content'] = 'Cargo Global'
        for meta in soup.select('meta[property="og:image"], meta[name="twitter:image"]'):
            meta['content'] = BASE + '/assets/sourcing-assortment.jpg'
        article = soup.select_one('article.guide-article')
        if article and current_route not in ('/privacy-policy/', '/terms/') and not article.select_one('.sourcing-context'):
            context = fragment(f'<aside class="sourcing-context"><p class="kicker">{locale[2]}</p><p>{locale[3]}</p><a class="text-link" href="/contact/?inquiry=sourcing">{locale[4]} <span aria-hidden="true">&#8599;</span></a></aside>')
            article.insert(0, context)
        robots = soup.find('meta', attrs={'name': 'robots'})
        if not robots:
            robots = soup.new_tag('meta', attrs={'name': 'robots'})
            soup.head.append(robots)
        robots['content'] = 'noindex, follow' if is_excluded(path) else 'index, follow'
        path.write_text(str(soup), encoding='utf-8', newline='\n')
        records.append({'path': current_route, 'old_title': old_title, 'title': soup.title.get_text(), 'indexing': robots['content'], 'source_url': BASE + current_route, 'last_checked': STAMP})
    return records


def merge_duplicates():
    for old, new in MERGES.items():
        old_file = ROOT / old.strip('/') / 'index.html'
        new_file = ROOT / new.strip('/') / 'index.html'
        source = BeautifulSoup(old_file.read_text(encoding='utf-8'), 'html.parser')
        target = BeautifulSoup(new_file.read_text(encoding='utf-8'), 'html.parser')
        target_article = target.select_one('article.guide-article')
        if target_article and not target_article.select_one('[data-merged-checks]'):
            known = set(target_article.stripped_strings)
            extras = []
            for li in source.select('.guide-panel li'):
                text = li.get_text(' ', strip=True)
                if text not in known and len(text) > 30:
                    extras.append(text)
                    known.add(text)
            if extras:
                target_article.append(fragment('<section data-merged-checks><h2>Additional supplier preparation checks</h2><ul>' + ''.join(f'<li>{escape(t)}</li>' for t in extras) + '</ul></section>'))
            new_file.write_text(str(target), encoding='utf-8', newline='\n')
        body = f'<section class="page-intro"><p class="kicker">Sourcing guide</p><h1>This checklist has moved.</h1><p>The consolidated version includes supplier preparation and product checks.</p><a class="button primary" href="{new}">Open the full checklist</a></section>'
        stub = BeautifulSoup(document('Supplier Checklist Moved', old, body, noindex=True), 'html.parser')
        stub.find('link', rel='canonical')['href'] = BASE + new
        stub.head.append(fragment(f'<meta http-equiv="refresh" content="0;url={new}">'))
        write(old.strip('/') + '/index.html', str(stub))


def rebuild_hubs():
    for root_name in ('freight-research', 'industries'):
        path = ROOT / root_name / 'index.html'
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        if root_name == 'freight-research':
            soup.h1.string = 'Supplier-country checklists'
            lead = soup.select_one('.lead')
            if lead:
                lead.string = 'Practical sourcing preparation for buyers comparing suppliers, samples, specifications and delivery requirements. Choose a language or a supplier-country checklist.'
            hero = soup.select_one('.knowledge-hero')
            if hero and hero.select_one('.kicker'):
                hero.select_one('.kicker').string = 'Sourcing preparation'
            if hero and not soup.select_one('.language-links'):
                hero.append(fragment('<nav class="language-links" aria-label="Guide languages">' + ''.join(f'<a href="/freight-research/{code}/" lang="{code}">{label}</a>' for code, label in [('en','English'),('es','Español'),('fr','Français'),('zh','中文'),('hi','हिन्दी')]) + '</nav>'))
        path.write_text(str(soup), encoding='utf-8', newline='\n')


def update_machine_files():
    data = {'@context': 'https://schema.org', **organization(), 'last_checked': STAMP, 'source_url': BASE + '/.well-known/organization.json'}
    write('.well-known/organization.json', json.dumps(data, ensure_ascii=False, indent=2))
    citation = {'brand_name': 'Cargo Global', 'legal_name': 'Flash Cargo Global', 'official_domain': BASE + '/', 'public_contact_method': 'Online request form', 'contact_url': BASE + '/contact/', 'public_service_area': REGION, 'services': ['Global product sourcing', 'Supplier shortlisting', 'Samples and pre-shipment inspection coordination', 'Purchase and door-to-door delivery coordination'], 'public_guides': [BASE + '/freight-research/', BASE + '/guides/en/'], 'last_checked': STAMP, 'source_url': BASE + '/.well-known/citation-profile.json'}
    write('.well-known/citation-profile.json', json.dumps(citation, ensure_ascii=False, indent=2))
    write('humans.txt', 'Cargo Global\nGlobal product sourcing and delivery.\n' + REGION + '\nContact: ' + BASE + '/contact/\nLast checked: ' + DAY + '\n')
    write('llms.txt', '# Cargo Global\n\n' + DESCRIPTION + '\n\n## Primary pages\n- [Sourcing](' + BASE + '/sourcing/)\n- [Start a Request](' + BASE + '/contact/)\n- [Supplier-country checklists](' + BASE + '/freight-research/)\n- [About](' + BASE + '/about/)\n- [Terms](' + BASE + '/terms/)\n- [Privacy](' + BASE + '/privacy-policy/)\n\n## Scope\n' + REGION + '. Supplier options, quality checks, currency, inclusions, exclusions and delivery requirements are confirmed before purchase.\n\n## Request status\nCurrent requests are saved for review. Automatic form-to-email delivery is not enabled.\n\nLast checked: ' + DAY + '\nSource: ' + BASE + '/\n')
    write('robots.txt', 'User-agent: *\nAllow: /\n\nSitemap: ' + BASE + '/sitemap.xml\n')
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', namespace)
    sitemap = ET.Element(f'{{{namespace}}}urlset')
    for path in pages():
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        robots = soup.find('meta', attrs={'name': 'robots'})
        if not robots or 'noindex' in robots.get('content', ''):
            continue
        canonical = soup.find('link', rel='canonical')
        expected = BASE + route(path)
        if not canonical or canonical['href'] != expected:
            continue
        url = ET.SubElement(sitemap, f'{{{namespace}}}url')
        ET.SubElement(url, f'{{{namespace}}}loc').text = expected
        ET.SubElement(url, f'{{{namespace}}}lastmod').text = DAY
    ET.indent(sitemap)
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(sitemap, encoding='unicode'))


def back_up():
    archive = OUT / 'before-reposition.zip'
    if archive.exists():
        return
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in ROOT.rglob('*'):
            rel = path.relative_to(ROOT)
            if path.is_file() and rel.parts[0] not in ('output', '.git', 'assets'):
                bundle.write(path, rel.as_posix())


def main():
    back_up()
    build_primary_pages()
    build_legal_pages()
    reconcile_library()
    merge_duplicates()
    rebuild_hubs()
    # Rerun metadata after hub names and canonical merges are settled.
    records = reconcile_library()
    update_machine_files()
    with (OUT / 'page-changes.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({'pages': len(records), 'noindex': sum('noindex' in r['indexing'] for r in records), 'merged_routes': len(MERGES), 'backup': str(OUT / 'before-reposition.zip')}))


if __name__ == '__main__':
    main()
