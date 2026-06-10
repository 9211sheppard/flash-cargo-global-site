import json
import re
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://flashcargoglobal.com"
OG_IMAGE = "https://static.wixstatic.com/media/999aa1_84fcfff1f12e4c9299aaa06edbe07a8d~mv2.png/v1/fill/w_1200,h_630,al_c,q_85,enc_auto/999aa1_84fcfff1f12e4c9299aaa06edbe07a8d~mv2.png"

LANGUAGES = [
    {"code": "en", "name": "English", "html_lang": "en", "label": "English Freight Research"},
    {"code": "es", "name": "Español", "html_lang": "es", "label": "Investigación de carga"},
    {"code": "fr", "name": "Français", "html_lang": "fr", "label": "Recherche fret"},
    {"code": "zh", "name": "中文", "html_lang": "zh-Hans", "label": "货运研究"},
    {"code": "hi", "name": "Hindi", "html_lang": "hi", "label": "Freight Research Hindi"},
]

LANGUAGE_HEADINGS = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "Chinese": "zh",
    "Hindi": "hi",
}

DAY_SLUGS = {
    1: "india-apparel-manufacturer-export-to-north-america",
    2: "italy-fashion-samples-to-japan",
    3: "china-electronics-battery-goods-to-canada",
    4: "mexico-automotive-parts-to-us-production",
    5: "turkey-furniture-supplier-to-us-hotel-project",
    6: "vietnam-footwear-manufacturer-to-european-retailer",
    7: "brazil-food-ingredient-exporter-to-north-america",
}


def json_ld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def seo_title(title):
    branded = f"{title} | Flash Cargo Global"
    return branded if len(branded) <= 60 else title[:60].rstrip()


def seo_description(description):
    if len(description) < 120:
        description += " Includes shipment facts, document checks, receiver context, and source URLs."
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


def parse_batch(path):
    text = path.read_text(encoding="utf-8")
    hindi_overrides = json.loads((ROOT / "content" / "research_batches" / "hindi_week_2026_06_14.json").read_text(encoding="utf-8"))
    blocks = re.split(r"(?m)^## Day (\d+): (.+)$", text)[1:]
    pages = []
    for index in range(0, len(blocks), 3):
        day = int(blocks[index])
        topic = blocks[index + 1].strip()
        body = blocks[index + 2]
        source_match = re.search(r"Source URLs:\n((?:- .+\n)+)", body)
        sources = [line[2:].strip() for line in source_match.group(1).splitlines()] if source_match else []
        lang_blocks = re.split(r"(?m)^### (English|Spanish|French|Chinese|Hindi)\s*$", body)[1:]
        translations = {}
        for lang_index in range(0, len(lang_blocks), 2):
            label = lang_blocks[lang_index]
            code = LANGUAGE_HEADINGS[label]
            content = lang_blocks[lang_index + 1].strip()
            title = re.search(r"(?m)^Title: (.+)$", content).group(1).strip()
            meta = re.search(r"(?m)^Meta: (.+)$", content).group(1).strip()
            draft = content.split("Draft:", 1)[1].strip()
            translations[code] = {"title": title, "meta": meta, "draft": draft}
        if str(day) in hindi_overrides:
            translations["hi"] = hindi_overrides[str(day)]
        pages.append({"day": day, "topic": topic, "slug": DAY_SLUGS[day], "sources": sources, "translations": translations})
    return pages


def split_draft(draft):
    lines = draft.splitlines()
    html = []
    bullets = []
    for raw in lines:
        line = raw.strip()
        if not line:
            if bullets:
                html.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in bullets) + "</ul>")
                bullets = []
            continue
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.endswith(":") and len(line) < 80:
            if bullets:
                html.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in bullets) + "</ul>")
                bullets = []
            html.append(f"<h2>{escape(line[:-1])}</h2>")
        else:
            if bullets:
                html.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in bullets) + "</ul>")
                bullets = []
            html.append(f"<p>{escape(line)}</p>")
    if bullets:
        html.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in bullets) + "</ul>")
    return "\n".join(html)


