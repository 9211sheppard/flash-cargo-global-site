"""Preserve the existing URL and metadata inventory before the audience rollout."""

import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'audience-rollout'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'baseline.json'
    if target.exists():
        (ROOT / 'content' / 'audience-baseline.json').write_text(target.read_text(encoding='utf-8'), encoding='utf-8')
        print('Existing rollout baseline retained.')
        return
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    with zipfile.ZipFile(OUT / 'before-audience-rollout.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob('*')):
            rel = path.relative_to(ROOT)
            if not path.is_file() or rel.parts[0] in ('output', '.git', 'infrastructure'):
                continue
            archive.write(path, rel.as_posix())
            if path.suffix != '.html' or rel.parts[0] == 'content':
                continue
            soup = BeautifulSoup(path.read_text(encoding='utf-8-sig'), 'html.parser')
            route = '/' + (rel.as_posix()[:-10] if path.name == 'index.html' else rel.as_posix())
            rows.append({'path': route, 'file': rel.as_posix(), 'title': soup.title.get_text(' ', strip=True), 'h1': soup.h1.get_text(' ', strip=True), 'description': soup.select_one('meta[name="description"]')['content'], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_url': 'https://flashcargoglobal.com' + route, 'last_checked': now})
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'content' / 'audience-baseline.json').write_text(target.read_text(encoding='utf-8'), encoding='utf-8')
    with (OUT / 'old-urls.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['path', 'action', 'source_url', 'last_checked'])
        writer.writeheader()
        writer.writerows({'path': row['path'], 'action': 'keep_200', 'source_url': row['source_url'], 'last_checked': now} for row in rows)
    print(json.dumps({'existing_urls_preserved': len(rows), 'title_policy': 'Keep existing titles until Search Console impressions are reviewed.'}))


if __name__ == '__main__':
    main()
