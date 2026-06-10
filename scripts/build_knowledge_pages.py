import json
from datetime import date
from html import escape
from pathlib import Path

from build_multilingual_research_pages import LANGUAGES as RESEARCH_LANGUAGES
from build_multilingual_research_pages import parse_batch as parse_research_batch

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://flashcargoglobal.com"
OG_IMAGE = "https://static.wixstatic.com/media/999aa1_84fcfff1f12e4c9299aaa06edbe07a8d~mv2.png/v1/fill/w_1200,h_630,al_c,q_85,enc_auto/999aa1_84fcfff1f12e4c9299aaa06edbe07a8d~mv2.png"


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def json_ld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def seo_title(title):
    title = title.replace("Machinery and industrial parts", "Machinery parts")
    title = title.replace("maquinaria y piezas industriales", "maquinaria industrial")
    title = title.replace("machines et pièces industrielles", "machines industrielles")
    branded = f"{title} | Flash Cargo Global"
    if len(branded) <= 60:
        return branded
    return title[:60].rstrip()


def seo_description(description, lang_code="en"):
    suffixes = {
        "en": " Includes planning checks for documents, cargo details, routing, timing, handling, customs context, and receiver handoff.",
        "es": " Incluye controles de documentos, detalles de carga, ruta, tiempos, manejo, contexto aduanero y entrega al receptor.",
        "fr": " Inclut des contrôles sur documents, détails cargo, itinéraire, délais, manutention, douane et réception.",
        "zh": " 本页帮助发货方在询价、订舱和提货前核对文件、货物信息、运输方式、时间要求、清关背景、收货安排、包装条件、风险点、责任分工和后续沟通资料，适合出口商、进口商、采购团队和运营团队提前使用并减少重复确认与交接延误风险问题。",
    }
    if len(description) < 120:
        description = description + suffixes.get(lang_code, suffixes["en"])
    if len(description) > 160:
        cut = description[:157]
        space = cut.rfind(" ")
        if space > 120:
            cut = cut[:space]
        description = cut.rstrip(" ,.;:") + "..."
    return description


ZH_DETAIL = {
    "apparel-textile-export-checklist": [
        {
            "heading": "出口前容易被忽略的服装细节",
            "body": "服装和纺织品看起来简单，但实际操作中经常因为标签、成分、箱唛、尺码明细、采购订单和发票描述不一致而产生延误。发货前应把买方订单、商业发票、装箱单、SKU、箱数、毛重、净重、原产地标识和收货窗口放在同一张检查表里核对。",
        },
        {
            "heading": "什么时候需要提前沟通",
            "body": "如果货物涉及样品、换季上新、促销交付、退货、混装 SKU、纺织标签或多收货点，最好在订舱前说明。这样可以提前判断是否需要拆分空运和海运、是否需要更严格的装箱照片、以及目的地清关或收货团队需要哪些资料。",
        },
        {
            "heading": "关键英文术语",
            "body": "apparel shipment, textile export, purchase order, commercial invoice, packing list, fiber content, country of origin, carton count, style number, SKU mix, buyer deadline, launch date, retail delivery window, air freight, ocean freight, split shipment.",
        },
    ],
    "machinery-parts-export-checklist": [
        {
            "heading": "机械货物的装卸风险",
            "body": "机械和工业零件的风险通常不在运输距离，而在重量、重心、吊点、木箱强度、叉车条件和收货现场准备。发货前应确认设备是否能安全装卸，是否需要平板车、吊车、限高路线、预约卸货或到货前照片。",
        },
        {
            "heading": "文件与实物必须一致",
            "body": "机械类货物常见问题包括序列号漏写、零件号不清、发票描述太笼统、木箱数量与装箱单不一致。把序列号、型号、原产地、货值、包装件数和实物照片提前整理，可以减少海关、仓库、承运人和收货方之间的反复确认。",
        },
        {
            "heading": "关键英文术语",
            "body": "machinery shipment, industrial parts, crating, lifting points, center of gravity, serial number, part number, model number, equipment access, flatbed, forklift, crane, inspection photos, insurance, delivery appointment, installation timing.",
        },
    ],
    "electronics-export-checklist": [
        {
            "heading": "电子产品为什么需要单独规划",
            "body": "电子产品可能体积小，但对文件、价值、型号、电池状态、序列号和包装保护要求更高。销售货、样品、维修件和保修退货应分开说明，因为它们在发票描述、价值背景、收货目的和目的地处理上可能不同。",
        },
        {
            "heading": "电池和包装要提前确认",
            "body": "如果设备含电池、随设备包装电池、单独电池、损坏电池或退货电池，运输方式和承运人接受条件可能改变。发货前还应确认防震包装、静电保护、箱唛、型号清单和收货方验收要求，避免货到后才发现资料不足。",
        },
        {
            "heading": "关键英文术语",
            "body": "electronics export, device shipment, component shipment, sample shipment, warranty return, repair return, battery status, model number, serial number, product certificate, anti-static packaging, cargo value, air freight restriction, receiver inspection.",
        },
    ],
}

