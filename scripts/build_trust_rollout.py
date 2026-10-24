"""Build honest process documents and source-linked guides; never invent proof."""

import csv
import json
from datetime import datetime
from html import escape
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from guide_experience import BASE, ROOT, content_fingerprint, documents, route
from trust_rollout_content import ANTI_PHISHING, CAPABILITY_COPY, FBX_UPDATE, LANES, PAYMENT_RULES, PROCESS_LINE, RETIRED_EXACT, RETIRED_PREFIXES, TEMPLATES


def retired_target(path):
    normalized = '/' + path.strip('/') + '/'
    if normalized in RETIRED_EXACT:
        return RETIRED_EXACT[normalized]
    return next((target for prefix,target in RETIRED_PREFIXES.items() if normalized.startswith(prefix)),None)


def primary_navigation(soup):
    from build_audience_rollout import header, footer
    soup.header.replace_with(BeautifulSoup(header(),'html.parser'))
    soup.footer.replace_with(BeautifulSoup(footer(),'html.parser'))


def build_lane_guides(document):
    from build_cargo_global import write
    proposed = {}
    day = datetime.now(ZoneInfo('America/Toronto')).date().isoformat()
    for lane in LANES:
        current = '/freight-research/' + lane['slug'] + '/'
        description = 'Supplier specifications, sample checks and quote scope for a China-to-' + lane['destination'].removeprefix('the ') + ' order, with dated primary index references.'
        checks = ''.join('<li>' + escape(text) + '</li>' for text in lane['buyer_checks'])
        main = '<article class="guide-article"><p class="kicker">Sourcing guides</p><h1>' + escape(lane['title']) + '</h1><p class="lead">A considered buying brief comes before a transport price. Compare the supplier, approved product and delivery scope before relying on an index benchmark.</p>'
        main += '<section><h2>Start with the buying decision</h2><p>Record the intended use, product specification, quantity and unit, material, finish, packaging and destination. Keep essential requirements separate from preferences. A supplier needs to know which details are fixed and which still need a sample or a documented answer.</p><p>Ask for a comparable quote rather than the lowest unexplained total. Identify what is included, what remains unconfirmed and how long the offer is valid. Do not turn an indicative ocean index into an itemized delivered price.</p></section>'
        main += '<section><h2>The reading and its limits</h2><p>' + escape(lane['regional_fact']) + '</p><p>A regional index does not establish the price for every port, a different container size, a shared container or final delivery. Check the primary publisher’s port coverage before comparing a quote with the reading.</p><p>Only a single attributed public FBX weekly reading is reproduced here. It is not a monthly average and is not converted into a 20ft price. A genuine dated written quote can be shown only with publication approval; other amounts remain quote required.</p></section>'
        main += '<section><h2>Confirm the actual handoff</h2><ul>' + checks + '</ul></section>'
        main += '<section><h2>Keep quality evidence with the order</h2><p>Identify the approved sample and specification revision. Confirm the checks needed before release and keep photographs, findings and unresolved issues together. Third-party inspection can be booked on request; its scope and charges must be agreed. An inspection is not a blanket product certification.</p><p>Record the invoice description, package count, dimensions, weight and receiving restrictions for the actual goods. Ask the responsible importer and qualified service providers to review product-specific obligations. No generic duty, tax or delivery promise is supplied here.</p></section>'
        main += '<section><h2>Use an itemized comparison</h2><p>Separate product cost, sample and inspection costs, origin work, transport, destination work, applicable duty and tax, and final delivery. Unknown amounts remain quote required. Keep all compared amounts in one stated currency and identify exclusions before a purchase decision.</p><p>Cargo Global serves buyers across the US, Canada and Mexico. This reference explains the named index lane; availability and any service outside that buyer focus require written confirmation.</p><a href="/sourcing/#sample-documents">Review the sample document formats</a></section>'
        main += '<section><h2>Primary sources</h2><ul>' + ''.join('<li><a href="' + escape(url, quote=True) + '">' + escape(name) + '</a><small class="source-checked"> Last checked: <time datetime="' + day + '">' + day + '</time></small></li>' for name, url in [(lane['fbx'] + ' route definition', lane['fbx_url']), ('Freightos public weekly update', FBX_UPDATE)]) + '</ul></section><p><a class="text-link" href="/contact/#buyer-request">Start a sourcing request</a></p></article>'
        schema = {'@type':'Article','headline':lane['title'],'description':description,'mainEntityOfPage':BASE+current,'publisher':{'@id':BASE+'/#organization'},'citation':[lane['fbx_url'],FBX_UPDATE]}
        soup = BeautifulSoup(document(lane['title'],current,main,extra_schema=[schema]),'html.parser')
        primary_navigation(soup)
        for meta in soup.select('meta[name="description"],meta[property="og:description"]'):
            meta['content'] = description
        write(current.strip('/')+'/index.html',str(soup))
        proposed[current] = {'review_status':'awaiting_fact_review','content_sha256':content_fingerprint(soup),'facts':[{'claim':lane['regional_fact'],'source_url':lane['fbx_url'],'checked_on':day,'verified':False}]}
    out = ROOT/'output/trust-rollout'
    out.mkdir(parents=True,exist_ok=True)
    (out/'proposed-publication-review.json').write_text(json.dumps(proposed,ensure_ascii=False,indent=2),encoding='utf-8')


