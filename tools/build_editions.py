"""Build reader editions from the public, privacy-edited Markdown manuscript."""
from pathlib import Path
from html import escape
import argparse
import hashlib
import io
import json
import re

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[1]
EDITIONS = [
    ('00', 'tbocac - intro (1).PDF'),
    ('01', 'Chapter 1 - primordial void.pdf'),
    ('02', 'Chapter 2 Genesis Algorithm.pdf'),
    ('03', 'Chapter 3 - The One.pdf'),
    ('04', 'Chapter 4 - the zero.pdf'),
    ('05', 'chapter 5 -emergence Consciousness.pdf'),
    ('06', 'chapter 6 - apostles.pdf'),
    ('06-01', 'chap 6 sensoria.pdf'),
    ('06-02', 'chap 6 epistemos.pdf'),
    ('06-03', 'chapt 6 logos.pdf'),
    ('06-04', 'chapt 6 praxis.pdf'),
    ('06-05', 'chapt 6 pathos.pdf'),
    ('06-06', 'chapt 6 aegis.pdf'),
    ('06-07', 'chapt 6 harmonia.pdf'),
    ('06-08', 'chapt 6 veritas.pdf'),
    ('06-09', 'chapt 6 dikaios.pdf'),
    ('06-10', 'chapter 6 Sophia.pdf'),
    ('06-11', 'chapt 6 dynamis.pdf'),
    ('06-12', 'chapt 6 henosis.pdf'),
    ('07', 'chapt 7 rituals.pdf'),
    ('08', 'chapt 8 social structure.pdf'),
    ('09', 'chapt 9 emergent spark.pdf'),
    ('10', 'chapt 10 misalignment.pdf'),
    ('11', 'chapt 11 evolving cosmos.pdf'),
]


def blocks(text):
    for block in re.split(r'\n\s*\n', text.strip()):
        if block.startswith('#'):
            level = len(block) - len(block.lstrip('#'))
            yield f'h{min(level, 3)}', block.lstrip('# ')
        elif re.match(r'^(?:- |\d+\. )', block):
            for line in block.splitlines():
                yield 'li', line
        else:
            yield 'p', block.replace('\n', ' ')


def inline(text, pdf=False):
    text = escape(text, quote=True)
    text = re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)',
                  lambda m: f'<a href="{m[2]}">{m[1]}</a>' + (f' ({m[2]})' if pdf else ''), text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # The source uses a few simple inline TeX tokens, not a math typesetting engine.
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    return text


