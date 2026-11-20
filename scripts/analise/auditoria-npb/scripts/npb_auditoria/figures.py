"""Figuras exploratórias em escala por benchmark, com saída PNG e PDF."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
import numpy as np

from .model import CLASS, LEVELS, REPETITIONS
from .statistics import Group, value

COLORS = ("#176987", "#c36625", "#147f68", "#8a5892", "#91741d", "#3f52a2")
TITLE_COLOR = "#192b39"
GRID_COLOR = "#dfe6eb"
META = {"Creator": "Auditoria NPB", "CreationDate": None, "ModDate": None}
FIGURES = (
    "tempo_medio_npb", "speedup", "eficiencia_paralela", "distribuicao_tempos",
    "completude_experimental", "comportamento_temporal",
)


def save(fig: Figure, target: Path, name: str) -> None:
    fig.savefig(target / f"{name}.png", dpi=180, facecolor="white", metadata={"Software": "Auditoria NPB"})
    fig.savefig(target / f"{name}.pdf", facecolor="white", metadata=META)
    plt.close(fig)


def facets(
    groups: list[Group], target: Path, name: str, title: str, ylabel: str,
    panel: Callable[[Axes, list[Group]], None], *, x_label: str = "Processos MPI",
) -> None:
    by_series: dict[tuple, list[Group]] = defaultdict(list)
    for group in groups:
        if group.reference:
            by_series[group.series].append(group)
    n_columns = min(4, max(1, len(by_series)))
    n_rows = max(1, (len(by_series) + n_columns - 1) // n_columns)
    fig, axes = plt.subplots(n_rows, n_columns, squeeze=False, figsize=(3.75 * n_columns, 3.6 * n_rows + .55), layout="constrained")
    counts = {b: sum(series[0] == b for series in by_series) for b in LEVELS}
    for axis, ((benchmark, _, campaign), subset) in zip(axes.flat, by_series.items()):
        label = benchmark if counts[benchmark] == 1 else f"{benchmark} · {campaign.rsplit('/', 1)[-1]}"
        axis.set_title(label, loc="left", fontsize=12, fontweight="bold", color=TITLE_COLOR)
        axis.spines[["right", "top"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#abbcc7")
        axis.grid(axis="y", color=GRID_COLOR, linewidth=.65)
        axis.set_axisbelow(True)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
        panel(axis, subset)
    for axis in list(axes.flat)[len(by_series):]:
        axis.set_visible(False)
    fig.suptitle(title, fontsize=17, color=TITLE_COLOR, fontweight="bold")
    fig.supxlabel(x_label, fontsize=11)
    fig.supylabel(ylabel, fontsize=11)
    save(fig, target, name)


def ticks(axis: Axes, groups: list[Group], *, annotate: bool = True) -> list[int]:
    positions = list(range(len(groups)))
    labels = []
    for group in groups:
        n = group.description["n"]
        labels.append(f"{group.processes}\n({n}/{REPETITIONS})" if annotate and n != REPETITIONS else str(group.processes))
    axis.set_xticks(positions, labels)
    axis.set_xlim(-.46, len(groups) - .54)
    return positions


def means_panel(axis: Axes, groups: list[Group]) -> None:
    positions = ticks(axis, groups)
    means = np.array([group.description["media_s"] if group.sample else np.nan for group in groups])
    if not np.isfinite(means).any():
        axis.text(.5, .5, "Sem tempos elegíveis", transform=axis.transAxes, ha="center", color="#687c88")
        return
    axis.plot(positions, means, "o-", color=COLORS[0], linewidth=1.4, markersize=5)
    for x, group in zip(positions, groups):
        d = group.description
        if d["ic95_inf_s"] is not None:
            axis.errorbar(x, d["media_s"], yerr=[[d["media_s"] - d["ic95_inf_s"]],
                                                [d["ic95_sup_s"] - d["media_s"]]],
                          fmt="none", color=COLORS[0], capsize=3, linewidth=1.3)


def metric_panel(axis: Axes, groups: list[Group], field: str) -> None:
    processes = [group.processes for group in groups]
    points = [group.scaling[field] if group.scaling[field] is not None else np.nan for group in groups]
    axis.set_xscale("log", base=2)
    axis.set_xticks(processes, [str(p) for p in processes])
    axis.tick_params(axis="x", which="minor", bottom=False)
    if field == "speedup":
        axis.plot(processes, processes, "--", color="#697782", linewidth=1.1, label="Ideal S(p) = p")
        axis.plot(processes, points, "o-", color=COLORS[0], linewidth=1.4, markersize=5, label="Observado")
        axis.legend(loc="upper left", frameon=False, fontsize=8, handlelength=1.5)
    else:
        axis.axhline(100, color="#697782", linestyle="--", linewidth=1.1)
        axis.plot(processes, points, "o-", color=COLORS[0], linewidth=1.4, markersize=5)
        axis.set_ylim(0, max(106, max((p * 1.07 for p in points if np.isfinite(p)), default=0)))
    if not any(np.isfinite(p) for p in points):
        axis.text(.5, .48, "Referência comparável ausente", transform=axis.transAxes, ha="center", color="#687c88")


def distribution_panel(axis: Axes, groups: list[Group]) -> None:
    positions = ticks(axis, groups)
    data = [(x, [value(item) for item in group.sample]) for x, group in zip(positions, groups) if group.sample]
    if not data:
        return
    axis.boxplot([points for _, points in data], positions=[x for x, _ in data], widths=.42,
                 manage_ticks=False, patch_artist=True, showfliers=False, whis=1.5,
                 boxprops={"facecolor": "#d3e8f0", "edgecolor": COLORS[0]},
                 medianprops={"color": "#13445a", "linewidth": 1.3},
                 whiskerprops={"color": COLORS[0]}, capprops={"color": COLORS[0]})
    for x, points in data:
        offsets = np.linspace(-.14, .14, len(points)) if len(points) > 1 else [0]
        axis.scatter(x + np.asarray(offsets), points, s=13, color=COLORS[0], alpha=.8, zorder=4, linewidths=0)


def completeness(groups: list[Group], target: Path) -> None:
    processes = sorted({p for levels in LEVELS.values() for p in levels})
    grouped: dict[tuple[str, str, str], dict[int, Group]] = defaultdict(dict)
    for group in groups:
        if group.reference:
            grouped[group.series][group.processes] = group
    matrix = np.full((len(grouped), len(processes)), -1, dtype=int)
    labels = []
    for yi, ((benchmark, _, campaign), entries) in enumerate(grouped.items()):
        labels.append(benchmark if sum(b == benchmark for b, _, _ in grouped) == 1 else f"{benchmark} · {campaign.rsplit('/', 1)[-1]}")
        for xi, p in enumerate(processes):
            if p in entries:
                matrix[yi, xi] = REPETITIONS - len(entries[p].coverage["blocos_sem_valida_na_referencia"])
    fig, axis = plt.subplots(figsize=(10.6, 4 + .29 * len(grouped)), layout="constrained")
    colors = ListedColormap(["#edf1f3", "#f7d4bd", "#feecc1", "#c3e7dc"])
    axis.pcolormesh(np.arange(len(processes) + 1) - .5, np.arange(len(labels) + 1) - .5, matrix,
                    cmap=colors, norm=BoundaryNorm([-1.5, -.5, .5, 9.5, 10.5], colors.N), shading="flat")
    axis.invert_yaxis()
    axis.set_xticks(range(len(processes)), processes)
    axis.set_yticks(range(len(labels)), labels)
    axis.set_xlabel("Processos MPI")
    axis.set_title("Repetições válidas por configuração planejada", loc="left", fontsize=16, pad=13, color=TITLE_COLOR)
    for y, x in np.ndindex(matrix.shape):
        n = matrix[y, x]
        axis.text(x, y, "—" if n < 0 else f"{n}/{REPETITIONS}", ha="center", va="center", color=TITLE_COLOR, fontsize=10)
    axis.spines[:].set_visible(False)
    axis.set_xticks(np.arange(-.5, len(processes), 1), minor=True)
    axis.set_yticks(np.arange(-.5, len(labels), 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=1.6)
    axis.tick_params(which="both", length=0, pad=5)
    axis.text(0, -.16, "—  Processo fora da grade do benchmark", transform=axis.transAxes, color="#556674", fontsize=9)
    save(fig, target, FIGURES[4])


def temporal_panel(axis: Axes, groups: list[Group]) -> None:
    axis.axhline(0, color="#8d9ba7", linewidth=.9)
    axis.set_xticks(range(1, REPETITIONS + 1))
    axis.tick_params(axis="x", labelsize=8)
    axis.set_xlim(.7, REPETITIONS + .3)
    for index, group in enumerate(groups):
        ordered = {item.data["bloco_observado"]: value(item) for item in group.sample if item.data["ordem_confiavel"]}
        if not ordered:
            continue
        central = group.description["mediana_s"]
        points = [100 * (ordered[b] / central - 1) if b in ordered else np.nan for b in range(1, REPETITIONS + 1)]
        axis.plot(range(1, REPETITIONS + 1), points, "o-", color=COLORS[index % len(COLORS)],
                  linewidth=.9, markersize=3, label=f"{group.processes} p")
    if axis.lines[1:]:
        axis.legend(fontsize=7, frameon=False, ncol=3, loc="best", handlelength=1.3,
                    borderaxespad=.25, columnspacing=.6)
    else:
        axis.text(.5, .56, "Ordem não estabelecida", transform=axis.transAxes, ha="center", color="#687c88")


def make_all(groups: list[Group], target: Path) -> None:
    """Usa painéis por campanha, com lacunas explícitas em amostras incompletas."""
    target.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42,
                         "axes.labelcolor": TITLE_COLOR, "xtick.color": TITLE_COLOR, "ytick.color": TITLE_COLOR}):
        facets(groups, target, FIGURES[0], "Tempo médio do NPB e IC de 95%", "Tempo do NPB (s)", means_panel)
        facets(groups, target, FIGURES[1], "Speedup por quantidade de processos", "Speedup",
               lambda axis, subset: metric_panel(axis, subset, "speedup"))
        facets(groups, target, FIGURES[2], "Eficiência paralela", "Eficiência (%)",
               lambda axis, subset: metric_panel(axis, subset, "eficiencia_pct"))
        facets(groups, target, FIGURES[3], "Distribuição das repetições válidas", "Tempo do NPB (s)", distribution_panel)
        completeness(groups, target)
        facets(groups, target, FIGURES[5], "Variação temporal por bloco", "Diferença da mediana da configuração (%)",
               temporal_panel, x_label="Bloco observado")