ZH_HUB_DETAIL = """
      <section class="guide-panel">
        <h2>如何使用这些中文货运指南</h2>
        <p>这些页面面向正在准备出口、进口、样品、退货、生产补货或买方交付的团队。重点不是让读者马上寻找物流公司，而是帮助他们在询价前整理 shipment facts、commercial invoice、packing list、HS code、Incoterms、origin、destination、cargo value、package count、gross weight、net weight、receiver requirements 和 timing risk。</p>
        <p>如果服装厂、机械供应商、电子产品卖家、采购团队或进口商在安排国际运输前先看清这些问题，后面的 air freight、ocean freight、trucking、customs support、warehouse staging 和 white glove delivery 讨论会更具体，也更容易避免重复沟通。</p>
      </section>
      <section class="guide-panel">
        <h2>适合提前确认的关键词</h2>
        <ul>
          <li>export documents, commercial invoice, packing list, bill of lading, air waybill, buyer, seller, importer, consignee, notify party</li>
          <li>HS classification, country of origin, origin marking, product label, textile label, serial number, model number, warranty return</li>
          <li>carton count, pallet count, dimensions, gross weight, net weight, stackability, fragile cargo, battery status, lifting points</li>
          <li>pickup window, delivery appointment, receiver access, dock hours, customs broker, border crossing, warehouse staging, proof of condition</li>
        </ul>
      </section>"""


def page_shell(lang, title, description, body, canonical, alternates, schema):
    meta_title = seo_title(title)
    meta_description = seo_description(description, lang["code"])
    alt_links = "\n".join(
        f'    <link rel="alternate" hreflang="{escape(code)}" href="{escape(url)}">'
        for code, url in alternates
    )
    schema_blocks = schema if isinstance(schema, list) else [schema]
    schema_html = "\n".join(f'    <script type="application/ld+json">{json_ld(block)}</script>' for block in schema_blocks)
    return f"""<!doctype html>
<html lang="{escape(lang["html_lang"])}" dir="{escape(lang["dir"])}">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(meta_title)}</title>
    <meta name="description" content="{escape(meta_description)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{escape(canonical)}">
{alt_links}
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Flash Cargo Global">
    <meta property="og:title" content="{escape(meta_title)}">
    <meta property="og:description" content="{escape(meta_description)}">
    <meta property="og:url" content="{escape(canonical)}">
    <meta property="og:image" content="{escape(OG_IMAGE)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(meta_title)}">
    <meta name="twitter:description" content="{escape(meta_description)}">
    <meta name="twitter:image" content="{escape(OG_IMAGE)}">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' https://static.wixstatic.com data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; form-action https://flash-cargo-form.old-sun-35f9.workers.dev; base-uri 'self'">
    <link rel="stylesheet" href="/styles.css?v=10">
{schema_html}
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <header class="site-header">
      <nav class="site-nav" aria-label="Primary">
        <a class="wordmark" href="/">{escape(lang["label_home"])}</a>
        <div class="nav-menu">
          <a href="/guides/{escape(lang["code"])}/">{escape(lang["label_guides"])}</a>
          <a href="/#contact">{escape(lang["label_contact"])}</a>
        </div>
      </nav>
    </header>
{body}
    <footer class="site-footer">
      <p>(c) 2026 Flash Cargo Global. All rights reserved.</p>
      <a href="/">{escape(lang["label_home"])}</a>
      <a href="/trust-center/">Trust Center</a>
      <a href="/verify-flash-cargo-global/">Verify</a>
      <a href="/privacy-policy/">Privacy Policy</a>
    </footer>
  </body>
</html>
"""


