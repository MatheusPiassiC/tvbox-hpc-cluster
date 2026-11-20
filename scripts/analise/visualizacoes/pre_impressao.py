"""Fragmentos LaTeX, PDFs de tabela, miniaturas e prova física A4."""

from pathlib import Path
import os
import re
import shutil
import subprocess
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from PIL import Image

from alternativas import ALTURA_UTIL, FAMILIAS, LARGURA_UTIL
from dados import melhor
from graficos import COR_TEXTO, METADADOS_PDF, cm, decimal, salvar, verificar_layout


CABECALHOS = {
    "benchmark": ("Benchmark", "Benchmark"),
    "p": (r"Melhor $p$", "Melhor $p$"),
    "tempo": (r"Tempo médio\\mín. (s)", "Tempo médio\nmín. (s)"),
    "ic": (r"IC de 95\%\\(s)", "IC de 95%\n(s)"),
    "speedup": (r"Speedup\\máx. ($\times$)", "Speedup\nmáx. (×)"),
    "eficiencia": (r"Eficiência\\no melhor $p$ (\%)", "Eficiência\nno melhor $p$ (%)"),
    "eficiencia_max_p": (r"Eficiência\\no maior $p$ (\%)", "Eficiência\nno maior $p$ (%)"),
}
PREAMBULO_LATEX = r"""
\usepackage[T1]{fontenc}
\usepackage{lmodern,booktabs,graphicx}
\pdfinfoomitdate=1
\pdftrailerid{}
\pdfsuppressptexinfo=15
"""


def base(item):
    return Path(FAMILIAS[item.familia][0]) / item.arquivo


def caminho_previa(item):
    return Path("comparativos/previas") / base(item).parent / f"{item.arquivo}_previa.png"


def caminho_comparativo(familia):
    return Path("comparativos") / f"comparativo_{familia}_{FAMILIAS[familia][1]}"


def dimensoes(dim):
    return f"{decimal(dim[0], 1)} × {decimal(dim[1], 1)} cm"


def linhas_tabela(tabela, dados):
    for b, serie in dados.series.items():
        minimo = melhor(serie)
        campos = {
            "benchmark": b,
            "p": str(minimo.p),
            "tempo": decimal(minimo.tempo, 3),
            "ic": f"[{decimal(minimo.ic_inf, 3)} a {decimal(minimo.ic_sup, 3)}]",
            "speedup": decimal(minimo.speedup, 3),
            "eficiencia": decimal(minimo.eficiencia, 2),
            "eficiencia_max_p": decimal(serie[-1].eficiencia, 2),
        }
        yield [campos[campo] for campo in tabela.campos]


def escrever_tabela(tabela, dados, pasta):
    alinhamento = "l" + "r" * (len(tabela.campos) - 1)
    cabecalhos = [rf"\shortstack[{a}]{{{CABECALHOS[campo][0]}}}"
                   for a, campo in zip(alinhamento, tabela.campos)]
    conteudo = [
        r"% Requer booktabs. Inserir com \input dentro de uma tabela centralizada.",
        r"\begingroup\small",
        r"\setlength{\tabcolsep}{2.5pt}%",
        r"\renewcommand{\arraystretch}{1.20}%",
        rf"\begin{{tabular*}}{{{tabela.largura:.1f}cm}}{{@{{\extracolsep{{\fill}}}}{alinhamento}@{{}}}}",
        r"\toprule",
        " & ".join(cabecalhos) + r" \\",
        r"\midrule",
        *(" & ".join(colunas) + r" \\" for colunas in linhas_tabela(tabela, dados)),
        r"\bottomrule",
        r"\end{tabular*}%",
        r"\endgroup%",
    ]
    (pasta / base(tabela).with_suffix(".tex")).write_text("\n".join(conteudo) + "\n", encoding="utf-8")


