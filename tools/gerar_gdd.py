"""Gera docs/GDD_Trabalho2.html e docs/GDD_Trabalho2.pdf a partir do Markdown.

Uso:  python tools/gerar_gdd.py [--sem-pdf]

- Converte docs/GDD_Trabalho2.md com o pacote `markdown` (tabelas, blocos de
  código, quebras de linha e ids nos títulos).
- Mantém exatamente o <head>/<style> que já está em docs/GDD_Trabalho2.html.
- Gera o PDF com o Microsoft Edge em modo headless (A4, sem cabeçalho/rodapé).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent.parent
MD = RAIZ / 'docs' / 'GDD_Trabalho2.md'
HTML = RAIZ / 'docs' / 'GDD_Trabalho2.html'
PDF = RAIZ / 'docs' / 'GDD_Trabalho2.pdf'
EDGE = Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')

EXTENSOES = ['tables', 'fenced_code', 'nl2br', 'toc']


def cabecalho_atual() -> str:
    """Tudo do início do HTML atual até a tag <body> (inclusive)."""
    texto = HTML.read_text(encoding='utf-8')
    fim = texto.find('<body>')
    if fim < 0:
        sys.exit(f'Não achei <body> em {HTML}')
    return texto[:fim + len('<body>')]


def gerar_html() -> None:
    corpo = markdown.markdown(MD.read_text(encoding='utf-8'), extensions=EXTENSOES)
    # Células só com um ID (RF-01, RNF-03...) não quebram linha no PDF.
    corpo = re.sub(r'<td( style="text-align: left;")?>(<strong>R?N?F-\d+</strong>)</td>',
                   r'<td style="text-align: left; white-space: nowrap;">\2</td>', corpo)
    html = f'{cabecalho_atual()}\n    {corpo}\n</body>\n</html>\n'
    HTML.write_text(html, encoding='utf-8', newline='\n')
    print(f'HTML gerado: {HTML.relative_to(RAIZ)}')


def gerar_pdf() -> None:
    if not EDGE.exists():
        sys.exit(f'Edge não encontrado em {EDGE}')
    cmd = [str(EDGE), '--headless', '--disable-gpu', '--no-pdf-header-footer',
           f'--print-to-pdf={PDF}', HTML.as_uri()]
    subprocess.run(cmd, check=True, timeout=120,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not PDF.exists():
        sys.exit('O Edge não gerou o PDF.')
    print(f'PDF gerado: {PDF.relative_to(RAIZ)} ({PDF.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    gerar_html()
    if '--sem-pdf' not in sys.argv:
        gerar_pdf()
