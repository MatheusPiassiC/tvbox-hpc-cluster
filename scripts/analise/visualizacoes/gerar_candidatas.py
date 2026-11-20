#!/usr/bin/env python3
"""Gera as figuras candidatas, a tabela e a prova de inserção em A4."""

import argparse
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from gerar_visualizacoes import ENTRADA, validar_destino


SCRIPT = Path(__file__).resolve()
RAIZ = SCRIPT.parents[3]
DESTINO = RAIZ / ".local/reproducao/candidatas-tcc"
DPI_PNG = 600
DPI_PROVA = 150
TAMANHO_TICKS_X = 8.5
TAMANHO_TICKS_Y = 9
ALTURA_FIGURA = 10.2
PROVA = "PROVA_INSERCAO_TCC"
EXEMPLO = "exemplo_inclusao_T01"
FIGURAS_SELECIONADAS = {
    "A01": ("A01_tempo_medio_8paineis_4x2",
            r"Tempo médio do NPB por número de processos MPI. Barras de erro representam os ICs bilaterais "
            r"de 95\% das médias. As escalas verticais são independentes."),
    "C03": ("C03_speedup_8paineis_4x2",
            r"Speedup em relação à execução com um processo MPI. A linha tracejada representa o "
            r"speedup ideal $S(p)=p$."),
    "D03": ("D03_eficiencia_8paineis_4x2",
            r"Eficiência paralela por quantidade de processos MPI. A linha tracejada indica "
            r"o nível de referência de 100\%."),
}


def documento(pasta, nome, preambulo, paginas):
    fonte = pasta / f"{nome}.tex"
    corpo = "\n\n\\clearpage\n\n".join(paginas)
    fonte.write_text(f"{preambulo}\n\\begin{{document}}\n{corpo}\n\\end{{document}}\n", encoding="utf-8")
    return fonte


def inserir_figura(identificador, nome, legenda):
    return (
        r"\begin{figure}[!ht]" "\n"
        r"  \centering" "\n"
        rf"  \includegraphics[width=\linewidth]{{{nome}.pdf}}" "\n"
        rf"  \caption{{{legenda}}}" "\n"
        rf"  \label{{fig:{identificador.lower()}}}" "\n"
        r"\end{figure}"
    )


def inserir_tabela(nome):
    return (
        r"\begin{table}[!ht]" "\n"
        r"  \centering" "\n"
        r"  \setlength{\belowcaptionskip}{5pt}" "\n"
        r"  \caption{Síntese do desempenho por benchmark.}" "\n"
        r"  \label{tab:sintese-desempenho}" "\n"
        rf"  \input{{{nome}.tex}}" "\n"
        r"  \par\smallskip" "\n"
        r"  {\footnotesize\raggedright" "\n"
        r"    \textit{Nota.} Melhor $p$ é a configuração de menor tempo médio e o IC de 95\% refere-se "
        r"a essa média. O maior $p$ avaliado é 25 para BT e SP e 32 para os demais benchmarks.\par}" "\n"
        r"\end{table}"
    )


def provas_raster(pdf, trabalho, pasta, identificadores):
    subprocess.run(["pdftoppm", "-png", "-r", str(DPI_PROVA), str(pdf), str(trabalho / "pagina")],
                   check=True, timeout=45, capture_output=True)
    paginas = sorted(trabalho.glob("pagina-*.png"))
    if len(paginas) != len(identificadores):
        raise ValueError("A prova A4 deve ter uma página para cada peça")
    previas = pasta / "previas_impressao"
    previas.mkdir()
    for numero, (identificador, png) in enumerate(zip(identificadores, paginas), start=1):
        png.replace(previas / f"{numero:02d}_{identificador}.png")