def compilar_latex(fonte, pasta, trabalho, nome):
    ambiente = {**os.environ, "LC_ALL": "C", "SOURCE_DATE_EPOCH": "946684800", "FORCE_SOURCE_DATE": "1"}
    resultado = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
         f"-output-directory={trabalho}", f"-jobname={nome}", str(fonte)],
        cwd=pasta, env=ambiente, capture_output=True, text=True, timeout=90,
    )
    if resultado.returncode:
        mensagens = [s.strip() for s in resultado.stdout.splitlines() if s.startswith("!") or ".tex:" in s]
        resumo = mensagens[0] if mensagens else "consulte a disponibilidade de pacotes TeX"
        raise RuntimeError(f"pdflatex falhou em {nome} ({resumo})")
    log = (trabalho / f"{nome}.log").read_text(encoding="utf-8", errors="replace")
    if re.search(r"Overfull \\[hv]box", log):
        raise RuntimeError(f"{nome} contém caixa LaTeX que ultrapassa as dimensões previstas")
    return trabalho / f"{nome}.pdf"


def exportar_tabela_latex(tabela, pasta, trabalho, dpi, dpi_previa):
    wrapper = trabalho / f"{tabela.id}.tex"
    wrapper.write_text(
        r"\documentclass[11pt]{article}" + PREAMBULO_LATEX + "\n" + r"""
\begin{document}
\newsavebox{\sintese}
""" + rf"\sbox{{\sintese}}{{\input{{{base(tabela).with_suffix('.tex').as_posix()}}}}}" + "\n" + r"""
\pdfpagewidth=\wd\sintese
\pdfpageheight=\dimexpr\ht\sintese+\dp\sintese+3mm\relax
\pdfhorigin=0pt
\pdfvorigin=0pt
\shipout\vbox{\kern1.5mm\hbox{\usebox{\sintese}}\kern1.5mm}
\end{document}
""", encoding="utf-8",
    )
    compilado = compilar_latex(wrapper, pasta, trabalho, tabela.id)
    pdf = pasta / base(tabela).with_suffix(".pdf")
    shutil.copyfile(compilado, pdf)
    for png, resolucao in ((pdf.with_suffix(".png"), dpi), (pasta / caminho_previa(tabela), dpi_previa)):
        subprocess.run(["pdftoppm", "-singlefile", "-png", "-r", str(resolucao), str(pdf),
                        str(png.with_suffix(""))], check=True, timeout=45, capture_output=True)
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, timeout=15, capture_output=True,
                          text=True, env={**os.environ, "LC_ALL": "C"}).stdout
    tamanho = re.search(r"Page size:\s+([0-9.]+) x ([0-9.]+) pts", info)
    if tamanho is None:
        raise RuntimeError(f"Dimensões indisponíveis para a tabela {tabela.id}")
    largura, altura = (float(v) * 2.54 / 72 for v in tamanho.groups())
    if abs(largura - tabela.largura) > .01:
        raise RuntimeError(f"Largura divergente para a tabela {tabela.id}")
    return tabela.largura, altura


def tabela_raster(tabela, dados, pasta, dpi, dpi_previa):
    altura = 4.65
    figura = plt.figure(figsize=(cm(tabela.largura), cm(altura)), dpi=dpi_previa)
    larguras_relativas = {"benchmark": 1.0, "p": .75, "tempo": 1.1, "ic": 1.65, "speedup": .95,
                          "eficiencia": 1.25, "eficiencia_max_p": 1.25}
    total = sum(larguras_relativas[c] for c in tabela.campos)
    posicoes = [.024]
    for campo in tabela.campos:
        posicoes.append(posicoes[-1] + .952 * larguras_relativas[campo] / total)
    linhas = list(linhas_tabela(tabela, dados))
    for i, campo in enumerate(tabela.campos):
        x, ha = (posicoes[0], "left") if i == 0 else (posicoes[i + 1] - .013, "right")
        figura.text(x, .856, CABECALHOS[campo][1], ha=ha, va="center", fontsize=9.8)
        for j, linha in enumerate(linhas):
            figura.text(x, .70 - .085 * j, linha[i], ha=ha, va="center", fontsize=10)
    for y, espessura in ((.96, .85), (.764, .5), (.054, .85)):
        figura.add_artist(Line2D([.024, .976], [y, y], transform=figura.transFigure,
                                 color=COR_TEXTO, linewidth=espessura))
    try:
        verificar_layout(figura, [], tabela.id, None)
        salvar(figura, pasta / base(tabela), dpi, pasta / caminho_previa(tabela), dpi_previa)
    finally:
        plt.close(figura)
    return tabela.largura, altura