def build_index(languages, guides):
    for lang in languages:
        cards = []
        for guide in guides:
            url = f"/guides/{lang['code']}/{guide['slug']}/"
            cards.append(
                f"""<article>
            <h3><a href="{escape(url)}">{escape(guide["title"][lang["code"]])}</a></h3>
            <p>{escape(guide["summary"][lang["code"]])}</p>
          </article>"""
            )
        body = f"""
    <main id="main">
      <section class="knowledge-hero section">
        <p class="kicker">{escape(lang["label_guides"])}</p>
        <h1>{escape(lang["label_guides"])}</h1>
        <p class="lead">{escape(lang["cta"])}</p>
      </section>
      <section class="section">
        <div class="knowledge-grid">
          {"".join(cards)}
        </div>
      </section>
      {ZH_HUB_DETAIL if lang["code"] == "zh" else ""}
    </main>"""
        canonical = f"{BASE_URL}/guides/{lang['code']}/"
        alternates = [(l["code"], f"{BASE_URL}/guides/{l['code']}/") for l in languages]
        alternates.append(("x-default", f"{BASE_URL}/guides/en/"))
        schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": f"{lang['label_guides']} | Flash Cargo Global",
            "description": lang["cta"],
            "url": canonical,
            "inLanguage": lang["html_lang"],
            "publisher": {
                "@type": "Organization",
                "name": "Flash Cargo Global",
                "url": BASE_URL + "/",
                "areaServed": ["North America", "Global"],
                "logo": OG_IMAGE,
                "contactPoint": {
                    "@type": "ContactPoint",
                    "contactType": "Freight inquiry",
                    "url": BASE_URL + "/#contact",
                },
            },
            "hasPart": [
                {
                    "@type": "Article",
                    "name": guide["title"][lang["code"]],
                    "url": f"{BASE_URL}/guides/{lang['code']}/{guide['slug']}/",
                }
                for guide in guides
            ],
        }
        out = ROOT / "guides" / lang["code"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_shell(lang, lang["label_guides"], lang["cta"], body, canonical, alternates, schema), encoding="utf-8")