def gerar(trabalho, entrada):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SCRIPT.parents[1] / "auditoria-npb/scripts"))
    os.environ.setdefault("MPLCONFIGDIR", str(trabalho / "matplotlib"))

    import matplotlib
    matplotlib.use("Agg")

    from alternativas import ALTURA_UTIL, FIGURAS, LARGURA_UTIL, TABELAS
    from dados import carregar
    from graficos import TIPOGRAFIA, decimal, gerar_figura
    from pre_impressao import PREAMBULO_LATEX, base, caminho_previa, compilar_latex, escrever_tabela, exportar_tabela_latex

    dados = carregar(entrada)
    pasta = trabalho / "entrega"
    latex = trabalho / "latex"
    tabela_temp = trabalho / "tabela"
    pasta.mkdir()
    latex.mkdir()
    especificacoes = {figura.id: figura for figura in FIGURAS}
    figuras = [
        (replace(especificacoes[identificador], arquivo=nome, dim=(LARGURA_UTIL, ALTURA_FIGURA)), legenda)
        for identificador, (nome, legenda) in FIGURAS_SELECIONADAS.items()
    ]
    alternativa = replace(especificacoes["D03"], id="D03-2x4", grade=(2, 4), dim=(LARGURA_UTIL, 20.0),
                          arquivo="D03_eficiencia_8paineis_alternativa_2x4")
    figuras.append((alternativa, "Eficiência paralela na disposição 2×4. As escalas e os valores são os mesmos de D03."))
    paginacao = {}
    tipografia = {**TIPOGRAFIA, "xtick.labelsize": TAMANHO_TICKS_X, "ytick.labelsize": TAMANHO_TICKS_Y}
    with matplotlib.rc_context(tipografia):
        for figura, legenda in figuras:
            gerar_figura(figura, dados, pasta / figura.arquivo, None, DPI_PNG, DPI_PROVA)
            paginacao[figura.id] = inserir_figura(figura.id, figura.arquivo, legenda)

    tabela = next(t for t in TABELAS if t.id == "T01")
    (tabela_temp / base(tabela).parent).mkdir(parents=True)
    (tabela_temp / caminho_previa(tabela).parent).mkdir(parents=True)
    escrever_tabela(tabela, dados, tabela_temp)
    exportar_tabela_latex(tabela, tabela_temp, latex, DPI_PNG, DPI_PROVA)
    for extensao in (".tex", ".pdf"):
        arquivo = base(tabela).with_suffix(extensao)
        (tabela_temp / arquivo).replace(pasta / arquivo.name)
    paginacao[tabela.id] = inserir_tabela(tabela.arquivo)

    preambulo = (
        r"\documentclass[a4paper,11pt]{article}" "\n"
        r"\usepackage[brazil]{babel}" + PREAMBULO_LATEX +
        rf"\usepackage[a4paper,total={{{LARGURA_UTIL:.1f}cm,{ALTURA_UTIL:.1f}cm}},centering]{{geometry}}" "\n"
        r"\pagestyle{empty}"
    )
    exemplo = documento(pasta, EXEMPLO, preambulo, [paginacao[tabela.id]])
    compilar_latex(exemplo, pasta, latex, EXEMPLO)

    ordem_paginas = (*FIGURAS_SELECIONADAS, tabela.id, alternativa.id)
    paginas = [
        rf"\noindent\textbf{{{identificador}}}\hfill "
        rf"{{\small Prova A4 · largura útil de {decimal(LARGURA_UTIL, 1)} cm}}\par" + "\n" + paginacao[identificador]
        for identificador in ordem_paginas
    ]
    fonte = documento(pasta, PROVA, preambulo, paginas)
    pdf = compilar_latex(fonte, pasta, latex, PROVA)
    provas_raster(pdf, trabalho, pasta, ordem_paginas)
    pdf.replace(pasta / pdf.name)
    print(f"Conferidas {dados.n_execucoes} execuções em {dados.n_configuracoes} configurações.")
    return pasta


def publicar(pasta, saida):
    arquivos = sorted(p for p in pasta.rglob("*") if p.is_file())
    destinos = [saida / p.relative_to(pasta) for p in arquivos]
    for destino in destinos:
        if not destino.resolve().is_relative_to(saida) or destino.is_dir():
            raise ValueError(f"Destino de publicação inválido: {destino}")
    for arquivo, destino in zip(arquivos, destinos):
        destino.parent.mkdir(parents=True, exist_ok=True)
        arquivo.replace(destino)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=ENTRADA, help="diretório das tabelas auditadas")
    parser.add_argument("--saida", type=Path, default=DESTINO, help="diretório das peças candidatas")
    args = parser.parse_args()
    entrada, saida = args.entrada.resolve(), args.saida.resolve()
    validar_destino(entrada, saida)
    saida.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".geracao-", dir=saida) as temporario:
        publicar(gerar(Path(temporario), entrada), saida)
    print(f"Figuras candidatas, tabela e prova A4 em {saida}")


if __name__ == "__main__":
    main()