def gerar_tabelas(tabelas, dados, pasta, trabalho, dpi, dpi_previa):
    for item in tabelas:
        escrever_tabela(item, dados, pasta)
    faltam = [utilitario for utilitario in ("pdflatex", "pdftoppm", "pdfinfo") if not shutil.which(utilitario)]
    if faltam:
        motivo = "Ferramentas ausentes para exportar as prévias TeX " + ", ".join(faltam) + "."
    else:
        try:
            return {t.id: exportar_tabela_latex(t, pasta, trabalho, dpi, dpi_previa) for t in tabelas}, ""
        except (RuntimeError, subprocess.SubprocessError) as erro:
            motivo = str(erro)
    return {t.id: tabela_raster(t, dados, pasta, dpi, dpi_previa) for t in tabelas}, motivo


def quebrar_nome(nome):
    # A quebra preserva todos os caracteres do nome, inclusive os sublinhados.
    return "\n".join(textwrap.wrap(nome.replace("_", "_ "), width=48, break_on_hyphens=False)).replace(" ", "")


def comparar(familia, itens, dim, pasta, dpi, dpi_previa):
    colunas = 2 if len(itens) <= 4 else 3
    linhas = [itens[i:i + colunas] for i in range(0, len(itens), colunas)]
    reducao = .52
    largura_card, margem, espaco = 9.05, .80, .35
    largura = 2 * margem + colunas * largura_card + (colunas - 1) * espaco
    alturas = [2.60 + reducao * max(dim[item.id][1] for item in linha) for linha in linhas]
    altura = 2.85 + sum(alturas) + espaco * (len(linhas) - 1) + margem
    figura = plt.figure(figsize=(cm(largura), cm(altura)), dpi=dpi_previa)

    def texto(x, y, s, **kwargs):
        figura.text(x / largura, 1 - y / altura, s, va="top", **kwargs)

    texto(margem, .46, FAMILIAS[familia][2], fontsize=21, fontweight="bold")
    texto(margem, 1.36, f"{len(itens)} alternativas em escala comum de miniatura", fontsize=10.5)
    x = largura - margem - LARGURA_UTIL * reducao
    texto(x, .96, f"Largura útil A4 · {decimal(LARGURA_UTIL, 1)} cm", fontsize=10)
    for pontos_x, pontos_y in (((x, x + LARGURA_UTIL * reducao), (1.53, 1.53)),
                              ((x, x), (1.40, 1.66)),
                              ((x + LARGURA_UTIL * reducao,) * 2, (1.40, 1.66))):
        figura.add_artist(Line2D([v / largura for v in pontos_x], [1 - v / altura for v in pontos_y],
                                 transform=figura.transFigure, color="#626a71", linewidth=.7))

    topo = 2.55
    for linha, altura_card in zip(linhas, alturas):
        for coluna, item in enumerate(linha):
            x = margem + coluna * (largura_card + espaco)
            figura.add_artist(Rectangle((x / largura, 1 - (topo + altura_card) / altura),
                                         largura_card / largura, altura_card / altura,
                                         transform=figura.transFigure, fill=False,
                                         edgecolor="#c9d0d7", linewidth=.65))
            texto(x + .28, topo + .23, item.id, fontsize=13, fontweight="bold")
            texto(x + largura_card - .28, topo + .27, dimensoes(dim[item.id]), fontsize=10.2, ha="right")
            texto(x + .28, topo + .78, quebrar_nome(item.arquivo + ".pdf"),
                  fontsize=8, fontfamily="DejaVu Sans Mono", linespacing=1.17)
            disposicao = textwrap.fill(item.disposicao, width=56)
            texto(x + .28, topo + 1.57, disposicao, fontsize=9.3, linespacing=1.13)
            w, h = (reducao * v for v in dim[item.id])
            eixo = figura.add_axes([(x + (largura_card - w) / 2) / largura, 1 - (topo + 2.33 + h) / altura,
                                   w / largura, h / altura])
            eixo.set_axis_off()
            with Image.open(pasta / caminho_previa(item)) as imagem:
                eixo.imshow(imagem.convert("RGB"), aspect="auto", interpolation="lanczos")
        topo += altura_card + espaco
    try:
        verificar_layout(figura, [], familia + " comparativo", None)
        salvar(figura, pasta / caminho_comparativo(familia), dpi)
    finally:
        plt.close(figura)


