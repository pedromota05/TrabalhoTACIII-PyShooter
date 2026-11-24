"""Gera o GDD completo (Trabalho 1 + Trabalho 2) em HTML e PDF.

Uso:  python tools/gerar_gdd_completo.py [--sem-pdf]

- Entrada: docs/gdd_completo/GDD_PyShooter_completo.md
- Diagramas: docs/gdd_completo/diagramas/*.svg, gerados a partir de docs/uml/*.puml
  com o PlantUML (java -jar plantuml.jar -tsvg -charset UTF-8 -o <pasta> docs/uml/*.puml).
- Fórmulas: blocos <div class="formula">\\[ ... \\]</div>, desenhados pelo KaTeX (CDN)
  no momento da impressão, em caixa escura como no GDD do Trabalho 1.
- PDF: Microsoft Edge headless (A4; diagramas grandes em página paisagem).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / 'docs' / 'gdd_completo'
MD = PASTA / 'GDD_PyShooter_completo.md'
HTML = PASTA / 'GDD_PyShooter_completo.html'
PDF = PASTA / 'GDD_PyShooter_completo.pdf'
EDGE = Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
KATEX = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist'

CSS = """
@page { size: A4; margin: 2cm 2.2cm; }
@page paisagem { size: A4 landscape; margin: 1.2cm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; color: #000;
       line-height: 1.38; }
h1 { text-align: center; font-size: 20pt; margin: 0 0 4pt; }
p.sub { text-align: center; color: #555; font-size: 9pt; margin-top: 0; }
h2 { font-size: 16pt; font-weight: normal; margin: 22pt 0 8pt; }
h3 { font-size: 13pt; font-weight: normal; margin: 16pt 0 6pt; break-after: avoid; }
h4 { font-size: 11pt; font-weight: normal; margin: 12pt 0 4pt; break-after: avoid; }
p { text-align: justify; margin: 4pt 0 8pt; }
code { font-family: Consolas, monospace; font-size: 9.5pt; }
table { width: 100%; border-collapse: collapse; margin: 6pt 0 12pt; font-size: 9.5pt; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th { background: #2f6ab5; color: #fff; text-align: left; padding: 7pt 6pt; }
td { border: 1px solid #9e9e9e; padding: 5pt 6pt; vertical-align: top; }
td:first-child { font-weight: bold; }
td strong { font-weight: bold; }
.formula { display: block; width: fit-content; background: #000; color: #fff;
           padding: 4pt 14pt; margin: 4pt 0 10pt 36pt; font-size: 10pt; break-inside: avoid; }
.formula .katex-display { margin: 0; }
.diagrama { text-align: center; margin: 10pt 0; break-inside: avoid; }
.diagrama img { max-width: 100%; max-height: 22cm; }
.diagrama.paisagem { page: paisagem; break-before: page; break-after: page; margin: 0; }
.diagrama.paisagem img { width: 100%; max-height: 18.2cm; object-fit: contain; }
a { color: #1155cc; }
"""

SCRIPT = """
<script>
document.querySelectorAll('.formula').forEach(function (el) {
  var tex = el.textContent.trim().replace(/^\\\\\\[/, '').replace(/\\\\\\]$/, '');
  katex.render(tex, el, {displayMode: true, throwOnError: true});
});
</script>
"""


def gerar_html() -> None:
    corpo = markdown.markdown(MD.read_text(encoding='utf-8'),
                              extensions=['tables', 'nl2br', 'sane_lists'])
    # Células só com um ID (RF-01, RNF-03...) não quebram linha.
    corpo = re.sub(r'<td>(<strong>R?N?F-\d+</strong>)</td>',
                   r'<td style="white-space: nowrap;">\1</td>', corpo)
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>GDD TAC III - PyShooter</title>
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<script src="{KATEX}/katex.min.js"></script>
<style>{CSS}</style>
</head>
<body>
{corpo}
{SCRIPT}
</body>
</html>
"""
    HTML.write_text(html, encoding='utf-8', newline='\n')
    print(f'HTML gerado: {HTML.relative_to(RAIZ)}')


def gerar_pdf() -> None:
    if not EDGE.exists():
        sys.exit(f'Edge não encontrado em {EDGE}')
    cmd = [str(EDGE), '--headless', '--disable-gpu', '--no-pdf-header-footer',
           '--virtual-time-budget=15000', f'--print-to-pdf={PDF}', HTML.as_uri()]
    subprocess.run(cmd, check=True, timeout=180,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not PDF.exists():
        sys.exit('O Edge não gerou o PDF.')
    print(f'PDF gerado: {PDF.relative_to(RAIZ)} ({PDF.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    gerar_html()
    if '--sem-pdf' not in sys.argv:
        gerar_pdf()
