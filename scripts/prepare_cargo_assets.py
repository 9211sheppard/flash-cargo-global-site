"""Prepare the selected illustration and self-hosted, openly licensed fonts."""

import csv
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
OUT = ROOT / 'output' / 'cargo-global-reposition'
IMAGE = Path(r'C:\Users\Owner\.codex\generated_images\019daff3-8eec-7d81-b7a9-fa761d68e614\exec-e91ef447-a1fe-4cb7-a1ea-e2f9f0ca07bc.png')


def responsive_images():
    source = IMAGE if IMAGE.exists() else ASSETS / 'sourcing-assortment.webp'
    image = Image.open(source).convert('RGB')
    rows = []
    for width in (480, 768):
        size = (width, round(image.height * width / image.width))
        target = ASSETS / f'sourcing-assortment-{width}.webp'
        image.resize(size, Image.Resampling.LANCZOS).save(target, 'WEBP', quality=84, method=6)
        rows.append({'asset': target.name, 'bytes': target.stat().st_size, 'source_url': source.as_uri(), 'last_checked': datetime.now(timezone.utc).isoformat()})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'responsive-asset-sources.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['asset', 'bytes', 'source_url', 'last_checked'])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    ASSETS.mkdir(exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    records = []
    image = Image.open(IMAGE).convert('RGB')
    image.save(ASSETS / 'sourcing-assortment.webp', 'WEBP', quality=84, method=6)
    image.save(ASSETS / 'sourcing-assortment.jpg', 'JPEG', quality=84, optimize=True, progressive=True)
    responsive_images()
    records.append({'asset': 'sourcing-assortment.webp', 'purpose': 'Illustrative product assortment, not a client project', 'source_url': IMAGE.as_uri(), 'last_checked': now})
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    for family, filename in [('Instrument Sans:wght@400;500;600;700', 'instrument-sans'), ('Instrument Serif', 'instrument-serif')]:
        css_url = 'https://fonts.googleapis.com/css2?family=' + family.replace(' ', '+') + '&display=swap'
        response = session.get(css_url, timeout=30)
        response.raise_for_status()
        blocks = re.findall(r'/\* latin \*/\s*(@font-face\s*\{.*?\})', response.text, re.S)
        if not blocks:
            raise RuntimeError('Could not identify the latin font subset')
        font_url = re.search(r'url\((https://fonts.gstatic.com/[^)]+)\)', blocks[-1]).group(1)
        font = session.get(font_url, timeout=30)
        font.raise_for_status()
        (ASSETS / (filename + '.woff2')).write_bytes(font.content)
        records.append({'asset': filename + '.woff2', 'purpose': 'Self-hosted font; no browser request to a third-party font service', 'source_url': font_url, 'last_checked': now})
        directory = filename.replace('-', '')
        license_url = f'https://raw.githubusercontent.com/google/fonts/main/ofl/{directory}/OFL.txt'
        license_response = session.get(license_url, timeout=30)
        license_response.raise_for_status()
        (ASSETS / (filename + '-OFL.txt')).write_text(license_response.text, encoding='utf-8')
    with (OUT / 'asset-sources.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['asset', 'purpose', 'source_url', 'last_checked'])
        writer.writeheader()
        writer.writerows(records)
    print([(p.name, p.stat().st_size) for p in ASSETS.iterdir()])


if __name__ == '__main__':
    main()