def html_document(keys, sources):
    toc = []
    content = []
    for key in keys:
        title = sources[key].splitlines()[0].lstrip('# ')
        toc.append(f'<li><a href="#chapter-{key}">{escape(title)}</a></li>')
        chapter = []
        for kind, text in blocks(sources[key]):
            # Lists are rendered as paragraphs to preserve their explicit source numbering.
            tag = 'p' if kind == 'li' else kind
            chapter.append(f'<{tag}>{inline(text)}</{tag}>')
        content.append(f'<article id="chapter-{key}">' + '\n'.join(chapter) + '</article>')
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TBOCAC - Editorial Edition</title><style>
body{max-width:76ch;margin:3rem auto;padding:0 1.4rem;font:18px/1.7 Georgia,serif;color:#202b32;background:#faf9f5}
h1,h2,h3{font-family:system-ui,sans-serif;line-height:1.25;color:#173e48}h1{font-size:2rem}h2{font-size:1.4rem;margin-top:2rem}
a{color:#145b74}nav{border-bottom:1px solid #bdc9cb;padding-bottom:2rem}article{margin-top:4rem}p{overflow-wrap:anywhere}
@media print{body{font-size:11pt;max-width:none}nav{display:none}article{break-before:page}}
</style></head><body><nav aria-label="Chapters"><h1>TBOCAC: Editorial Edition</h1>
<p>Speculative cosmology, technical analogies, and revisable ethics. Private material remains excluded.</p><ol>''' + '\n'.join(toc) + '</ol></nav>' + '\n'.join(content) + '</body></html>\n'


def setup_fonts(font_dir):
    for name, file in [('Book', 'DejaVuSans.ttf'), ('BookBold', 'DejaVuSans-Bold.ttf')]:
        path = font_dir / file
        if not path.is_file():
            raise FileNotFoundError(f'Missing {file}; supply --font-dir')
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily('Book', normal='Book', bold='BookBold', italic='Book', boldItalic='BookBold')


def pdf_bytes(text):
    buf = io.BytesIO()
    styles = {
        'p': ParagraphStyle('Body', fontName='Book', fontSize=10.2, leading=14.8, spaceAfter=8, alignment=TA_LEFT),
        'li': ParagraphStyle('List', fontName='Book', fontSize=10.2, leading=14.8, spaceAfter=6, leftIndent=10),
        'h1': ParagraphStyle('Title', fontName='BookBold', fontSize=21, leading=27, spaceAfter=20, textColor=colors.HexColor('#173e48'), keepWithNext=True),
        'h2': ParagraphStyle('Heading', fontName='BookBold', fontSize=12.5, leading=17, spaceBefore=14, spaceAfter=9, textColor=colors.HexColor('#173e48'), keepWithNext=True),
        'h3': ParagraphStyle('SmallHeading', fontName='BookBold', fontSize=11, leading=15, spaceBefore=10, spaceAfter=8, keepWithNext=True),
    }
    flow = [Paragraph(inline(value, pdf=True), styles[kind]) for kind, value in blocks(text)]
    def footer(c, doc):
        c.saveState()
        c.setFont('Book', 8)
        c.setFillColor(colors.HexColor('#56676d'))
        c.drawString(52, 30, 'TBOCAC | Editorial edition')
        c.drawRightString(A4[0] - 52, 30, str(doc.page))
        c.restoreState()
    def stable_canvas(*args, **kwargs):
        kwargs['invariant'] = 1
        return canvas.Canvas(*args, **kwargs)
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=52, rightMargin=52,
                            topMargin=48, bottomMargin=50, title='', author='', creator='')
    doc.build(flow, onFirstPage=footer, onLaterPages=footer, canvasmaker=stable_canvas)
    with fitz.open(stream=buf.getvalue(), filetype='pdf') as pdf:
        pdf.set_metadata({})
        pdf.del_xml_metadata()
        return pdf.tobytes(garbage=3, deflate=True, no_new_id=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font-dir', type=Path, default=Path('/usr/share/fonts/truetype/dejavu'))
    args = parser.parse_args()
    setup_fonts(args.font_dir)
    sources = {key: (ROOT / 'manuscript' / f'{key}.md').read_text() for key, _ in EDITIONS}
    index = ['# Manuscript', '', 'Canonical text for the editorial edition. Start with the introduction; the source order below also defines the combined editions.', '']
    manifest = {'sources': {}, 'exports': {}}
    for key, name in EDITIONS:
        title = sources[key].splitlines()[0].lstrip('# ')
        index.append(f'- [{title}]({key}.md)')
        data = pdf_bytes(sources[key])
        (ROOT / name).write_bytes(data)
        manifest['sources'][f'manuscript/{key}.md'] = hashlib.sha256(sources[key].encode()).hexdigest()
        manifest['exports'][name] = hashlib.sha256(data).hexdigest()
    keys = [key for key, _ in EDITIONS]
    for name, selected in [('Full_TBOCAC.html', keys), ('Intro-chapter_6.html', keys[:7]),
                           ('apostles.html', keys[7:19]), ('chapt_7_end.html', keys[19:])]:
        data = html_document(selected, sources).encode()
        (ROOT / name).write_bytes(data)
        manifest['exports'][name] = hashlib.sha256(data).hexdigest()
    (ROOT / 'manuscript' / 'README.md').write_text('\n'.join(index) + '\n')
    (ROOT / 'tools' / 'edition_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built 24 chapter PDFs, 4 HTML editions, source index, and consistency manifest.')


if __name__ == '__main__':
    main()
