"""Prepare a bounded release manifest; never include local outputs or credentials."""

import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'cargo-global-reposition'


def main():
    selected = [p for p in ROOT.rglob('*.html') if p.relative_to(ROOT).parts[0] not in ('output', 'content')]
    selected.extend((ROOT / 'assets').iterdir())
    selected.extend(ROOT / path for path in [
        'cargo-global.css', 'cargo-global.js', '_redirects', 'README.md', 'sitemap.xml', 'robots.txt',
        'llms.txt', 'humans.txt', '.well-known/organization.json', '.well-known/citation-profile.json',
        'content/interim-inquiry-form.html', 'scripts/build_cargo_global.py', 'scripts/validate_cargo_global.py',
        'scripts/prepare_cargo_assets.py', 'scripts/package_cargo_reposition.py',
        'scripts/build_service_pages.py', 'scripts/build_knowledge_pages.py', 'scripts/build_industry_pages.py',
        'scripts/build_downstream_pages.py', 'scripts/build_planning_pages.py', 'scripts/build_multilingual_research_pages.py',
    ])
    entries = []
    total = 0
    for path in sorted(set(selected)):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        binary = path.suffix in ('.jpg', '.webp', '.woff2')
        data = path.read_bytes() if binary else path.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode('utf-8')
        if 'output/' in rel or rel.startswith('.git'):
            raise ValueError('Unsafe release path')
        total += len(data)
        entries.append({'path': rel, 'encoding': 'base64' if binary else 'utf-8', 'content': base64.b64encode(data).decode() if binary else data.decode(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    (OUT / 'release.json').write_text(json.dumps(entries, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'files': len(entries), 'bytes': total, 'binary_files': sum(e['encoding'] == 'base64' for e in entries)}))


if __name__ == '__main__':
    main()