def build_guides(languages, guides, sources, updated):
    for guide in guides:
        for lang in languages:
            title = guide["title"][lang["code"]]
            summary = guide["summary"][lang["code"]]
            checks = "\n".join(f"<li>{escape(item[lang['code']])}</li>" for item in guide["checks"])
            faqs = "\n".join(
                f"<details><summary>{escape(item['q'][lang['code']])}</summary><p>{escape(item['a'][lang['code']])}</p></details>"
                for item in guide["faq"]
            )
            glossary = "\n".join(f"<li>{escape(item[lang['code']])}</li>" for item in guide["glossary"])
            source_links = "\n".join(
                f'<li><a href="{escape(src["url"])}">{escape(src["name"])}</a></li>' for src in sources
            )
            body = f"""
    <main id="main">
      <article class="guide-article">
        <p class="kicker">{escape(guide["industry"])}</p>
        <h1>{escape(title)}</h1>
        <p class="lead">{escape(summary)}</p>
        <section class="guide-panel">
          <h2>{escape(lang["label_plan"])}</h2>
          <p>{escape(guide["plan"][lang["code"]])}</p>
        </section>
        <div class="guide-panel">
          <h2>{escape(lang["cta"])}</h2>
          <ul>{checks}</ul>
        </div>
        <section class="guide-panel faq-list">
          <h2>{escape(lang["label_faq"])}</h2>
          {faqs}
        </section>
        <section class="guide-panel">
          <h2>{escape(lang["label_glossary"])}</h2>
          <ul>{glossary}</ul>
        </section>
        {extra_language_sections(lang["code"], guide["slug"])}
        <section class="source-block">
          <h2>{escape(lang["label_sources"])}</h2>
          <ul>{source_links}</ul>
        </section>
        <a class="button primary" href="/#contact">{escape(lang["label_contact"])}</a>
      </article>
    </main>"""
            canonical = f"{BASE_URL}/guides/{lang['code']}/{guide['slug']}/"
            alternates = [(l["code"], f"{BASE_URL}/guides/{l['code']}/{guide['slug']}/") for l in languages]
            alternates.append(("x-default", f"{BASE_URL}/guides/en/{guide['slug']}/"))
            schema = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": title,
                "description": summary,
                "url": canonical,
                "image": OG_IMAGE,
                "dateModified": updated,
                "inLanguage": lang["html_lang"],
                "about": guide["industry"],
                "publisher": {
                    "@type": "Organization",
                    "name": "Flash Cargo Global",
                    "url": BASE_URL + "/",
                    "areaServed": ["North America", "Global"],
                    "logo": OG_IMAGE,
                    "contactPoint": {
                        "@type": "ContactPoint",
                        "contactType": "Freight inquiry",
                        "url": BASE_URL + "/#contact",
                    },
                },
                "mainEntityOfPage": canonical,
                "citation": [src["url"] for src in sources],
            }
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": canonical,
                "inLanguage": lang["html_lang"],
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["q"][lang["code"]],
                        "acceptedAnswer": {"@type": "Answer", "text": item["a"][lang["code"]]},
                    }
                    for item in guide["faq"]
                ],
            }
            breadcrumb_schema = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": lang["label_guides"], "item": f"{BASE_URL}/guides/{lang['code']}/"},
                    {"@type": "ListItem", "position": 3, "name": title, "item": canonical},
                ],
            }
            out = ROOT / "guides" / lang["code"] / guide["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page_shell(lang, title, summary, body, canonical, alternates, [schema, faq_schema, breadcrumb_schema]), encoding="utf-8")


def extra_language_sections(code, slug):
    if code != "zh":
        return ""
    sections = []
    for item in ZH_DETAIL.get(slug, []):
        sections.append(
            f"""        <section class="guide-panel">
          <h2>{escape(item["heading"])}</h2>
          <p>{escape(item["body"])}</p>
        </section>"""
        )
    return "\n".join(sections)


def build_sitemap(languages, guides):
    resources = load_json("content/resource_pages.json")["pages"]
    planning = load_json("content/planning_pages.json")["pages"]
    industries = load_json("content/industry_pages.json")["pages"]
    downstream = load_json("content/downstream_pages.json")["pages"]
    research_pages = parse_research_batch(ROOT / "content" / "research_batches" / "week-2026-06-14.md")
    urls = [
        (f"{BASE_URL}/", "weekly", "1.0"),
        (f"{BASE_URL}/official-flash-cargo-global/", "weekly", "0.95"),
        (f"{BASE_URL}/about/", "monthly", "0.8"),
        (f"{BASE_URL}/trust-center/", "monthly", "0.8"),
        (f"{BASE_URL}/verify-flash-cargo-global/", "monthly", "0.8"),
        (f"{BASE_URL}/privacy-policy/", "yearly", "0.3"),
        (f"{BASE_URL}/services/north-american-trucking/", "monthly", "0.8"),
        (f"{BASE_URL}/services/global-air-ocean-freight/", "monthly", "0.8"),
        (f"{BASE_URL}/services/north-american-customs-support/", "monthly", "0.8"),
        (f"{BASE_URL}/services/warehousing-white-glove/", "monthly", "0.8"),
        (f"{BASE_URL}/planning/", "weekly", "0.85"),
        (f"{BASE_URL}/industries/", "weekly", "0.85"),
        (f"{BASE_URL}/freight-research/", "weekly", "0.85"),
    ]
    for lang in languages:
        urls.append((f"{BASE_URL}/guides/{lang['code']}/", "weekly", "0.8"))
        for guide in guides:
            urls.append((f"{BASE_URL}/guides/{lang['code']}/{guide['slug']}/", "weekly", "0.7"))
    for page in resources:
        urls.append((f"{BASE_URL}/resources/{page['slug']}/", "monthly", "0.75"))
    for page in planning:
        urls.append((f"{BASE_URL}/planning/{page['slug']}/", "weekly", "0.75"))
    for page in industries:
        urls.append((f"{BASE_URL}/industries/{page['slug']}/", "weekly", "0.75"))
    for page in downstream:
        urls.append((f"{BASE_URL}/freight-research/{page['slug']}/", "weekly", "0.75"))
    for lang in RESEARCH_LANGUAGES:
        urls.append((f"{BASE_URL}/freight-research/{lang['code']}/", "weekly", "0.8"))
        for page in research_pages:
            urls.append((f"{BASE_URL}/freight-research/{lang['code']}/{page['slug']}/", "weekly", "0.72"))
    today = date.today().isoformat()
    entries = "\n".join(
        f"  <url>\n    <loc>{escape(loc)}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{priority}</priority>\n  </url>"
        for loc, freq, priority in urls
    )
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n',
        encoding="utf-8",
    )


