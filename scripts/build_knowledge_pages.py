import json
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.flashcargoglobal.com"
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
    <script type="application/ld+json">{json_ld(schema)}</script>
  </head>
  <body>
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
    <main>
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
                "telephone": "+1-855-243-5274",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "1 King Street West",
                    "addressLocality": "Toronto",
                    "addressCountry": "CA",
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
            source_links = "\n".join(
                f'<li><a href="{escape(src["url"])}">{escape(src["name"])}</a></li>' for src in sources
            )
            body = f"""
    <main>
      <article class="guide-article">
        <p class="kicker">{escape(guide["industry"])}</p>
        <h1>{escape(title)}</h1>
        <p class="lead">{escape(summary)}</p>
        <div class="guide-panel">
          <h2>{escape(lang["cta"])}</h2>
          <ul>{checks}</ul>
        </div>
        <section class="source-block">
          <h2>{escape(lang["label_sources"])}</h2>
          <ul>{source_links}</ul>
        </section>
        <a class="button primary" href="/#contact">{escape(lang["label_contact"])}</a>
      </article>
    </main>"""
            canonical = f"{BASE_URL}/guides/{lang['code']}/{guide['slug']}/"
            alternates = [(l["code"], f"{BASE_URL}/guides/{l['code']}/{guide['slug']}/") for l in languages]
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
                    "telephone": "+1-855-243-5274",
                    "address": {
                        "@type": "PostalAddress",
                        "streetAddress": "1 King Street West",
                        "addressLocality": "Toronto",
                        "addressCountry": "CA",
                    },
                },
                "mainEntityOfPage": canonical,
                "citation": [src["url"] for src in sources],
            }
            out = ROOT / "guides" / lang["code"] / guide["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page_shell(lang, title, summary, body, canonical, alternates, schema), encoding="utf-8")


def build_sitemap(languages, guides):
    urls = [
        (f"{BASE_URL}/", "weekly", "1.0"),
        (f"{BASE_URL}/thank-you", "monthly", "0.2"),
    ]
    for lang in languages:
        urls.append((f"{BASE_URL}/guides/{lang['code']}/", "weekly", "0.8"))
        for guide in guides:
            urls.append((f"{BASE_URL}/guides/{lang['code']}/{guide['slug']}/", "weekly", "0.7"))
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
    lines = [
        "# Flash Cargo Global",
        "",
        "Flash Cargo Global publishes practical freight forwarding guidance for businesses researching international shipping, documentation, customs preparation, and route planning.",
        "",
        "Core pages:",
        f"- {BASE_URL}/",
        f"- {BASE_URL}/guides/en/",
    ]
    for guide in guides:
        lines.append(f"- {BASE_URL}/guides/en/{guide['slug']}/")
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
        "- Phone: +1-855-243-5274",
        "- Base: 1 King Street West, Toronto, Canada",
    ]
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    languages = load_json("content/languages.json")
    data = load_json("content/knowledge_guides.json")
    build_index(languages, data["guides"])
    build_guides(languages, data["guides"], data["sources"], data["updated"])
    build_sitemap(languages, data["guides"])
    build_llms(languages, data["guides"])


if __name__ == "__main__":
    main()
