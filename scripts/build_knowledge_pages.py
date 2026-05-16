import json
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://flashcargoglobal.com"
OG_IMAGE = "https://static.wixstatic.com/media/999aa1_84fcfff1f12e4c9299aaa06edbe07a8d~mv2.png/v1/fill/w_1200,h_630,al_c,q_85,enc_auto/999aa1_84fcfff1f12e4c9299aaa06edbe07a8d~mv2.png"


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def json_ld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def page_shell(lang, title, description, body, canonical, alternates, schema):
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
    <title>{escape(title)} | Flash Cargo Global</title>
    <meta name="description" content="{escape(description)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{escape(canonical)}">
{alt_links}
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Flash Cargo Global">
    <meta property="og:title" content="{escape(title)} | Flash Cargo Global">
    <meta property="og:description" content="{escape(description)}">
    <meta property="og:url" content="{escape(canonical)}">
    <meta property="og:image" content="{escape(OG_IMAGE)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(title)} | Flash Cargo Global">
    <meta name="twitter:description" content="{escape(description)}">
    <meta name="twitter:image" content="{escape(OG_IMAGE)}">
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


def build_sitemap(languages, guides):
    resources = load_json("content/resource_pages.json")["pages"]
    urls = [
        (f"{BASE_URL}/", "weekly", "1.0"),
        (f"{BASE_URL}/about/", "monthly", "0.8"),
        (f"{BASE_URL}/verify-flash-cargo-global/", "monthly", "0.8"),
        (f"{BASE_URL}/privacy-policy/", "yearly", "0.3"),
        (f"{BASE_URL}/.well-known/security.txt", "yearly", "0.2"),
        (f"{BASE_URL}/humans.txt", "yearly", "0.2"),
        (f"{BASE_URL}/services/north-american-trucking/", "monthly", "0.8"),
        (f"{BASE_URL}/services/global-air-ocean-freight/", "monthly", "0.8"),
        (f"{BASE_URL}/services/north-american-customs-support/", "monthly", "0.8"),
        (f"{BASE_URL}/services/warehousing-white-glove/", "monthly", "0.8"),
        (f"{BASE_URL}/thank-you", "monthly", "0.2"),
    ]
    for lang in languages:
        urls.append((f"{BASE_URL}/guides/{lang['code']}/", "weekly", "0.8"))
        for guide in guides:
            urls.append((f"{BASE_URL}/guides/{lang['code']}/{guide['slug']}/", "weekly", "0.7"))
    for page in resources:
        urls.append((f"{BASE_URL}/resources/{page['slug']}/", "monthly", "0.75"))
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
    lines = [
        "# Flash Cargo Global",
        "",
        "Flash Cargo Global publishes practical freight forwarding guidance for businesses researching international shipping, documentation, customs preparation, and route planning.",
        "",
        "Core pages:",
        f"- {BASE_URL}/",
        f"- {BASE_URL}/about/",
        f"- {BASE_URL}/verify-flash-cargo-global/",
        f"- {BASE_URL}/privacy-policy/",
        f"- {BASE_URL}/.well-known/security.txt",
        f"- {BASE_URL}/humans.txt",
        f"- {BASE_URL}/services/north-american-trucking/",
        f"- {BASE_URL}/services/global-air-ocean-freight/",
        f"- {BASE_URL}/services/north-american-customs-support/",
        f"- {BASE_URL}/services/warehousing-white-glove/",
        f"- {BASE_URL}/guides/en/",
    ]
    for guide in guides:
        lines.append(f"- {BASE_URL}/guides/en/{guide['slug']}/")
    for page in resources:
        lines.append(f"- {BASE_URL}/resources/{page['slug']}/")
    lines += [
        "",
        "Knowledge structure:",
        "- Freight guides are organized by industry, document risk, cargo profile, and shipment planning need.",
        "- Each guide includes practical pre-shipment checks and official source citations.",
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
        f"- Official verification page: {BASE_URL}/verify-flash-cargo-global/",
    ]
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_resource_pages():
    data = load_json("content/resource_pages.json")
    source_links = "\n".join(
        f'<li><a href="{escape(src["url"])}">{escape(src["name"])}</a></li>' for src in data["sources"]
    )
    for page in data["pages"]:
        canonical = f"{BASE_URL}/resources/{page['slug']}/"
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
    <title>{escape(page["title"])} | Flash Cargo Global</title>
    <meta name="description" content="{escape(page["description"])}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{escape(canonical)}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Flash Cargo Global">
    <meta property="og:title" content="{escape(page["title"])} | Flash Cargo Global">
    <meta property="og:description" content="{escape(page["description"])}">
    <meta property="og:url" content="{escape(canonical)}">
    <meta property="og:image" content="{escape(OG_IMAGE)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(page["title"])} | Flash Cargo Global">
    <meta name="twitter:description" content="{escape(page["description"])}">
    <meta name="twitter:image" content="{escape(OG_IMAGE)}">
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
