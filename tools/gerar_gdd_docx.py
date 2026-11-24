"""Gera o GDD completo em Word (.docx) para edição.

Uso:  python tools/gerar_gdd_docx.py

- Entrada: docs/gdd_completo/GDD_PyShooter_completo.md (o mesmo do PDF).
- Saída:   docs/gdd_completo/GDD_PyShooter_completo.docx
- Fórmulas viram equações nativas do Word (editáveis); diagramas entram como PNG
  (docs/gdd_completo/diagramas/*.png, gerados com
  java -DPLANTUML_LIMIT_SIZE=16384 -jar plantuml.jar -tpng -Sdpi=200 -charset UTF-8 -o <pasta> docs/uml/*.puml).
- Depois do pandoc, o python-docx aplica o visual do GDD 1: Arial, títulos pretos,
  tabelas com cabeçalho azul e diagramas grandes em páginas paisagem.

Requer: pip install pypandoc_binary python-docx
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

import pypandoc
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / 'docs' / 'gdd_completo'
MD = PASTA / 'GDD_PyShooter_completo.md'
DOCX = PASTA / 'GDD_PyShooter_completo.docx'

AZUL = '2F6AB5'
FONTE = 'Arial'
TAMANHOS = {'Title': 20, 'Heading 1': 20, 'Heading 2': 16, 'Heading 3': 13, 'Heading 4': 11}


def preparar_markdown() -> str:
    """Troca os trechos em HTML do .md (feitos para o PDF) por Markdown do pandoc."""
    t = MD.read_text(encoding='utf-8')
    t = re.sub(r'<div class="formula">\\\[(.*?)\\\]</div>', r'$$\1$$', t)

    def diagrama(m: re.Match) -> str:
        paisagem, nome = bool(m.group(1)), m.group(2)
        largura = '25.5cm' if paisagem else ('13cm' if 'sequencia' in nome else '16cm')
        alt = 'paisagem' if paisagem else 'diagrama'
        return f'![{alt}]({nome}.png){{width={largura}}}'

    t = re.sub(r'<div class="diagrama( paisagem)?"><img src="(diagramas/[^".]+)\.svg"[^>]*></div>', diagrama, t)
    t = re.sub(r'<p class="sub">(.*?)</p>', r'*\1*', t)
    return t


def sombrear(celula, cor: str) -> None:
    tcPr = celula._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), cor)
    tcPr.append(shd)


def bordas(tabela) -> None:
    tblPr = tabela._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for lado in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement(f'w:{lado}')
        e.set(qn('w:val'), 'single')
        e.set(qn('w:sz'), '4')
        e.set(qn('w:color'), '9E9E9E')
        b.append(e)
    tblPr.append(b)
    largura = OxmlElement('w:tblW')
    largura.set(qn('w:w'), '5000')
    largura.set(qn('w:type'), 'pct')
    for velho in tblPr.findall(qn('w:tblW')):
        tblPr.remove(velho)
    tblPr.append(largura)


def estilo_tabelas(doc: Document) -> None:
    for tabela in doc.tables:
        bordas(tabela)
        tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, linha in enumerate(tabela.rows):
            if i == 0:
                trPr = linha._tr.get_or_add_trPr()
                rep = OxmlElement('w:tblHeader')
                trPr.append(rep)
            for j, celula in enumerate(linha.cells):
                if i == 0:
                    sombrear(celula, AZUL)
                for par in celula.paragraphs:
                    par.paragraph_format.space_before = Pt(3)
                    par.paragraph_format.space_after = Pt(3)
                    for run in par.runs:
                        run.font.size = Pt(9.5)
                        if i == 0:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        elif j == 0:
                            run.font.bold = True


def estilo_textos(doc: Document) -> None:
    for estilo in doc.styles:
        try:
            fonte = estilo.font
        except AttributeError:
            continue
        if fonte is None:
            continue
        fonte.name = FONTE
        rpr = estilo.element.get_or_add_rPr()
        rfonts = rpr.find(qn('w:rFonts'))
        if rfonts is None:
            rfonts = OxmlElement('w:rFonts')
            rpr.append(rfonts)
        for att in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rfonts.set(qn(att), FONTE)
        for att in ('w:asciiTheme', 'w:hAnsiTheme', 'w:cstheme', 'w:eastAsiaTheme'):
            rfonts.attrib.pop(qn(att), None)
        if estilo.name in TAMANHOS:
            fonte.size = Pt(TAMANHOS[estilo.name])
            fonte.color.rgb = RGBColor(0, 0, 0)
            fonte.bold = estilo.name in ('Title', 'Heading 1')
            fonte.italic = False
    for nome in ('Normal', 'Body Text', 'First Paragraph', 'Compact'):
        if nome in [s.name for s in doc.styles]:
            doc.styles[nome].font.size = Pt(10.5)
    # Título centralizado (primeiro parágrafo) e subtítulo logo abaixo.
    doc.paragraphs[0].alignment = 1
    doc.paragraphs[1].alignment = 1


def secao(orientacao, modelo) -> OxmlElement:
    s = copy.deepcopy(modelo)
    pg = s.find(qn('w:pgSz'))
    w, h = Cm(21.0), Cm(29.7)
    if orientacao == 'paisagem':
        w, h = h, w
        pg.set(qn('w:orient'), 'landscape')
        mar = s.find(qn('w:pgMar'))
        for lado in ('w:top', 'w:bottom', 'w:left', 'w:right'):
            mar.set(qn(lado), str(Cm(1.2).twips))
    else:
        pg.attrib.pop(qn('w:orient'), None)
    pg.set(qn('w:w'), str(w.twips))
    pg.set(qn('w:h'), str(h.twips))
    return s


def paginas_paisagem(doc: Document) -> None:
    corpo = doc.sections[-1]
    corpo.orientation = WD_ORIENT.PORTRAIT
    corpo.page_width, corpo.page_height = Cm(21.0), Cm(29.7)
    corpo.top_margin = corpo.bottom_margin = Cm(2.0)
    corpo.left_margin = corpo.right_margin = Cm(2.2)
    modelo = corpo._sectPr

    def e_paisagem(elem) -> bool:
        return any(d.get('descr') == 'paisagem' for d in elem.iter(qn('wp:docPr')))

    for p in doc.paragraphs:
        if not e_paisagem(p._p):
            continue
        # A seção retrato termina no elemento logo antes do diagrama; se ele for
        # uma tabela (ou não existir parágrafo), cria um parágrafo vazio para isso.
        anterior = p._p.getprevious()
        if anterior is None or not e_paisagem(anterior):
            if anterior is None or anterior.tag != qn('w:p'):
                anterior = OxmlElement('w:p')
                p._p.addprevious(anterior)
            pPr = anterior.find(qn('w:pPr'))
            if pPr is None:
                pPr = OxmlElement('w:pPr')
                anterior.insert(0, pPr)
            pPr.append(secao('retrato', modelo))
        p.alignment = 1
        # O pandoc limita a imagem à largura do retrato; aqui ela ocupa a página deitada
        # (até 26,5 × 18 cm, mantendo a proporção).
        for ext in p._p.iter(qn('wp:extent'), qn('a:ext')):
            cx, cy = int(ext.get('cx')), int(ext.get('cy'))
            escala = min(Cm(26.5) / cx, Cm(18.0) / cy)
            ext.set('cx', str(int(cx * escala)))
            ext.set('cy', str(int(cy * escala)))
        p._p.get_or_add_pPr().append(secao('paisagem', modelo))


def main() -> None:
    texto = preparar_markdown()
    pypandoc.convert_text(texto, 'docx', format='markdown+hard_line_breaks-implicit_figures',
                          outputfile=str(DOCX),
                          extra_args=[f'--resource-path={PASTA}'])
    doc = Document(str(DOCX))
    estilo_textos(doc)
    estilo_tabelas(doc)
    paginas_paisagem(doc)
    for p in doc.paragraphs:  # diagramas retrato centralizados
        if any(d.get('descr') == 'diagrama' for d in p._p.iter(qn('wp:docPr'))):
            p.alignment = 1
    doc.save(str(DOCX))
    print(f'DOCX gerado: {DOCX.relative_to(RAIZ)} ({DOCX.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
