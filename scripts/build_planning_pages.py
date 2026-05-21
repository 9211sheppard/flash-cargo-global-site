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


def seo_title(title):
    branded = f"{title} | Flash Cargo Global"
    return branded if len(branded) <= 60 else title[:60].rstrip()


def seo_description(description):
    if len(description) < 120:
        description += " Includes sourced planning notes for importers, exporters, manufacturers, buyers, brokers, and freight teams."
    if len(description) > 160:
        cut = description[:157]
        space = cut.rfind(" ")
        if space > 120:
            cut = cut[:space]
        description = cut.rstrip(" ,.;:") + "..."
    return description


def source_lookup(data):
    return {item["url"]: item["name"] for item in data["sources"]}


def page_shell(title, description, canonical, body, schema_blocks):
    meta_title = seo_title(title)
    meta_description = seo_description(description)
    schema_html = "\n".join(f'    <script type="application/ld+json">{json_ld(block)}</script>' for block in schema_blocks)
    return f"""<!doctype html>
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
    <link rel="stylesheet" href="/styles.css?v=13">
{schema_html}
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <header class="site-header">
      <nav class="site-nav" aria-label="Primary">
        <a class="wordmark" href="/">FLASH CARGO GLOBAL</a>
        <div class="nav-menu">
          <a href="/about/">About</a>
          <a href="/planning/">Planning</a>
          <a href="/guides/en/">Guides</a>
          <a href="/trust-center/">Trust</a>
          <a href="/#contact">Contact</a>
        </div>
      </nav>
    </header>
{body}
    <footer class="site-footer">
      <p>(c) 2026 Flash Cargo Global. All rights reserved.</p>
      <a href="/planning/">Planning Library</a>
      <a href="/trust-center/">Trust Center</a>
      <a href="/verify-flash-cargo-global/">Verify</a>
      <a href="/privacy-policy/">Privacy Policy</a>
    </footer>
  </body>
</html>
"""


def organization():
    return {
        "@type": "Organization",
        "@id": BASE_URL + "/#organization",
        "name": "Flash Cargo Global",
        "url": BASE_URL + "/",
        "logo": OG_IMAGE,
        "areaServed": ["North America", "Global"],
        "contactPoint": {"@type": "ContactPoint", "contactType": "Freight inquiry", "url": BASE_URL + "/#contact"},
    }


def build_hub(data):
    groups = {}
    for page in data["pages"]:
        groups.setdefault(page["category"], []).append(page)
    sections = []
    for category, pages in groups.items():
        cards = []
        for page in pages:
            cards.append(
                f"""<article>
            <h3><a href="/planning/{escape(page['slug'])}/">{escape(page['title'])}</a></h3>
            <p>{escape(page['description'])}</p>
          </article>"""
            )
        sections.append(
            f"""      <section class="section knowledge-preview">
        <div class="section-title">
          <p class="kicker">{escape(category)}</p>
          <h2>{escape(category)} pages for freight decisions.</h2>
        </div>
        <div class="wide-grid">
          {''.join(cards)}
        </div>
      </section>"""
        )
    canonical = BASE_URL + "/planning/"
    body = f"""
    <main id="main">
      <section class="knowledge-hero section">
        <p class="kicker">Freight Planning Library</p>
        <h1>{escape(data['hub']['title'])}</h1>
        <p class="lead">{escape(data['hub']['description'])}</p>
      </section>
{''.join(sections)}
    </main>"""
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": data["hub"]["title"],
        "description": data["hub"]["description"],
        "url": canonical,
        "publisher": organization(),
        "hasPart": [{"@type": "Article", "name": page["title"], "url": f"{BASE_URL}/planning/{page['slug']}/"} for page in data["pages"]],
    }
    out = ROOT / "planning" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page_shell(data["hub"]["title"], data["hub"]["description"], canonical, body, [schema]), encoding="utf-8")


def build_pages(data):
    sources = source_lookup(data)
    for page in data["pages"]:
        canonical = f"{BASE_URL}/planning/{page['slug']}/"
        section_html = []
        for section in page["sections"]:
            items = "\n".join(f"<li>{escape(item)}</li>" for item in section["items"])
            section_html.append(f"""        <section class="guide-panel">
          <h2>{escape(section['heading'])}</h2>
          <ul>{items}</ul>
        </section>""")
        source_links = "\n".join(
            f'<li><a href="{escape(url)}">{escape(sources.get(url, url))}</a><br><span>source_url: {escape(url)}</span></li>'
            for url in page["source_urls"]
        )
        faq = [
            {
                "q": f"Who should use this {page['category'].lower()}?",
                "a": "Importers, exporters, manufacturers, buyers, and operations teams can use it before quoting, booking, routing, or handing cargo to a carrier.",
            },
            {
                "q": "Does this replace a broker, agency, or compliance professional?",
                "a": "No. It is a freight planning aid that helps teams organize the facts and questions they should confirm with the right responsible party.",
            },
        ]
        faq_html = "\n".join(f"<details><summary>{escape(item['q'])}</summary><p>{escape(item['a'])}</p></details>" for item in faq)
        body = f"""
    <main id="main">
      <article class="guide-article">
        <p class="kicker">{escape(page['category'])}</p>
        <h1>{escape(page['title'])}</h1>
        <p class="lead">{escape(page['description'])}</p>
{chr(10).join(section_html)}
        <section class="guide-panel faq-list">
          <h2>Planning questions</h2>
          {faq_html}
        </section>
        <section class="source-block">
          <h2>Official sources</h2>
          <ul>{source_links}</ul>
        </section>
        <a class="button primary" href="/#contact">Start a freight inquiry</a>
      </article>
    </main>"""
        article = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": page["title"],
            "description": page["description"],
            "url": canonical,
            "dateModified": data["updated"],
            "publisher": organization(),
            "about": page["category"],
            "citation": page["source_urls"],
        }
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "url": canonical,
            "mainEntity": [{"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}} for item in faq],
        }
        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Planning", "item": BASE_URL + "/planning/"},
                {"@type": "ListItem", "position": 3, "name": page["title"], "item": canonical},
            ],
        }
        out = ROOT / "planning" / page["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_shell(page["title"], page["description"], canonical, body, [article, faq_schema, breadcrumb]), encoding="utf-8")


def main():
    data = load_json("content/planning_pages.json")
    build_hub(data)
    build_pages(data)


if __name__ == "__main__":
    main()
