"""Desenho das figuras e verificações dos artistas antes da exportação."""

from itertools import combinations

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.container import ErrorbarContainer
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.text import Text
from matplotlib.ticker import MaxNLocator, NullLocator
import numpy as np

from alternativas import TODOS


COR_TEXTO = "#20252b"
COR_IDEAL = "#636870"
TRACEJADO_IDEAL = (0, (3.5, 2.5))
ESTILOS = {
    "EP": ("#006ba4", "o", "-"),
    "IS": ("#b95100", "s", (0, (5, 1.7))),
    "CG": ("#007655", "^", (0, (2, 1.5))),
    "MG": ("#774ca3", "D", (0, (4, 1.5, 1.1, 1.5))),
    "FT": ("#a63245", "v", (0, (1, 1.55))),
    "LU": ("#237c91", "P", (0, (6, 1.6, 2, 1.6))),
    "BT": ("#7b6200", "X", (0, (3, 1.35, 1, 1.35, 1, 1.35))),
    "SP": ("#41454c", "<", (0, (7, 1.55))),
}
METADADOS_PDF = {"Creator": "Catálogo experimental NPB", "CreationDate": None, "ModDate": None}
TIPOGRAFIA = {
    "font.family": "STIXGeneral",
    "mathtext.fontset": "stix",
    "font.size": 8.6,
    "axes.labelsize": 9.2,
    "axes.labelcolor": COR_TEXTO,
    "axes.titlecolor": COR_TEXTO,
    "text.color": COR_TEXTO,
    "xtick.color": COR_TEXTO,
    "ytick.color": COR_TEXTO,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.unicode_minus": False,
    "pdf.fonttype": 42,
    "savefig.facecolor": "white",
    "savefig.bbox": None,
}
ROTULOS_Y = {
    "tempo": "Tempo médio do NPB (s)",
    "relativo": "Tempo normalizado (R)",
    "speedup": "Speedup (×)",
    "eficiencia": "Eficiência (%)",
}


def cm(valor):
    return valor / 2.54


def decimal(valor, casas):
    return f"{valor:.{casas}f}".replace(".", ",")


def numero(valor):
    return f"{valor:.6f}".rstrip("0").rstrip(".").replace(".", ",")


def estilo(benchmark):
    cor, marcador, traco = ESTILOS[benchmark]
    return dict(color=cor, marker=marcador, linestyle=traco, linewidth=1.16,
                markersize=3.7, markerfacecolor="white", markeredgewidth=.85,
                markeredgecolor=cor)


def escala_vertical(eixo, painel, conteudo, dados):
    metrica = painel.metrica
    log = painel.escala_y == "log"
    if log:
        eixo.set_yscale("log")

    if metrica == "tempo":
        minimo = min(p.ic_inf for p in conteudo)
        maximo = max(p.ic_sup for p in conteudo)
        limites = (minimo / 1.35, maximo * 1.40) if log else (0, maximo * 1.09)
        marcas = (1, 3, 10, 30, 100, 300) if log else MaxNLocator(nbins=4).tick_values(*limites)
    elif metrica == "relativo":
        base = conteudo if painel.escala_y == "local" else [p for serie in dados.series.values() for p in serie]
        minimo, maximo = min(p.relativo for p in base), max(p.relativo for p in base)
        limites = (minimo / 1.25, maximo * 1.30) if log else (0, maximo * 1.11)
        marcas = (.03, .1, .3, 1, 3) if log else ((0, .5, 1) if maximo < 1.5 else (0, 1, 2, 3))
    elif metrica == "speedup":
        limites = (.23, 40) if log else (0, 34.5)
        marcas = (.25, .5, 1, 2, 4, 8, 16, 32) if log else (0, 8, 16, 24, 32)
    else:
        limites = (.87, 156) if log else (0, 135)
        marcas = (1, 2, 5, 10, 20, 50, 100) if log else (0, 25, 50, 75, 100, 125)

    marcas = [m for m in marcas if limites[0] <= m <= limites[1]]
    if log:
        rotulos = [numero(m) for m in marcas]
    else:
        casas = max((len(numero(m).partition(",")[2]) for m in marcas), default=0)
        rotulos = [decimal(m, casas) for m in marcas]
    eixo.set_yticks(marcas, rotulos)
    # Mantém o tick zero e separa dele os símbolos de valores muito baixos.
    base_visual = -limites[1] * .032 if not log else limites[0]
    eixo.set_ylim(base_visual, limites[1])
    eixo.yaxis.set_minor_locator(NullLocator())


