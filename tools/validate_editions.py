"""Read-only consistency and basic privacy checks; not an exhaustive secret scan."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re
import fitz
from build_editions import ROOT, EDITIONS, blocks


class TextReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def normalized(text):
    text = re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)', r'\1 (\2)', text)
    text = text.replace('**', '')
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    return re.sub(r'\s+', '', text)


def main():
    manifest = json.loads((ROOT / 'tools' / 'edition_manifest.json').read_text())
    for group in manifest.values():
        for name, expected in group.items():
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            assert actual == expected, f'Stale edition file: {name}'
    pages = 0
    for key, name in EDITIONS:
        source = (ROOT / 'manuscript' / f'{key}.md').read_text()
        assert source.startswith('# '), name
        with fitz.open(ROOT / name) as doc:
            assert doc.embfile_count() == 0 and not doc.get_xml_metadata(), name
            for field in ['author', 'subject', 'keywords', 'creator', 'producer', 'creationDate', 'modDate']:
                assert not doc.metadata.get(field), (name, field)
            extracted = normalized('\n'.join(re.sub(r'^TBOCAC \| Editorial edition\n\d+\n', '', p.get_text(), flags=re.M) for p in doc))
            for kind, text in blocks(source):
                # A paragraph can be split by a page footer; compare meaningful runs.
                for sentence in re.split(r'(?<=[.!?])\s+', text):
                    cleaned = normalized(sentence)
                    if len(cleaned) > 25:
                        # Remove generated footers before checking source completeness.
                        assert cleaned in extracted, f'Missing PDF text in {name}: {cleaned[:35]}'
            for page in doc:
                pages += 1
                assert page.get_text().strip(), (name, page.number, 'blank')
                for b in page.get_text('dict')['blocks']:
                    for line in b.get('lines', []):
                        x0, y0, x1, y1 = line['bbox']
                        assert x0 >= 45 and x1 <= page.rect.width - 45, (name, page.number, 'horizontal overflow')
                        assert y0 >= 35 and y1 <= page.rect.height - 22, (name, page.number, 'vertical overflow')
    html = (ROOT / 'Full_TBOCAC.html').read_text()
    assert html.startswith('<!doctype html>')
    for key, _ in EDITIONS:
        assert f'id="chapter-{key}"' in html, key
    selections = sorted((ROOT / 'cassandra-chapters').glob('20*.md'))
    assert len(selections) == 58
    patterns = {
        'private IPv4': r'\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b',
        'email address': r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b',
        'token': r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})\b',
        'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    }
    for path in list((ROOT / 'manuscript').glob('*.md')) + selections:
        text = path.read_text()
        assert not re.search(r'^--- PAGE \d+ ---', text, re.M), path.name
        assert '*[Private or operational passage omitted.]*' not in text, path.name
        for label, pattern in patterns.items():
            assert not re.search(pattern, text), (path.name, label)
    print(f'PASS: 24 PDFs / {pages} pages; 4 export hashes; 58 selections; source completeness, bounds, metadata, basic privacy patterns.')


if __name__ == '__main__':
    main()
