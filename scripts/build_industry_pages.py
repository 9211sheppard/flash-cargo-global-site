import json
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
        description += " Includes practical freight planning checks, document context, route questions, and source URLs."
    if len(description) > 160:
        cut = description[:157]
        space = cut.rfind(" ")
        if space > 120:
            cut = cut[:space]
        description = cut.rstrip(" ,.;:") + "..."
    return description


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


def page_shell(title, description, canonical, body, schema_blocks):
    schema_html = "\n".join(f'    <script type="application/ld+json">{json_ld(block)}</script>' for block in schema_blocks)
    meta_title = seo_title(title)
    meta_description = seo_description(description)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(meta_title)}</title>
    <meta name="description" content="{escape(meta_description)}">
    <meta name="robots" content="index, follow">
    <meta name="referrer" content="strict-origin-when-cross-origin">
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
    <link rel="stylesheet" href="/styles.css?v=14">
{schema_html}
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <header class="site-header">
      <nav class="site-nav" aria-label="Primary">
        <a class="wordmark" href="/">FLASH CARGO GLOBAL</a>
        <div class="nav-menu">
          <a href="/about/">About</a>
          <a href="/industries/">Industries</a>
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
      <a href="/industries/">Industry Library</a>
      <a href="/planning/">Planning Library</a>
      <a href="/trust-center/">Trust Center</a>
      <a href="/verify-flash-cargo-global/">Verify</a>
      <a href="/privacy-policy/">Privacy Policy</a>
    </footer>
  </body>
</html>
"""


def build_hub(data):
    cards = []
    for page in data["pages"]:
        cards.append(
            f"""<article>
            <h3><a href="/industries/{escape(page['slug'])}/">{escape(page['title'])}</a></h3>
            <p>{escape(page['description'])}</p>
          </article>"""
        )
    canonical = BASE_URL + "/industries/"
    body = f"""
    <main id="main">
      <section class="knowledge-hero section">
        <p class="kicker">Industry Freight Planning</p>
        <h1>{escape(data['hub']['title'])}</h1>
        <p class="lead">{escape(data['hub']['description'])}</p>
      </section>
      <section class="section knowledge-preview">
        <div class="wide-grid">
          {''.join(cards)}
        </div>
      </section>
    </main>"""
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": data["hub"]["title"],
        "description": data["hub"]["description"],
        "url": canonical,
        "publisher": organization(),
        "hasPart": [{"@type": "Article", "name": page["title"], "url": f"{BASE_URL}/industries/{page['slug']}/"} for page in data["pages"]],
    }
    out = ROOT / "industries" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page_shell(data["hub"]["title"], data["hub"]["description"], canonical, body, [schema]), encoding="utf-8")


def build_pages(data):
    source_names = {item["url"]: item["name"] for item in data["sources"]}
    for page in data["pages"]:
        canonical = f"{BASE_URL}/industries/{page['slug']}/"
        sections = []
        for section in page["sections"]:
            items = "\n".join(f"<li>{escape(item)}</li>" for item in section["items"])
            sections.append(f"""        <section class="guide-panel">
          <h2>{escape(section['heading'])}</h2>
          <ul>{items}</ul>
        </section>""")
        source_links = "\n".join(
            f'<li><a href="{escape(url)}">{escape(source_names.get(url, url))}</a><br><span>source_url: {escape(url)}</span></li>'
            for url in page["source_urls"]
        )
        faq = [
            {
                "q": f"Who is this {page['industry'].lower()} page for?",
                "a": "It is for manufacturers, exporters, buyers, importers, operations teams, and shipment planners researching freight questions before they request help.",
            },
            {
                "q": "Does this page replace customs, legal, or regulatory advice?",
                "a": "No. It helps organize freight facts and source-backed questions so the right responsible parties can review them earlier.",
            },
            {
                "q": "How should a company use this before contacting Flash Cargo Global?",
                "a": "Use it to prepare cargo details, documents, timing, route context, handling needs, receiver constraints, and unanswered questions before using the online inquiry form.",
            },
        ]
        faq_html = "\n".join(f"<details><summary>{escape(item['q'])}</summary><p>{escape(item['a'])}</p></details>" for item in faq)
        body = f"""
    <main id="main">
      <article class="guide-article">
        <p class="kicker">{escape(page['industry'])}</p>
        <h1>{escape(page['title'])}</h1>
        <p class="lead">{escape(page['description'])}</p>
{chr(10).join(sections)}
        <section class="guide-panel faq-list">
          <h2>Industry freight questions</h2>
          {faq_html}
        </section>
        <section class="source-block">
          <h2>Public sources</h2>
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
            "about": page["industry"],
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
                {"@type": "ListItem", "position": 2, "name": "Industries", "item": BASE_URL + "/industries/"},
                {"@type": "ListItem", "position": 3, "name": page["title"], "item": canonical},
            ],
        }
        out = ROOT / "industries" / page["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_shell(page["title"], page["description"], canonical, body, [article, faq_schema, breadcrumb]), encoding="utf-8")


def main():
    data = load_json("content/industry_pages.json")
    build_hub(data)
    build_pages(data)


if __name__ == "__main__":
    main()