def preparar_eixo(eixo, painel, escalax, processos):
    if escalax == "log":
        eixo.set_xscale("log", base=2)
        limites = (processos[0] / 1.2, processos[-1] * 1.2)
    else:
        limites = (.25, processos[-1] + 1.25)
    eixo.set_xticks(processos, [str(p) for p in processos])
    eixo.set_xlim(*limites)
    eixo.xaxis.set_minor_locator(NullLocator())
    eixo.set_axisbelow(True)
    eixo.grid(axis="y", color="#dce1e4", linewidth=.48)
    eixo.spines[["top", "right"]].set_visible(False)
    for lado in ("bottom", "left"):
        eixo.spines[lado].set(color="#838b93", linewidth=.55)
    eixo.tick_params(axis="both", length=2.3, width=.55, pad=2.4)
    if painel.titulo:
        eixo.set_title(painel.titulo, fontsize=9.3, fontweight="bold", pad=3.8, loc="left")


def desenhar_referencia(eixo, metrica, processos):
    traco = dict(color=COR_IDEAL, linestyle=TRACEJADO_IDEAL, linewidth=.88, zorder=2)
    if metrica == "speedup":
        # Amostra apenas a função teórica. Os marcadores das curvas vêm dos CSVs.
        p = np.geomspace(processos[0], processos[-1], 320)
        return eixo.plot(p, p, **traco)[0]
    if metrica in ("relativo", "eficiencia"):
        return eixo.axhline(1 if metrica == "relativo" else 100, **traco)
    return None


def validar_painel(eixo, especificacao, processos, curvas, referencia):
    x_min, x_max = eixo.get_xlim()
    y_min, y_max = eixo.get_ylim()
    np.testing.assert_array_equal(eixo.get_xticks(), processos)
    for p, y, linha, barras in curvas:
        np.testing.assert_array_equal(linha.get_xdata(), p)
        np.testing.assert_array_equal(linha.get_ydata(), y)
        if not (x_min < min(p) <= max(p) < x_max and y_min < min(y) <= max(y) < y_max):
            raise ValueError(f"Pontos fora dos limites no painel {especificacao}")
        if barras is not None:
            segmentos, inf, sup = barras
            np.testing.assert_allclose(segmentos[:, 0, 0], p)
            np.testing.assert_allclose(segmentos[:, 1, 0], p)
            np.testing.assert_allclose(segmentos[:, 0, 1], inf)
            np.testing.assert_allclose(segmentos[:, 1, 1], sup)
            if not y_min < min(inf) <= max(sup) < y_max:
                raise ValueError(f"IC fora dos limites no painel {especificacao}")
    if referencia is not None:
        valores = referencia.get_ydata()
        if especificacao.metrica == "speedup":
            np.testing.assert_array_equal(referencia.get_xdata(), valores)
            np.testing.assert_array_equal([valores[0], valores[-1]], [processos[0], processos[-1]])
        else:
            np.testing.assert_array_equal(valores, [1, 1] if especificacao.metrica == "relativo" else [100, 100])
        if not y_min < min(valores) <= max(valores) < y_max:
            raise ValueError(f"Referência fora dos limites no painel {especificacao}")