def build_payment_page(document):
    from build_cargo_global import write
    current='/how-payment-works/'
    day=datetime.now(ZoneInfo('America/Toronto')).date().isoformat()
    body='<article class="guide-article"><p class="kicker">Before a payment</p><h1>How Payment Works.</h1><p class="lead">'+escape(PROCESS_LINE)+'</p>'
    body+=''.join('<section><h2>'+escape(title)+'</h2><p>'+escape(text)+'</p></section>' for title,text in PAYMENT_RULES)
    body+='<section><h2>Verify an unexpected request</h2><p>'+escape(ANTI_PHISHING)+'</p><p>If payment details change or a request does not match the agreed quote, stop and use the request form on this website to verify it. Do not send payment-card details, passwords or bank credentials through the enquiry form.</p><a class="text-link" href="/contact/#buyer-request">Ask us to verify the request</a></section><p><a href="/terms/">Read the order and website terms</a></p><p class="updated">Policy last checked: <time datetime="'+day+'">'+day+'</time></p></article>'
    soup=BeautifulSoup(document('How Payment Works',current,body),'html.parser')
    primary_navigation(soup)
    description='Written itemized quotes, staged supplier payments, sample approval, pre-shipment inspection and clear refund or replacement terms before payment.'
    for meta in soup.select('meta[name="description"],meta[property="og:description"]'):
        meta['content']=description
    write('how-payment-works/index.html',str(soup))
    terms=BeautifulSoup((ROOT/'terms/index.html').read_text(encoding='utf-8'),'html.parser')
    for previous in terms.select('#payment-protection-policy'):
        previous.decompose()
    terms.article.append(BeautifulSoup('<section id="payment-protection-policy"><h2>Our payment policy</h2>'+''.join('<h3>'+escape(title)+'</h3><p>'+escape(text)+'</p>' for title,text in PAYMENT_RULES)+'<p>'+escape(ANTI_PHISHING)+'</p><p><a href="/how-payment-works/">How payment works</a></p></section>','html.parser'))
    write('terms/index.html',str(terms))
    for current in ('about','sourcing'):
        path=ROOT/current/'index.html'
        page=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        for previous in page.select('[data-order-process-policy]'):
            previous.decompose()
        container=page.select_one('.editorial') or page.main
        container.append(BeautifulSoup('<p class="lead" data-order-process-policy>'+escape(PROCESS_LINE)+'</p><p><a href="/how-payment-works/">See the payment steps</a></p>','html.parser'))
        write(current+'/index.html',str(page))