def fonte_a4(itens, dim):
    partes = [
        r"\documentclass[a4paper,11pt]{article}",
        PREAMBULO_LATEX,
        rf"\usepackage[a4paper,total={{{LARGURA_UTIL:.1f}cm,{ALTURA_UTIL:.1f}cm}},centering]{{geometry}}",
        r"\pagestyle{empty}",
        r"\setlength{\parindent}{0pt}",
        r"\begin{document}",
    ]
    for item in itens:
        largura = dim[item.id][0]
        partes.extend((
            rf"\noindent\textbf{{{item.id}}} \hfill {FAMILIAS[item.familia][2]}\par",
            r"\noindent\rule{\textwidth}{0.45pt}\par",
            rf"{{\small Área útil de {decimal(LARGURA_UTIL, 1)} cm \hfill Largura de inserção de {decimal(largura, 1)} cm\par}}",
            r"\medskip",
            r"{\centering",
        ))
        nome = base(item)
        if item.familia == "T":
            partes.append(rf"\input{{{nome.with_suffix('.tex').as_posix()}}}")
        else:
            partes.append(rf"\includegraphics[width={largura:.1f}cm]{{{nome.with_suffix('.pdf').as_posix()}}}")
        partes.extend((r"\par}", r"\clearpage"))
    return "\n".join([*partes, r"\end{document}", ""])


def simular_a4(itens, dim, destino, pasta, dpi_previa):
    papel_x, papel_y = 21, 29.7
    inicio_x = (papel_x - LARGURA_UTIL) / 2 / papel_x
    fim_x = 1 - inicio_x
    with PdfPages(destino, metadata=METADADOS_PDF) as paginas:
        for item in itens:
            figura = plt.figure(figsize=(cm(papel_x), cm(papel_y)), dpi=dpi_previa)
            figura.text(inicio_x, .911, item.id, fontsize=11, fontweight="bold")
            figura.text(fim_x, .911, FAMILIAS[item.familia][2], fontsize=11, ha="right")
            figura.add_artist(Line2D([inicio_x, fim_x], [.899] * 2, transform=figura.transFigure,
                                     color=COR_TEXTO, linewidth=.45))
            largura, altura = dim[item.id]
            figura.text(inicio_x, .883, f"Área útil de {decimal(LARGURA_UTIL, 1)} cm", fontsize=10)
            figura.text(fim_x, .883, f"Largura de inserção de {decimal(largura, 1)} cm", fontsize=10, ha="right")
            w, h = largura / papel_x, altura / papel_y
            eixo = figura.add_axes([(1 - w) / 2, .87 - h, w, h])
            eixo.set_axis_off()
            with Image.open(pasta / base(item).with_suffix(".png")) as imagem:
                eixo.imshow(imagem.convert("RGB"), aspect="auto")
            try:
                paginas.savefig(figura)
            finally:
                plt.close(figura)


def prova_a4(itens, dim, pasta, trabalho, dpi_previa):
    caminho = Path("comparativos/previas_A4.tex")
    (pasta / caminho).write_text(fonte_a4(itens, dim), encoding="utf-8")
    destino = pasta / caminho.with_suffix(".pdf")
    if shutil.which("pdflatex"):
        try:
            pdf = compilar_latex(caminho, pasta, trabalho, "previas_A4")
            shutil.copyfile(pdf, destino)
            return ""
        except (RuntimeError, subprocess.SubprocessError) as erro:
            motivo = str(erro)
    else:
        motivo = "Executável pdflatex indisponível"
    simular_a4(itens, dim, destino, pasta, dpi_previa)
    return motivo