def desenhar_painel(eixo, painel, especificacao, dados):
    conteudo = [p for b in painel.series for p in dados.series[b]]
    processos = sorted({p.p for p in conteudo})
    preparar_eixo(eixo, painel, especificacao.escala_x, processos)
    escala_vertical(eixo, painel, conteudo, dados)
    referencia = desenhar_referencia(eixo, painel.metrica, processos)
    curvas = []
    for b in painel.series:
        serie = dados.series[b]
        p = [obs.p for obs in serie]
        y = np.array([getattr(obs, painel.metrica) for obs in serie])
        linha = eixo.plot(p, y, **estilo(b), zorder=3)[0]
        barras = None
        if painel.metrica == "tempo":
            inf, sup = (np.array([getattr(obs, campo) for obs in serie]) for campo in ("ic_inf", "ic_sup"))
            erros = eixo.errorbar(p, y, yerr=[y - inf, sup - y], fmt="none", ecolor=ESTILOS[b][0],
                                  elinewidth=.84, capsize=2.15, capthick=.8, zorder=4)
            barras = np.asarray(erros.lines[2][0].get_segments()), inf, sup
        curvas.append((p, y, linha, barras))
    validar_painel(eixo, painel, processos, curvas, referencia)


def legenda_media():
    ponto = Line2D([], [], color=COR_IDEAL, marker="o", markerfacecolor="white", markersize=3.7)
    tampa = Line2D([], [], color=COR_IDEAL, marker="_", linestyle="none", markersize=4.3)
    barras = LineCollection([], colors=[COR_IDEAL], linewidths=.84)
    return ErrorbarContainer((ponto, (tampa, tampa), (barras,)), has_yerr=True)


def legenda(figura, eixos, especificacao):
    sobrepostas = any(len(painel.series) > 1 for painel in especificacao.paineis)
    benchmarks = [b for b in TODOS if any(b in painel.series for painel in especificacao.paineis)]
    rotulos = benchmarks[:] if sobrepostas else []
    simbolos = [Line2D([], [], **estilo(b)) for b in rotulos]
    referencias = {
        "A": "Média e IC de 95%",
        "B": "Referência R = 1",
        "C": "Ideal S = p",
        "D": "Referência 100%",
        "E": "Referência ideal",
    }
    ref = (legenda_media() if especificacao.familia == "A" else
           Line2D([], [], color=COR_IDEAL, linestyle=TRACEJADO_IDEAL, linewidth=.88))
    simbolos.append(ref)
    rotulos.append(referencias[especificacao.familia])
    largura = especificacao.dim[0]
    opcoes = dict(frameon=False, fontsize=8.3, handlelength=2.6, columnspacing=1.2,
                  labelspacing=.38, handletextpad=.5, borderaxespad=.36)
    if especificacao.legenda == "celula":
        return eixos[-1].legend(simbolos, rotulos, loc="center", **opcoes)
    loc = "outside upper center" if especificacao.legenda == "superior" else "lower center"
    return figura.legend(simbolos, rotulos, loc=loc, ncols=3 if largura < 9 else 5, **opcoes)


def rotular(figura, eixos, especificacao, legenda_):
    escala_x = r" ($\log_2$)" if especificacao.escala_x == "log" else ""
    rotulo_x = f"Processos MPI{escala_x}"
    if especificacao.legenda == "inferior":
        renderizador = figura.canvas.get_renderer()
        espaco = .035 / figura.get_figheight()
        y = legenda_.get_window_extent(renderizador).y1 / figura.bbox.height + espaco
        xlabel = figura.supxlabel(rotulo_x, fontsize=9.2, y=y)
        inicio_paineis = xlabel.get_window_extent(renderizador).y1 / figura.bbox.height + espaco
        figura.get_layout_engine().set(rect=(0, inicio_paineis, 1, 1 - inicio_paineis))
    else:
        figura.supxlabel(rotulo_x, fontsize=9.2)
    paineis = especificacao.paineis
    rotulos = [ROTULOS_Y[p.metrica] + ("\nEscala logarítmica" if p.escala_y == "log" else "") for p in paineis]
    if especificacao.id == "C06":
        rotulos[0] += "\nEscala linear"
    if especificacao.id == "B03":
        rotulos = [r + "\nEscalas y por painel" for r in rotulos]
    if len(set(rotulos)) == 1:
        figura.supylabel(rotulos[0], fontsize=9.2)
    else:
        for eixo, rotulo in zip(eixos, rotulos):
            eixo.set_ylabel(rotulo, labelpad=4)
        figura.align_ylabels()