def add_process_documents():
    day = datetime.now(ZoneInfo('America/Toronto')).date().isoformat()
    soup = BeautifulSoup((ROOT/'sourcing/index.html').read_text(encoding='utf-8'),'html.parser')
    container = soup.select_one('.editorial')
    for previous in soup.select('#sample-documents,#capability-scope'):
        previous.decompose()
    block = '<section id="sample-documents"><h2>See the working formats.</h2><p>These are blank sample templates, not completed orders, client examples or proof of a past sale. The actual scope and terms belong in the written order agreement.</p>'
    for filename, title, fields in TEMPLATES:
        path = ROOT/'assets'/(filename+'.csv')
        with path.open('w',encoding='utf-8-sig',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=['field','information_to_confirm','your_entry','source_url','last_checked'])
            writer.writeheader()
            writer.writerows({'field':name,'information_to_confirm':instruction,'your_entry':'','source_url':BASE+'/sourcing/#sample-documents','last_checked':day} for name,instruction in fields)
        block += '<details><summary>' + escape(title) + '</summary><p>Sample template. All entry fields are blank; no supplier, price or inspection outcome is asserted.</p><div class="table-scroll"><table><caption>' + escape(title) + '</caption><thead><tr><th scope="col">Field</th><th scope="col">What to record</th></tr></thead><tbody>' + ''.join('<tr><th scope="row">'+escape(name)+'</th><td>'+escape(instruction)+'</td></tr>' for name,instruction in fields) + '</tbody></table></div><p><a download href="/assets/' + filename + '.csv">Download the blank CSV template</a></p></details>'
    block += '</section><section id="capability-scope"><h2>What we do and don’t do.</h2><ul>' + ''.join('<li>'+escape(text)+'</li>' for text in CAPABILITY_COPY) + '</ul></section>'
    container.append(BeautifulSoup(block,'html.parser'))
    (ROOT/'sourcing/index.html').write_text(str(soup),encoding='utf-8')


def link_guides():
    path=ROOT/'freight-research/index.html'
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    for previous in soup.select('#index-route-guides'):
        previous.decompose()
    block='<section class="section" id="index-route-guides"><h2>Buying briefs by index route.</h2><p>Match the supplier brief to a named route before comparing transport benchmarks. These guides do not promise a rate or delivery date.</p><ul>' + ''.join('<li><a href="/freight-research/'+lane['slug']+'/">'+escape(lane['title'])+'</a></li>' for lane in LANES) + '</ul></section>'
    soup.main.append(BeautifulSoup(block,'html.parser'))
    path.write_text(str(soup),encoding='utf-8')


