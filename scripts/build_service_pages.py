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
    title = title.replace("Warehousing and White Glove Freight Service", "Warehousing and White Glove Freight")
    branded = f"{title} | Flash Cargo Global"
    if len(branded) <= 60:
        return branded
    return title[:60].rstrip()


def seo_description(description):
    if len(description) < 120:
        description = (
            description
            + " Includes planning checks for documents, cargo details, timing, handling, routing, and receiver handoff."
        )
    if len(description) > 160:
        cut = description[:157]
        space = cut.rfind(" ")
        if space > 120:
            cut = cut[:space]
        description = cut.rstrip(" ,.;:") + "..."
    return description


def render_page(page):
    canonical = f"{BASE_URL}/services/{page['slug']}/"
    meta_title = seo_title(page["title"])
    meta_description = seo_description(page["description"])
    sections = []
    for section in page["sections"]:
        items = "\n".join(f"              <li>{escape(item)}</li>" for item in section["items"])
        sections.append(
            f"""        <section class="guide-panel">
          <h2>{escape(section['heading'])}</h2>
          <ul>
{items}
          </ul>
        </section>"""
        )
    faqs = "\n".join(
        f"          <details><summary>{escape(item['q'])}</summary><p>{escape(item['a'])}</p></details>"
        for item in page["faqs"]
    )
    service_schema = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": page["title"],
        "description": page["description"],
        "provider": {"@type": "Organization", "name": "Flash Cargo Global", "url": BASE_URL + "/", "logo": OG_IMAGE},
        "areaServed": page["areaServed"],
        "serviceType": page["serviceType"],
        "url": canonical,
        "dateModified": date.today().isoformat(),
    }
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "url": canonical,
        "mainEntity": [
            {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
            for item in page["faqs"]
        ],
    }
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Services", "item": BASE_URL + "/#services"},
            {"@type": "ListItem", "position": 3, "name": page["title"], "item": canonical},
        ],
    }
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
    <link rel="stylesheet" href="/styles.css?v=11">
    <script type="application/ld+json">{json_ld(service_schema)}</script>
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
        <p class="kicker">{escape(page['kicker'])}</p>
        <h1>{escape(page['title'])}</h1>
        <p class="lead">{escape(page['lead'])}</p>
        <section class="guide-panel">
          <h2>How this service is planned</h2>
          <p>{escape(page['overview'])}</p>
        </section>
{chr(10).join(sections)}
        <section class="guide-panel">
          <h2>What to include in the inquiry</h2>
          <p>A cleaner freight inquiry should include the business reason for the move, origin, destination, cargo description, quantity, dimensions, weight, value range, requested timing, document status, handling requirements, receiver constraints, and whether the shipment supports production, resale, installation, warranty, replenishment, or customer delivery.</p>
          <p>Those details help separate a simple price request from a shipment that needs route planning, document review, warehouse staging, customs coordination, or receiver-sensitive delivery control. They also help protect the customer promise, sales relationship, production schedule, and receiving plan behind the freight.</p>
        </section>
        <section class="guide-panel faq-list">
          <h2>Service questions</h2>
{faqs}
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


def main():
    data = load_json("content/service_pages.json")
    for page in data["pages"]:
        out = ROOT / "services" / page["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_page(page), encoding="utf-8")


if __name__ == "__main__":
    main()
