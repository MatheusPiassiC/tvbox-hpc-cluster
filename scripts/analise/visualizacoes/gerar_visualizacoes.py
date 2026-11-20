#!/usr/bin/env python3
"""Regenera o catálogo de alternativas a partir dos CSVs da auditoria NPB."""

import argparse
from pathlib import Path
import os
import sys
from tempfile import TemporaryDirectory


SCRIPT = Path(__file__).resolve()
RAIZ = SCRIPT.parents[3]
AUDITORIA = RAIZ / "results/processed/auditoria"
ENTRADA = AUDITORIA / "tabelas"
SAIDA = RAIZ / ".local/reproducao/visualizacoes"


def resolucao(valor):
    dpi = int(valor)
    if dpi <= 0:
        raise argparse.ArgumentTypeError("informe uma resolução positiva")
    return dpi


def opcoes():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=ENTRADA, help="diretório das tabelas auditadas")
    parser.add_argument("--saida", type=Path, default=SAIDA, help="diretório dos arquivos deste catálogo")
    parser.add_argument("--dpi", type=resolucao, default=300, help="resolução dos PNGs finais (padrão: 300)")
    parser.add_argument("--dpi-previa", type=resolucao, default=150, help="resolução das prévias (padrão: 150)")
    return parser.parse_args()


def publicar(pasta, saida):
    arquivos = sorted(p for p in pasta.rglob("*") if p.is_file())
    catalogo = pasta / "CATALOGO_VISUALIZACOES.md"
    arquivos.remove(catalogo)
    arquivos.append(catalogo)
    destinos = [saida / p.relative_to(pasta) for p in arquivos]
    for destino in destinos:
        if not destino.resolve().is_relative_to(saida) or destino.is_dir():
            raise ValueError(f"Destino de publicação inválido: {destino}")
    for arquivo, destino in zip(arquivos, destinos):
        destino.parent.mkdir(parents=True, exist_ok=True)
        os.replace(arquivo, destino)


def gerar(args, entrada, saida, trabalho):
    sys.dont_write_bytecode = True
    sys.path.append(str(SCRIPT.parents[1] / "auditoria-npb/scripts"))
    os.environ.setdefault("MPLCONFIGDIR", str(trabalho / "matplotlib"))

    import matplotlib
    matplotlib.use("Agg")

    from alternativas import FAMILIAS, FIGURAS, TABELAS
    from catalogo import escrever_catalogo
    from dados import carregar
    from graficos import TIPOGRAFIA, gerar_figura
    from pre_impressao import base, caminho_previa, comparar, gerar_tabelas, prova_a4

    dados = carregar(entrada)
    print(f"Conferidas {dados.n_execucoes} execuções em {dados.n_configuracoes} configurações.", flush=True)
    pasta = trabalho / "artefatos"
    itens = (*FIGURAS, *TABELAS)
    for item in itens:
        (pasta / base(item).parent).mkdir(parents=True, exist_ok=True)
        (pasta / caminho_previa(item).parent).mkdir(parents=True, exist_ok=True)
    dim = {item.id: item.dim for item in FIGURAS}
    latex = trabalho / "latex"
    latex.mkdir()

    with matplotlib.rc_context(TIPOGRAFIA):
        for familia in FAMILIAS:
            membros = [item for item in itens if item.familia == familia]
            if familia == "T":
                dimensoes, motivo_tabelas = gerar_tabelas(membros, dados, pasta, latex, args.dpi, args.dpi_previa)
                dim.update(dimensoes)
            else:
                for item in membros:
                    gerar_figura(item, dados, pasta / base(item), pasta / caminho_previa(item),
                                 args.dpi, args.dpi_previa)
            comparar(familia, membros, dim, pasta, args.dpi, args.dpi_previa)
            print(f"Família {familia}: {len(membros)} alternativas e comparativo.", flush=True)
        motivo_a4 = prova_a4(itens, dim, pasta, latex, args.dpi_previa)

    escrever_catalogo(pasta, saida, entrada, SCRIPT, dados, dim, args.dpi, args.dpi_previa,
                        motivo_tabelas, motivo_a4)
    publicar(pasta, saida)
    for aviso in (motivo_tabelas, motivo_a4):
        if aviso:
            print(aviso, file=sys.stderr)
    print(f"{len(FIGURAS)} figuras, {len(TABELAS)} tabelas e prova A4 em {saida}", flush=True)


def validar_destino(entrada, saida):
    protegidos = [
        entrada,
        AUDITORIA,
        RAIZ / "results/raw",
        RAIZ / "reports/figures/visualizacoes_experimentais",
    ]
    if any(saida.is_relative_to(p) or p.is_relative_to(saida) for p in protegidos):
        raise SystemExit("Escolha um destino separado das tabelas de entrada, da auditoria e dos dados brutos.")


def main():
    args = opcoes()
    entrada, saida = args.entrada.resolve(), args.saida.resolve()
    validar_destino(entrada, saida)
    saida.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".geracao-", dir=saida) as temporario:
        gerar(args, entrada, saida, Path(temporario))


if __name__ == "__main__":
    main()