def verificar_layout(figura, eixos, chave, legenda_):
    figura.canvas.draw()
    renderizador = figura.canvas.get_renderer()
    textos = list(figura.texts)
    for eixo in eixos:
        textos += [artista for artista in eixo.get_children() if isinstance(artista, Text)]
        for direcao in (eixo.xaxis, eixo.yaxis):
            textos.extend([direcao.label, *direcao.get_majorticklabels()])
        verificar_marcadores(eixo, chave, renderizador)
    if legenda_ is not None:
        textos.extend(legenda_.get_texts())
        caixa = legenda_.get_window_extent(renderizador)
        if any(caixa.overlaps(eixo.get_window_extent(renderizador)) for eixo in eixos):
            raise ValueError(f"{chave}: legenda sobre os dados")
    caixas = [(t.get_text(), t.get_window_extent(renderizador)) for t in textos
              if t.get_visible() and t.get_text().strip()]
    tela = figura.bbox
    margem = renderizador.points_to_pixels(.30)
    for texto, caixa in caixas:
        if (caixa.x0 < -margem or caixa.y0 < -margem or
                caixa.x1 > tela.width + margem or caixa.y1 > tela.height + margem):
            raise ValueError(f"{chave}: texto fora da figura: {texto!r}")
    for (texto_a, a), (texto_b, b) in combinations(caixas, 2):
        sobreposicao_x = min(a.x1, b.x1) - max(a.x0, b.x0)
        sobreposicao_y = min(a.y1, b.y1) - max(a.y0, b.y0)
        if sobreposicao_x > margem and sobreposicao_y > margem:
            raise ValueError(f"{chave}: colisão entre {texto_a!r} e {texto_b!r}")


def verificar_marcadores(eixo, chave, renderizador):
    janela = eixo.get_window_extent(renderizador)
    for linha in eixo.lines:
        if linha.get_marker() in (None, "None", "", " "):
            continue
        simbolo = MarkerStyle(linha.get_marker())
        caixa = simbolo.get_path().get_extents(simbolo.get_transform())
        escala = renderizador.points_to_pixels(linha.get_markersize())
        contorno = renderizador.points_to_pixels(linha.get_markeredgewidth() / 2)
        x, y = linha.get_transform().transform(np.column_stack(linha.get_data(orig=False))).T
        if (min(x) + caixa.x0 * escala - contorno < janela.x0 or
                max(x) + caixa.x1 * escala + contorno > janela.x1 or
                min(y) + caixa.y0 * escala - contorno < janela.y0 or
                max(y) + caixa.y1 * escala + contorno > janela.y1):
            raise ValueError(f"{chave}: marcador ou tampa de IC junto à borda do painel")


def salvar(figura, caminho, dpi, previa=None, dpi_previa=150):
    figura.savefig(caminho.with_suffix(".pdf"), metadata=METADADOS_PDF)
    figura.savefig(caminho.with_suffix(".png"), dpi=dpi)
    if previa is not None:
        figura.savefig(previa, dpi=dpi_previa)


def gerar_figura(especificacao, dados, caminho, previa, dpi, dpi_previa):
    colunas, linhas = especificacao.grade
    grade = {"width_ratios": (1, 1.19)} if especificacao.id == "C06" else {}
    figura, eixos = plt.subplots(linhas, colunas, figsize=tuple(map(cm, especificacao.dim)),
                                  sharex="col" if especificacao.eixo_x_comum else False,
                                  layout="constrained", squeeze=False, gridspec_kw=grade,
                                  dpi=dpi_previa)
    figura.get_layout_engine().set(w_pad=.051, h_pad=.042, wspace=.048, hspace=.06)
    eixos = list(eixos.flat)
    ocupados = eixos[:len(especificacao.paineis)]
    try:
        for eixo, painel in zip(ocupados, especificacao.paineis):
            desenhar_painel(eixo, painel, especificacao, dados)
        for eixo in eixos[len(ocupados):]:
            eixo.set_axis_off()
        legenda_ = legenda(figura, eixos, especificacao)
        rotular(figura, ocupados, especificacao, legenda_)
        verificar_layout(figura, ocupados, especificacao.id, legenda_)
        figura.set_layout_engine("none")
        salvar(figura, caminho, dpi, previa, dpi_previa)
    finally:
        plt.close(figura)