def retire_legacy_pages(document):
    from build_cargo_global import write
    targets={}
    for path in documents():
        current=route(path)
        target=retired_target(current)
        if not target:
            continue
        targets[current]=target
        label='About Cargo Global' if target=='/about/' else 'Delivery' if target=='/delivery/' else 'Product sourcing'
        page=BeautifulSoup(document('Continue to '+label,current,'<section class="page-intro"><h1>Continue to '+escape(label)+'.</h1><p>This address now leads to the current Cargo Global page.</p><a class="button primary" href="'+target+'">Continue</a></section>'),'html.parser')
        page.html['data-retired-route']=''
        page.select_one('link[rel="canonical"]')['href']=BASE+target
        page.head.append(page.new_tag('meta',attrs={'http-equiv':'refresh','content':'0; url='+BASE+target}))
        for script in page.select('script[type="application/ld+json"]'):
            script.decompose()
        for meta in page.select('meta[property="og:url"]'):
            meta['content']=BASE+target
        primary_navigation(page)
        write(path.relative_to(ROOT).as_posix(),str(page))
    for path in documents():
        if retired_target(route(path)):
            continue
        soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        for anchor in soup.select('a[href]'):
            parsed=urlsplit(anchor['href'])
            if parsed.netloc and parsed.netloc not in {'flashcargoglobal.com','www.flashcargoglobal.com'}:
                continue
            target=retired_target(parsed.path) if parsed.path.startswith('/') else None
            if target:
                anchor['href']=target
        path.write_text(str(soup),encoding='utf-8')
    lines=[]
    for current,target in sorted(targets.items()):
        lines.extend([f'{current} {target} 301',f'{current.rstrip("/")} {target} 301'])
    lines.extend(f'{prefix}* {target} 301' for prefix,target in RETIRED_PREFIXES.items())
    write('_redirects','\n'.join(lines)+'\n')
    out=ROOT/'output/trust-rollout'
    with (out/'retired-routes.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['path','target','delivery','source_url','last_checked'])
        writer.writeheader()
        day=datetime.now(ZoneInfo('America/Toronto')).date().isoformat()
        writer.writerows({'path':current,'target':target,'delivery':'Immediate meta refresh; HTTP 301 requires a capable edge host','source_url':BASE+current,'last_checked':day} for current,target in sorted(targets.items()))


def protect_forms_and_cache_urls():
    from build_audience_rollout import settings
    key=settings()['turnstile_sitekey']
    paths=documents()+[ROOT/'content/interim-inquiry-form.html']
    for path in paths:
        soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        forms=soup.select('[data-request-form]')
        for form in forms:
            action=form.select_one('[name="request_type"]')['value']
            widget=form.select_one('.cf-turnstile')
            button=form.select_one('button[type="submit"]')
            if not widget:
                widget=soup.new_tag('div',attrs={'class':'cf-turnstile wide','data-sitekey':key,'data-action':action,'data-size':'flexible','data-theme':'light'})
                button.insert_before(widget)
            widget['data-request-verification']=''
            if not form.select_one('[data-verification-status]'):
                button.insert_before(BeautifulSoup('<p class="field-note wide" data-verification-status role="status" aria-live="polite" tabindex="-1">Complete the security check before submitting.</p>','html.parser'))
            button['disabled']=''
            if not form.select_one('a[href="/how-payment-works/"]'):
                button.insert_before(BeautifulSoup('<p><a href="/how-payment-works/">How payment works</a></p>','html.parser'))
            if not form.find('noscript'):
                button.insert_before(BeautifulSoup('<noscript><p>Browser scripting is required for the security check. Enable it and reload this page to send a request.</p></noscript>','html.parser'))
        if forms and not soup.select_one('script[src^="https://challenges.cloudflare.com/turnstile/"]'):
            script=soup.new_tag('script',src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit',attrs={'async':'','defer':''})
            (soup.head or soup).append(script)
        if forms and not soup.select_one('script[src*="cargo-global.js"]'):
            (soup.head or soup).append(soup.new_tag('script',src='/cargo-global.js?v=4',defer=''))
        for script in soup.select('script[src*="cargo-global.js"]'):
            script['src']='/cargo-global.js?v=4'
        for css in soup.select('link[href*="cargo-global.css"]'):
            css['href']='/cargo-global.css?v=4'
        if route(path)=='/privacy-policy/':
            for title in soup.find_all('h2'):
                if title.get_text()=='Supplier verification and spam protection':
                    title.string='Request verification and spam protection'
                    first=title.find_next_sibling('p')
                    second=first.find_next_sibling('p')
                    first.string='All buyer, supplier and delivery request forms require Cloudflare Turnstile. The request handler checks the token, approved hostname and matching request action before accepting a request. A timer and a hidden spam-detection field provide additional checks.'
                    second.string='Browser scripting is required for this security check. Disabling scripting, using an old form version or sending an unverified request does not bypass verification. No enquiry is accepted through a separate unverified review form.'
        path.write_text(str(soup),encoding='utf-8')


def apply_trust_content():
    from build_cargo_global import document
    build_lane_guides(document)
    add_process_documents()
    link_guides()
    build_payment_page(document)
    retire_legacy_pages(document)
    protect_forms_and_cache_urls()