def shell(lang, title, description, canonical, alternates, body, schemas):
    alternates_html = "\n".join(
        f'    <link rel="alternate" hreflang="{escape(code)}" href="{escape(url)}">' for code, url in alternates
    )
    schema_html = "\n".join(f'    <script type="application/ld+json">{json_ld(schema)}</script>' for schema in schemas)
    meta_title = seo_title(title)
    meta_description = seo_description(description)
    return f"""<!doctype html>
<html lang="{escape(lang['html_lang'])}">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(meta_title)}</title>
    <meta name="description" content="{escape(meta_description)}">
    <meta name="robots" content="index, follow">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    <link rel="canonical" href="{escape(canonical)}">
{alternates_html}
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
    <link rel="stylesheet" href="/styles.css?v=16">
{schema_html}
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <header class="site-header">
      <nav class="site-nav" aria-label="Primary">
        <a class="wordmark" href="/">FLASH CARGO GLOBAL</a>
        <div class="nav-menu">
          <a href="/freight-research/">Research</a>
          <a href="/industries/">Industries</a>
          <a href="/planning/">Planning</a>
          <a href="/trust-center/">Trust</a>
          <a href="/#contact">Contact</a>
        </div>
      </nav>
    </header>
{body}
    <footer class="site-footer">
      <p>(c) 2026 Flash Cargo Global. All rights reserved.</p>
      <a href="/freight-research/">Freight Research Library</a>
      <a href="/trust-center/">Trust Center</a>
      <a href="/verify-flash-cargo-global/">Verify</a>
      <a href="/privacy-policy/">Privacy Policy</a>
    </footer>
  </body>
</html>
"""


def build_hubs(pages):
    for lang in LANGUAGES:
        cards = []
        for page in pages:
            item = page["translations"][lang["code"]]
            cards.append(
                f"""<article>
            <h3><a href="/freight-research/{lang['code']}/{page['slug']}/">{escape(item['title'])}</a></h3>
            <p>{escape(item['meta'])}</p>
          </article>"""
            )
        canonical = f"{BASE_URL}/freight-research/{lang['code']}/"
        alternates = [(l["code"], f"{BASE_URL}/freight-research/{l['code']}/") for l in LANGUAGES]
        alternates.append(("x-default", f"{BASE_URL}/freight-research/en/"))
        body = f"""
    <main id="main">
      <section class="knowledge-hero section">
        <p class="kicker">Freight Research</p>
        <h1>{escape(lang['label'])}</h1>
        <p class="lead">Practical freight planning pages for manufacturers, buyers, importers, and operators researching shipment problems before they submit a freight inquiry.</p>
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
            "name": lang["label"],
            "url": canonical,
            "inLanguage": lang["html_lang"],
            "publisher": organization(),
            "hasPart": [
                {"@type": "Article", "name": p["translations"][lang["code"]]["title"], "url": f"{BASE_URL}/freight-research/{lang['code']}/{p['slug']}/"}
                for p in pages
            ],
        }
        out = ROOT / "freight-research" / lang["code"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(shell(lang, lang["label"], "Multilingual freight research for practical shipment planning.", canonical, alternates, body, [schema]), encoding="utf-8")


def build_pages(pages):
    for page in pages:
        for lang in LANGUAGES:
            item = page["translations"][lang["code"]]
            canonical = f"{BASE_URL}/freight-research/{lang['code']}/{page['slug']}/"
            alternates = [(l["code"], f"{BASE_URL}/freight-research/{l['code']}/{page['slug']}/") for l in LANGUAGES]
            alternates.append(("x-default", f"{BASE_URL}/freight-research/en/{page['slug']}/"))
            sources = "\n".join(f'<li><a href="{escape(url)}">{escape(url)}</a><br><span>source_url: {escape(url)}</span></li>' for url in page["sources"])
            body = f"""
    <main id="main">
      <article class="guide-article">
        <p class="kicker">Freight Research</p>
        <h1>{escape(item['title'])}</h1>
        <p class="lead">{escape(item['meta'])}</p>
        <section class="guide-panel">
          {split_draft(item['draft'])}
        </section>
        <section class="source-block">
          <h2>Public sources</h2>
          <ul>{sources}</ul>
        </section>
        <a class="button primary" href="/#contact">Start a freight inquiry</a>
      </article>
    </main>"""
            article = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": item["title"],
                "description": item["meta"],
                "url": canonical,
                "datePublished": "2026-06-14",
                "dateModified": date.today().isoformat(),
                "inLanguage": lang["html_lang"],
                "publisher": organization(),
                "citation": page["sources"],
                "mainEntityOfPage": canonical,
            }
            breadcrumb = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Freight Research", "item": f"{BASE_URL}/freight-research/{lang['code']}/"},
                    {"@type": "ListItem", "position": 3, "name": item["title"], "item": canonical},
                ],
            }
            out = ROOT / "freight-research" / lang["code"] / page["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(shell(lang, item["title"], item["meta"], canonical, alternates, body, [article, breadcrumb]), encoding="utf-8")


def main():
    pages = parse_batch(ROOT / "content" / "research_batches" / "week-2026-06-14.md")
    build_hubs(pages)
    build_pages(pages)


if __name__ == "__main__":
    main()