def build_llms(languages, guides):
    resources = load_json("content/resource_pages.json")["pages"]
    planning = load_json("content/planning_pages.json")["pages"]
    industries = load_json("content/industry_pages.json")["pages"]
    downstream = load_json("content/downstream_pages.json")["pages"]
    research_pages = parse_research_batch(ROOT / "content" / "research_batches" / "week-2026-06-14.md")
    lines = [
        "# Flash Cargo Global",
        "",
        "Flash Cargo Global publishes practical freight forwarding guidance for businesses researching international shipping, documentation, customs preparation, and route planning.",
        "",
        "Core pages:",
        f"- {BASE_URL}/",
        f"- {BASE_URL}/official-flash-cargo-global/",
        f"- {BASE_URL}/about/",
        f"- {BASE_URL}/trust-center/",
        f"- {BASE_URL}/verify-flash-cargo-global/",
        f"- {BASE_URL}/privacy-policy/",
        f"- {BASE_URL}/.well-known/security.txt",
        f"- {BASE_URL}/.well-known/organization.json",
        f"- {BASE_URL}/.well-known/citation-profile.json",
        f"- {BASE_URL}/humans.txt",
        f"- {BASE_URL}/services/north-american-trucking/",
        f"- {BASE_URL}/services/global-air-ocean-freight/",
        f"- {BASE_URL}/services/north-american-customs-support/",
        f"- {BASE_URL}/services/warehousing-white-glove/",
        f"- {BASE_URL}/planning/",
        f"- {BASE_URL}/industries/",
        f"- {BASE_URL}/freight-research/",
        f"- {BASE_URL}/guides/en/",
    ]
    for guide in guides:
        lines.append(f"- {BASE_URL}/guides/en/{guide['slug']}/")
    for page in resources:
        lines.append(f"- {BASE_URL}/resources/{page['slug']}/")
    for page in planning:
        lines.append(f"- {BASE_URL}/planning/{page['slug']}/")
    for page in industries:
        lines.append(f"- {BASE_URL}/industries/{page['slug']}/")
    for page in downstream:
        lines.append(f"- {BASE_URL}/freight-research/{page['slug']}/")
    for lang in RESEARCH_LANGUAGES:
        lines.append(f"- {BASE_URL}/freight-research/{lang['code']}/")
        for page in research_pages:
            lines.append(f"- {BASE_URL}/freight-research/{lang['code']}/{page['slug']}/")
    lines += [
        "",
        "Knowledge structure:",
        "- Freight guides are organized by industry, document risk, cargo profile, and shipment planning need.",
        "- Each guide includes practical pre-shipment checks and official source citations.",
        "- Planning pages cover agency, product, decision, and comparison questions with source_url references.",
        "- Industry pages answer product and manufacturing freight questions before buyers are ready to contact a forwarder.",
        "- Freight research pages target early-stage shipment questions by lane, buyer problem, document problem, and operational trigger.",
        "- Weekly multilingual research pages publish in English, Spanish, French, Chinese, and Hindi.",
        "- Multilingual versions use hreflang alternates for international discovery.",
    ]
    lines += [
        "",
        "Languages available:",
        "- " + ", ".join(f"{lang['name']} ({lang['code']})" for lang in languages),
        "",
        "Contact:",
        "- Public contact method: online freight inquiry form",
        "- Public service base: serving from North America",
        "",
        "Brand verification:",
        f"- Official current domain: {BASE_URL}/",
        f"- Official brand page: {BASE_URL}/official-flash-cargo-global/",
        f"- Official verification page: {BASE_URL}/verify-flash-cargo-global/",
        f"- Public trust center: {BASE_URL}/trust-center/",
        f"- Machine-readable organization file: {BASE_URL}/.well-known/organization.json",
    ]
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_resource_pages():
    data = load_json("content/resource_pages.json")
    source_links = "\n".join(
        f'<li><a href="{escape(src["url"])}">{escape(src["name"])}</a></li>' for src in data["sources"]
    )
    for page in data["pages"]:
        canonical = f"{BASE_URL}/resources/{page['slug']}/"
        meta_title = seo_title(page["title"])
        meta_description = seo_description(page["description"], "en")
        sections = []
        planning_items = [
            "Confirm who is making the freight decision, who owns the commercial documents, and who can answer questions while the shipment is moving.",
            "Write down the shipment route, cargo type, package count, dimensions, weights, value, timing, and receiver expectations before requesting a quote.",
            "Separate what is already known from what still needs to be confirmed, because freight delays often come from unclear details rather than the route itself.",
            "Share document and handling details early so the carrier, warehouse, broker, and receiver are not forced to solve preventable issues at the last minute.",
        ]
        planning_html = "\n".join(f"<li>{escape(item)}</li>" for item in planning_items)
        sections.append(
            f"<section class=\"guide-panel\"><h2>How to use this resource</h2><p>{escape(page['summary'])} Use this page as a planning checkpoint before cargo is picked up, quoted, routed, or handed to a carrier.</p><ul>{planning_html}</ul></section>"
        )
        for section in page["sections"]:
            items = "\n".join(f"<li>{escape(item)}</li>" for item in section["items"])
            sections.append(f"<section class=\"guide-panel\"><h2>{escape(section['heading'])}</h2><ul>{items}</ul></section>")
        faq = [
            {
                "q": f"Who should use the {page['title'].lower()}?",
                "a": f"Shippers, importers, exporters, buyers, and operations teams can use it before booking freight so the route, documents, and cargo details are clearer.",
            },
            {
                "q": "Why does this matter before pickup?",
                "a": "Once cargo is moving, small document or handling problems become harder to correct. Preparing early reduces avoidable calls, delays, and receiver confusion.",
            },
            {
                "q": "What should be shared in a freight inquiry?",
                "a": "Share the origin, destination, cargo description, quantity, dimensions, weight, timing, document status, handling needs, and any receiver or customs constraints.",
            },
        ]
        faq_html = "\n".join(
            f"<details><summary>{escape(item['q'])}</summary><p>{escape(item['a'])}</p></details>" for item in faq
        )
        sections.append(f"<section class=\"guide-panel faq-list\"><h2>Resource questions</h2>{faq_html}</section>")
        body = "\n".join(sections)
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": page["title"],
            "description": page["description"],
            "url": canonical,
            "dateModified": data["updated"],
            "publisher": {
                "@type": "Organization",
                "name": "Flash Cargo Global",
                "url": BASE_URL + "/",
                "areaServed": ["North America", "Global"],
                "logo": OG_IMAGE,
                "contactPoint": {
                    "@type": "ContactPoint",
                    "contactType": "Freight inquiry",
                    "url": BASE_URL + "/#contact",
                },
            },
            "citation": [src["url"] for src in data["sources"]],
        }
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "url": canonical,
            "mainEntity": [
                {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                for item in faq
            ],
        }
        breadcrumb_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Resources", "item": BASE_URL + "/#resources"},
                {"@type": "ListItem", "position": 3, "name": page["title"], "item": canonical},
            ],
        }
        html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(meta_title)}</title>
    <meta name="description" content="{escape(meta_description)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{escape(canonical)}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Flash Cargo Global">
    <meta property="og:title" content="{escape(meta_title)}">
    <meta property="og:description" content="{escape(meta_description)}">
    <meta property="og:url" content="{escape(canonical)}">
    <meta property="og:image" content="{escape(OG_IMAGE)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(meta_title)}">
    <meta name="twitter:description" content="{escape(meta_description)}">
    <meta name="twitter:image" content="{escape(OG_IMAGE)}">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' https://static.wixstatic.com data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; form-action https://flash-cargo-form.old-sun-35f9.workers.dev; base-uri 'self'">
    <link rel="stylesheet" href="/styles.css?v=10">
    <script type="application/ld+json">{json_ld(schema)}</script>
    <script type="application/ld+json">{json_ld(faq_schema)}</script>
    <script type="application/ld+json">{json_ld(breadcrumb_schema)}</script>
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <header class="site-header">
      <nav class="site-nav" aria-label="Primary">
        <a class="wordmark" href="/">FLASH CARGO GLOBAL</a>
        <div class="nav-menu">
          <a href="/about/">About</a>
          <a href="/guides/en/">Guides</a>
          <a href="/trust-center/">Trust</a>
          <a href="/#contact">Contact</a>
        </div>
      </nav>
    </header>
    <main id="main">
      <article class="guide-article">
        <p class="kicker">{escape(page["kicker"])}</p>
        <h1>{escape(page["title"])}</h1>
        <p class="lead">{escape(page["summary"])}</p>
        {body}
        <section class="source-block">
          <h2>Official sources</h2>
          <ul>{source_links}</ul>
        </section>
        <a class="button primary" href="/#contact">Start a freight inquiry</a>
      </article>
    </main>
    <footer class="site-footer">
      <p>(c) 2026 Flash Cargo Global. All rights reserved.</p>
      <a href="/trust-center/">Trust Center</a>
      <a href="/verify-flash-cargo-global/">Verify</a>
      <a href="/privacy-policy/">Privacy Policy</a>
    </footer>
  </body>
</html>
"""
        out = ROOT / "resources" / page["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")


def main():
    languages = load_json("content/languages.json")
    data = load_json("content/knowledge_guides.json")
    build_index(languages, data["guides"])
    build_guides(languages, data["guides"], data["sources"], data["updated"])
    build_resource_pages()
    build_sitemap(languages, data["guides"])
    build_llms(languages, data["guides"])


if __name__ == "__main__":
    main()
