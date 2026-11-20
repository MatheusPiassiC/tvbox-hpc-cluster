"""Cobertura, estatística descritiva, strong scaling e diagnósticos de sensibilidade."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from math import sqrt
from typing import Any, Iterable

import numpy as np
from scipy import stats

from .model import Attempt, Campaign, CLASS, CONFLICT, INVALID, LEVELS, MISSING, REPETITIONS, UNCERTAIN, VALID, first_known
from .validation import MAP_GAPS

DESCRIPTIVE_FIELDS = (
    "n", "media_s", "mediana_s", "dp_amostral_s", "variancia_amostral_s2", "min_s", "max_s",
    "q1_s", "q3_s", "iqr_s", "cv_pct", "ic95_inf_s", "ic95_sup_s", "assimetria_ajustada",
)
SIGNATURE_FIELDS = (
    "plataforma_identificada_sha256", "binario_identificado_sha256", "versao_npb", "tamanho_npb",
    "iteracoes_npb", "compilacao_npb", "compilacao_opcoes_normalizadas", "opcoes_mpi_observadas",
    "governor_previo_observado", "limite_cpufreq_previo_observado_mhz",
)


@dataclass
class Group:
    campaign: Campaign | None
    benchmark: str
    cls: str
    processes: int
    attempts: list[Attempt]
    reference: bool
    coverage: dict[str, Any] = field(default_factory=dict)
    sample: list[Attempt] = field(default_factory=list)
    description: dict[str, Any] = field(default_factory=dict)
    scaling: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> dict[str, Any]:
        return {
            "campanha": self.campaign.key if self.campaign else None,
            "benchmark": self.benchmark, "classe": self.cls, "np": self.processes,
        }

    @property
    def series(self) -> tuple[str, str, str]:
        return self.benchmark, self.cls, self.campaign.key if self.campaign else ""

    def stat_row(self) -> dict[str, Any]:
        fields = ("tentativas_agrupadas", "validas_confirmadas", "invalidas_confirmadas",
                  "inconclusivas", "conflitantes", "meta_validas", "completude")
        return {**self.key, **{key: self.coverage[key] for key in fields}, **self.description}


@dataclass
class Analysis:
    groups: list[Group]
    summaries: list[dict[str, Any]]
    wall: list[dict[str, Any]]
    outliers: list[dict[str, Any]]
    temporal: list[dict[str, Any]]
    sensitivity: list[dict[str, Any]]


def describe(values: Iterable[float]) -> dict[str, Any]:
    """Calcula o IC bilateral t e medidas com quartis por interpolação linear."""
    sample = np.array(list(values), dtype=float)
    n = len(sample)
    result = dict.fromkeys(DESCRIPTIVE_FIELDS)
    result["n"] = n
    if not n:
        return result
    mean = np.mean(sample)
    q1, median, q3 = np.quantile(sample, [.25, .5, .75], method="linear")
    result.update(media_s=float(mean), mediana_s=float(median), min_s=float(sample.min()), max_s=float(sample.max()),
                  q1_s=float(q1), q3_s=float(q3), iqr_s=float(q3 - q1))
    if n > 1:
        variance = np.var(sample, ddof=1)
        error = stats.t.ppf(.975, n - 1) * sqrt(variance / n)
        result.update(dp_amostral_s=sqrt(variance), variancia_amostral_s2=float(variance),
                      cv_pct=100 * sqrt(variance) / float(mean) if mean > 0 else None,
                      ic95_inf_s=float(mean - error), ic95_sup_s=float(mean + error))
    if n > 2 and sample.max() != sample.min():
        result["assimetria_ajustada"] = float(stats.skew(sample, bias=False))
    return result


def value(item: Attempt, field: str = "tempo_npb_s") -> float | None:
    raw = item.data.get(field)
    return float(raw) if raw is not None else None


def precheck(item: Attempt, field: str) -> Any:
    return first_known(item.csv.values.get(field) if item.csv else None,
                       item.log.precheck.get(field) if item.log else None)


def plan_slot(item: Attempt) -> bool:
    block = item.data.get("bloco_observado")
    return (bool(item.data.get("id_repeticao_logica")) and block is not None and 1 <= block <= REPETITIONS
            and item.data.get("fase_observada") in (None, "MEDICAO"))


def signature(sample: list[Attempt]) -> tuple[Any, ...] | None:
    """Exige evidência de comparabilidade da carga e da plataforma para razões de médias."""
    if not sample:
        return None
    signatures = {tuple(item.data.get(key) for key in SIGNATURE_FIELDS) for item in sample}
    if len(signatures) == 1:
        result = next(iter(signatures))
        if None not in result:
            return result
    return None


def is_mixed(sample: list[Attempt]) -> bool:
    return any(len({item.data.get(key) for item in sample if item.data.get(key) is not None}) > 1
               for key in SIGNATURE_FIELDS)


def populate(group: Group, plan_positions: set[tuple[int, int]]) -> None:
    """Distingue contagens de registros, tentativas e posições válidas."""
    items = group.attempts
    states = Counter(item.state for item in items)
    confirmed = [item for item in items if item.state == VALID]
    planned_blocks = {block for block, p in plan_positions if p == group.processes}
    attempts_blocks = {item.data["bloco_observado"] for item in items if item.data["bloco_observado"] is not None}
    valid_blocks = {item.data["bloco_observado"] for item in confirmed if item.data.get("id_repeticao_logica")}
    expected = set(range(1, REPETITIONS + 1))
    valid_required = len(valid_blocks & expected)
    status = "fora_da_referencia"
    if group.reference:
        if not items:
            status = "ausente"
        elif valid_required < REPETITIONS:
            status = "incompleta"
        else:
            status = "completa" if len(valid_blocks) == REPETITIONS else "acima_da_meta"
    selected = [item for item in confirmed if group.reference and plan_slot(item) and value(item) is not None]
    mixed = is_mixed(selected)
    group.sample = [] if mixed else selected
    for item in items:
        item.data["inclusao_estatistica_principal"] = False
        item.data["motivo_inclusao_estatistica"] = (item.state if item.state != VALID else
                                                   "fora_da_grade_de_referencia" if not group.reference or not plan_slot(item)
                                                   else "evidencia_heterogenea_na_configuracao" if mixed else "tempo_npb_ausente")
    for item in group.sample:
        item.data.update(inclusao_estatistica_principal=True, motivo_inclusao_estatistica="posicao_confirmada")
    group.description = describe(value(item) for item in group.sample)
    nodes = sorted({item.data["n_nos_observados"] for item in confirmed if item.data.get("n_nos_observados") is not None})
    layouts = {tuple(sorted(item.data["distribuicao_ranks_observados"].items())) for item in confirmed
               if item.data.get("distribuicao_ranks_observados")}
    valid_ordinals = {item.csv.values["repeticao_valida"] for item in items if item.csv and "repeticao_valida" in item.csv.values}
    group.coverage = {
        **group.key, "na_referencia": group.reference, "completude": status,
        "meta_validas": REPETITIONS if group.reference else None, "posicoes_no_plano": len(planned_blocks),
        "registros_plano": sum(row.values.get("np") == group.processes for row in group.campaign.plan) if group.campaign else 0,
        "registros_csv": sum(len(item.csvs) for item in items), "blocos_txt": sum(len(item.blocks) for item in items),
        "tentativas_agrupadas": len(items), "com_csv_e_txt": sum(bool(item.csvs and item.blocks) for item in items),
        "linhas_csv_aceitas": sum(row.values.get("status") == "VALIDA" for item in items for row in item.csvs),
        "aceitas_coleta": sum(item.data["aceita_coleta"] is True for item in items),
        "ordinais_validos_coletor": len(valid_ordinals),
        "validas_confirmadas": states[VALID], "invalidas_confirmadas": states[INVALID], "inconclusivas": states[UNCERTAIN],
        "conflitantes": states[CONFLICT], "repeticoes_logicas_confirmadas": len(valid_blocks),
        "blocos_no_plano": sorted(planned_blocks), "blocos_observados": sorted(attempts_blocks),
        "blocos_sem_tentativa_na_referencia": sorted(expected - attempts_blocks) if group.reference else None,
        "blocos_sem_valida_na_referencia": sorted(expected - valid_blocks) if group.reference else None,
        "n_estatistica_principal": len(group.sample), "nps_rejeitados_no_stdout": sum(
            any(issue.code == "np_nao_aceito" for issue in item.issues) for item in items),
        "n_nos_observados": nodes, "distribuicoes_observadas": [dict(layout) for layout in sorted(layouts)],
        "serie_tempos_heterogenea": mixed,
    }


def scaling(
    processes: int, mean: float | None, base_mean: float | None,
    current_signature: Any, base_signature: Any,
) -> dict[str, Any]:
    """Razão entre médias comparáveis, com referência estrita de um processo."""
    reason = None
    observed = None
    if mean is None:
        reason = "sem_tempo_na_configuracao"
    elif base_mean is None:
        reason = "sem_referencia_1p"
    elif current_signature is None or base_signature is None or current_signature != base_signature:
        reason = "comparabilidade_nao_demonstrada"
    else:
        observed = base_mean / mean
    return {
        "speedup_ideal": processes, "speedup": observed,
        "desvio_speedup_do_ideal": observed - processes if observed is not None else None,
        "eficiencia": observed / processes if observed is not None else None,
        "eficiencia_pct": 100 * observed / processes if observed is not None else None,
        "superlinear": observed > processes if observed is not None else None,
        "reducao_tempo_vs_1p_pct": 100 * (1 - mean / base_mean) if observed is not None else None,
        "motivo_speedup_ausente": reason,
    }


def transition(a: Group | None, b: Group) -> dict[str, Any]:
    """Compara níveis adjacentes da grade com médias e mapas compatíveis."""
    result = dict.fromkeys(("np_anterior", "ganho_tempo_vs_anterior_pct", "transicao", "nos_anteriores", "nos_atuais", "escopo_transicao"))
    actual_nodes = b.coverage["n_nos_observados"]
    result["nos_atuais"] = actual_nodes[0] if len(actual_nodes) == 1 else None
    if a is None:
        return result
    previous_nodes = a.coverage["n_nos_observados"]
    result.update(np_anterior=a.processes, nos_anteriores=previous_nodes[0] if len(previous_nodes) == 1 else None)
    if result["nos_atuais"] is not None and result["nos_anteriores"] is not None:
        result["escopo_transicao"] = ("intranó" if result["nos_atuais"] == result["nos_anteriores"] == 1 else
                                     "mudança de nós" if result["nos_atuais"] != result["nos_anteriores"] else "mesmo nº de nós")
    a_mean, b_mean = a.description["media_s"], b.description["media_s"]
    a_signature, b_signature = signature(a.sample), signature(b.sample)
    if a_mean is not None and b_mean is not None and a_signature is not None and a_signature == b_signature:
        result["ganho_tempo_vs_anterior_pct"] = 100 * (1 - b_mean / a_mean)
        result["transicao"] = "melhora" if b_mean < a_mean else "piora" if b_mean > a_mean else "igual nas médias"
    return result


def outlier_rows(group: Group) -> list[dict[str, Any]]:
    """Sinaliza os pontos externos às cercas de Tukey e estima sua influência individual."""
    count, iqr = group.description["n"], group.description["iqr_s"]
    if count < 4 or not iqr:
        return []
    q1, q3 = group.description["q1_s"], group.description["q3_s"]
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    result = []
    for item in group.sample:
        time = value(item)
        if low - 1e-10 <= time <= high + 1e-10:
            continue
        others = [other for other in group.sample if other is not item]
        mean_without = float(np.mean([value(other) for other in others]))
        temp = precheck(item, "temp_max_antes_c")
        other_temps = [float(t) for other in others if (t := precheck(other, "temp_max_antes_c")) is not None]
        result.append({
            **group.key, "id_auditoria": item.id, "exec_id": item.key, "bloco": item.data["bloco_observado"],
            "inicio": item.data["inicio_observado"], "tempo_npb_s": time, "tempo_parede_s": value(item, "tempo_parede_coletor_s"),
            "tempo_inicializacao_npb_s": value(item, "tempo_inicializacao_npb_s"),
            "cerca_inferior_s": low, "cerca_superior_s": high, "tipo": "rápido" if time < low else "lento",
            "media_original_s": group.description["media_s"], "media_sem_ponto_s": mean_without,
            "variacao_media_sem_ponto_pct": 100 * (mean_without / group.description["media_s"] - 1),
            "temp_max_antes_c": temp, "mediana_temp_antes_demais_c": float(np.median(other_temps)) if other_temps else None,
            "cpu_max_antes_pct": precheck(item, "cpu_ocupada_max_antes_pct"),
            "mem_min_antes_mb": precheck(item, "mem_disp_min_antes_mb"),
            "fonte_csv": item.csv.ref if item.csv else None,
            "fonte_npb": item.log.source.ref(item.data["linha_tempo_npb"]) if item.log else None,
        })
    return result


def temporal_row(group: Group) -> dict[str, Any]:
    """Resume posição da primeira medida, tendência ordinal e dependência de curto prazo."""
    sample = sorted((item for item in group.sample if item.data["ordem_confiavel"]),
                    key=lambda item: item.data["ordem_execucao"])
    temporal = {
        **group.key, "n_com_ordem": len(sample), "primeiro_bloco": None, "primeiro_tempo_s": None,
        "media_dos_seguintes_s": None,
        "primeiro_vs_seguintes_pct": None, "metade_final_vs_inicial_pct": None,
        "rho_spearman_ordem": None, "r_lag1": None,
    }
    if not sample:
        return temporal
    blocks = [item.data["bloco_observado"] for item in sample]
    timings = np.array([value(item) for item in sample])
    n = len(sample)
    temporal.update(primeiro_bloco=blocks[0], primeiro_tempo_s=float(timings[0]))
    if n >= 2:
        following = float(timings[1:].mean())
        temporal.update(media_dos_seguintes_s=following, primeiro_vs_seguintes_pct=100 * (timings[0] / following - 1))
    if n >= 4:
        half = n // 2
        temporal["metade_final_vs_inicial_pct"] = float(100 * (timings[-half:].mean() / timings[:half].mean() - 1))
        if timings.min() != timings.max():
            temporal["rho_spearman_ordem"] = float(stats.spearmanr(blocks, timings).statistic)
        if all(b - a == 1 for a, b in zip(blocks, blocks[1:])) and np.ptp(timings[:-1]) and np.ptp(timings[1:]):
            temporal["r_lag1"] = float(np.corrcoef(timings[:-1], timings[1:])[0, 1])
    return temporal


def sensitivity_sample(group: Group, policy: str, temperature: int | None) -> list[Attempt]:
    if policy == "limite_termico_comum":
        if temperature is None:
            return []
        return [item for item in group.sample if (temp := precheck(item, "temp_max_antes_c")) is not None and temp <= temperature]
    relaxed = [
        item for item in group.attempts if item.state == UNCERTAIN and plan_slot(item) and value(item) is not None
        and {issue.code for issue in item.issues if issue.level == MISSING} <= MAP_GAPS
    ]
    candidates = [*group.sample, *relaxed] if group.reference and not group.coverage["serie_tempos_heterogenea"] else []
    slots = Counter(item.data["id_repeticao_logica"] for item in candidates)
    return [item for item in candidates if slots[item.data["id_repeticao_logica"]] == 1] if not is_mixed(candidates) else []


def build_analysis(
    campaigns: list[Campaign], attempts: list[Attempt],
    plans: dict[str, dict[tuple[int, int], list]],
) -> Analysis:
    """Preserva cada campanha como série, inclusive quando arquivos adicionais são incluídos."""
    by_config: dict[tuple[str, int], list[Attempt]] = defaultdict(list)
    for item in attempts:
        item.data.setdefault("inclusao_estatistica_principal", False)
        item.data.setdefault("motivo_inclusao_estatistica", "configuracao_nao_identificada")
        p = item.data.get("np_solicitado")
        if p is not None:
            by_config[item.campaign.key, p].append(item)
    benchmark_order = {name: i for i, name in enumerate(LEVELS)}
    groups = []
    for campaign in campaigns:
        levels = LEVELS.get(campaign.benchmark, ()) if campaign.problem_class == CLASS else ()
        plan = set(plans[campaign.key])
        observed = {p for key, p in by_config if key == campaign.key}
        for p in sorted(set(levels) | {np_ for _, np_ in plan} | observed):
            group = Group(campaign, campaign.benchmark, campaign.problem_class, p, by_config[campaign.key, p], p in levels)
            populate(group, plan)
            groups.append(group)
    present = {(campaign.benchmark, campaign.problem_class) for campaign in campaigns}
    for benchmark, levels in LEVELS.items():
        if (benchmark, CLASS) not in present:
            for p in levels:
                group = Group(None, benchmark, CLASS, p, [], True)
                populate(group, set())
                groups.append(group)
    groups.sort(key=lambda group: (benchmark_order.get(group.benchmark, len(LEVELS)), group.series, group.processes))
    temperature_limits = [c.environment.values["temp_max_c"] for c in campaigns if c.environment and "temp_max_c" in c.environment.values]
    common_temp = min(temperature_limits) if temperature_limits else None
    series: dict[tuple, list[Group]] = defaultdict(list)
    for group in groups:
        series[group.series].append(group)
    summaries, sensitivity = [], []
    for (benchmark, cls, campaign), strata in series.items():
        base = next((group for group in strata if group.processes == 1 and group.reference), None)
        base_mean = base.description["media_s"] if base else None
        base_hashes = signature(base.sample) if base else None
        prev = None
        for group in strata:
            group.scaling = {
                **group.key, "n": group.description["n"], "media_s": group.description["media_s"],
                "media_ref_1p_s": base_mean,
                **scaling(group.processes, group.description["media_s"], base_mean, signature(group.sample), base_hashes),
                **transition(prev, group),
            }
            if group.reference:
                prev = group
        used = [group for group in strata if group.sample]
        best = min(used, key=lambda group: group.description["media_s"], default=None)
        highest = max(used, key=lambda group: group.processes, default=None)
        fastest_speedup = max((group for group in used if group.scaling["speedup"] is not None),
                              key=lambda group: group.scaling["speedup"], default=None)
        summaries.append({
            "campanha": campaign or None, "benchmark": benchmark, "classe": cls, "tempo_medio_1p_s": base_mean,
            "melhor_np": best.processes if best else None, "menor_media_s": best.description["media_s"] if best else None,
            "reducao_na_melhor_pct": best.scaling["reducao_tempo_vs_1p_pct"] if best else None,
            "np_maior_speedup": fastest_speedup.processes if fastest_speedup else None,
            "maior_speedup": fastest_speedup.scaling["speedup"] if fastest_speedup else None,
            "maior_np_com_tempos": highest.processes if highest else None,
            "eficiencia_maior_np_pct": highest.scaling["eficiencia_pct"] if highest else None,
        })
        for policy in ("mapeamento_ou_binding_sem_evidencia", "limite_termico_comum"):
            alt_base = sensitivity_sample(base, policy, common_temp) if base else []
            for group in strata:
                sample = sensitivity_sample(group, policy, common_temp)
                mean = describe(value(item) for item in sample)["media_s"]
                mean_base = describe(value(item) for item in alt_base)["media_s"]
                alt = scaling(group.processes, mean, mean_base, signature(sample), signature(alt_base))
                sensitivity.append({
                    **group.key, "cenario": policy, "limite_c": common_temp if policy == "limite_termico_comum" else None,
                    "n_principal": group.description["n"], "n_cenario": len(sample),
                    "media_principal_s": group.description["media_s"], "media_cenario_s": mean,
                    "speedup_principal": group.scaling["speedup"], "speedup_cenario": alt["speedup"],
                    "eficiencia_cenario_pct": alt["eficiencia_pct"], "motivo_speedup_ausente": alt["motivo_speedup_ausente"],
                })
    wall = [
        {**group.key, **describe(wall for item in group.sample if (wall := value(item, "tempo_parede_coletor_s")) is not None)}
        for group in groups
    ]
    return Analysis(groups, summaries, wall, [row for group in groups for row in outlier_rows(group)],
                    [temporal_row(group) for group in groups], sensitivity)
