"""Leitura e conferência das tabelas auditadas usadas nas visualizações."""

import csv
from collections import defaultdict
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from npb_auditoria.model import CLASS, LEVELS, REPETITIONS, VALID
from npb_auditoria.statistics import describe


@dataclass(frozen=True)
class Observacao:
    p: int
    tempo: float
    ic_inf: float
    ic_sup: float
    relativo: float
    speedup: float
    eficiencia: float


@dataclass(frozen=True)
class Dados:
    series: dict[str, tuple[Observacao, ...]]
    n_execucoes: int
    n_configuracoes: int
    n_atipicas: int


def linhas(caminho: Path):
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        yield from csv.DictReader(arquivo)


def chave(linha):
    return linha["campanha"], linha["benchmark"], linha["classe"], int(linha["np"])


def indexar(caminho, fn_chave=chave):
    indice = {}
    for linha in linhas(caminho):
        k = fn_chave(linha)
        if k in indice:
            raise ValueError(f"Chave duplicada em {caminho.name}: {k}")
        indice[k] = linha
    return indice


def conferir(esperado, obtido, campo, k):
    if not isclose(float(esperado), float(obtido), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"Valor divergente para {k}, {campo}: {esperado} e {obtido}")


def melhor(serie):
    return min(serie, key=lambda observacao: observacao.tempo)


def carregar(pasta: Path) -> Dados:
    descritivas = indexar(pasta / "estatisticas_descritivas.csv")
    escala = indexar(pasta / "speedup_eficiencia.csv")
    execucoes = indexar(pasta / "execucoes_consolidadas.csv", lambda r: r["id_auditoria"])
    amostras = defaultdict(list)
    for id_auditoria, linha in execucoes.items():
        if (linha["estado_auditoria"], linha["inclusao_estatistica_principal"]) != (VALID, "sim"):
            raise ValueError(f"Tentativa fora da amostra confirmada desta campanha: {id_auditoria}")
        k = (linha["campanha"], linha["benchmark_auditado"], linha["classe_auditada"],
             int(linha["np_solicitado"]))
        tempo = float(linha["tempo_npb_s"])
        if not isfinite(tempo) or tempo <= 0:
            raise ValueError(f"Tempo NPB inválido para {id_auditoria}")
        amostras[k].append(tempo)

    esperadas = {(b, CLASS, p) for b, niveis in LEVELS.items() for p in niveis}
    if (descritivas.keys() != escala.keys() or descritivas.keys() != amostras.keys()
            or {k[1:] for k in descritivas} != esperadas or len(descritivas) != len(esperadas)):
        raise ValueError("As tabelas e as execuções devem cobrir a mesma grade auditada")

    agrupadas = defaultdict(list)
    for k, medida in descritivas.items():
        _, b, _, p = k
        metricas = escala[k]
        recalculada = describe(amostras[k])
        if any(int(n) != REPETITIONS for n in (medida["n"], metricas["n"], recalculada["n"])):
            raise ValueError(f"Quantidade de repetições divergente para {k}")
        for campo in ("media_s", "dp_amostral_s", "ic95_inf_s", "ic95_sup_s"):
            conferir(medida[campo], recalculada[campo], campo, k)
        ref = float(descritivas[(*k[:3], 1)]["media_s"])
        tempo, inf, sup = (float(medida[c]) for c in ("media_s", "ic95_inf_s", "ic95_sup_s"))
        if not (0 < inf <= tempo <= sup):
            raise ValueError(f"IC de 95% fora da faixa esperada para {k}")
        s, e = float(metricas["speedup"]), float(metricas["eficiencia_pct"])
        conferir(tempo, metricas["media_s"], "media_s", k)
        conferir(ref, metricas["media_ref_1p_s"], "media_ref_1p_s", k)
        conferir(p, metricas["speedup_ideal"], "speedup_ideal", k)
        conferir(ref / tempo, s, "speedup", k)
        conferir(100 * s / p, e, "eficiencia_pct", k)
        relativo = tempo / ref
        conferir(1, relativo * s, "R × S", k)
        agrupadas[b].append(Observacao(p, tempo, inf, sup, relativo, s, e))

    atipicas = indexar(pasta / "observacoes_atipicas.csv", lambda r: r["id_auditoria"])
    for id_auditoria, ponto in atipicas.items():
        if id_auditoria not in execucoes:
            raise ValueError(f"Observação atípica ausente da amostra: {id_auditoria}")
        conferir(ponto["tempo_npb_s"], execucoes[id_auditoria]["tempo_npb_s"],
                 "tempo_npb_s", id_auditoria)

    series = {b: tuple(sorted(agrupadas[b], key=lambda ponto: ponto.p)) for b in LEVELS}
    resumo = indexar(pasta / "resumo_benchmarks.csv", lambda r: r["benchmark"])
    if resumo.keys() != series.keys():
        raise ValueError("O resumo de benchmarks deve cobrir a mesma grade auditada")
    for b, serie in series.items():
        minimo = melhor(serie)
        maior_p = serie[-1]
        for campo, valor in {
            "melhor_np": minimo.p,
            "menor_media_s": minimo.tempo,
            "np_maior_speedup": minimo.p,
            "maior_speedup": minimo.speedup,
            "maior_np_com_tempos": maior_p.p,
            "eficiencia_maior_np_pct": maior_p.eficiencia,
        }.items():
            conferir(resumo[b][campo], valor, campo, b)

    return Dados(series, len(execucoes), len(descritivas), len(atipicas))
