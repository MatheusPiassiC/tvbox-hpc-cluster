"""Relatórios Markdown com resultados, critérios e referências aos dados brutos."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from os.path import relpath
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.parse import quote

from .figures import FIGURES
from .model import Attempt, Campaign, CONFLICT, INVALID, Issue, REPETITIONS, UNCERTAIN, VALID
from .statistics import Analysis, Group, precheck

NASA = "[Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)"
NIST = "[Intervalo t para a média, NIST/SEMATECH](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)"
POLICY = """A classificação independente exige conclusão do NPB, verificação numérica `SUCCESSFUL` no resumo, tempo interno positivo, código de saída zero, consistência do problema classe A e dos processos, associação ao plano e mapeamento completo com afinidade individual e exclusiva por núcleo. O timeout e os limites prévios são avaliados pelos valores e controles documentados em cada campanha. O número de slots representa capacidade de alocação. O número de ranks distintos e os processos totais e ativos do resumo verificam o paralelismo. Os ranks devem preencher a ordem dos oito hosts computacionais, até quatro por nó, com o NFS dedicado.

- **Válida confirmada** requer evidência suficiente nos registros e ausência de contradição material.
- **Inválida confirmada** registra falha inequívoca da execução, da verificação numérica ou de critério obrigatório.
- **Inconclusiva** registra uma lacuna que impede confirmar a execução. Ausência de mapa, afinidade ou rodapé pode ter essa consequência.
- **Conflitante** indica valores materiais incompatíveis ou identidade ambígua. O conflito tem precedência quando coexistem sinais de falha ou lacunas. O catálogo preserva todos os motivos.

Para a amostra principal, uma tentativa confirmada precisa ocupar uma posição única na grade de referência, entre os blocos 1 e 10, com tempo do NPB e condições comparáveis dentro da configuração. Campanhas distintas permanecem como séries independentes. O status original do coletor é mantido em coluna própria. Avisos identificados têm registros e referências individuais."""

PROFILES = {
    "EP": (
        "A separação das amostras do gerador em trabalho predominantemente local é compatível com a escalabilidade observada e com o ganho contínuo ao adicionar nós.",
        "Tempos de computação, inicialização e reduções em separado, além de contadores de CPU e registros de frequência sob carga.",
    ),
    "IS": (
        "A ordenação de inteiros envolve redistribuição de chaves. A mudança de domínio de memória e de comunicação pode contribuir para a elevação do tempo em múltiplos nós.",
        "Perfil das chamadas MPI por fase, volumes e tempos de troca de chaves, desempenho por enlace e medições no mesmo número de processos com arranjos diferentes.",
    ),
    "CG": (
        "Localidade de cache e memória pode contribuir para ganhos intranó. Os acessos irregulares e as reduções podem limitar ganhos quando a distribuição abrange mais nós.",
        "Contadores de cache, ciclos, banda de memória e tempos de computação esparsa e de reduções MPI, com frequência sob carga.",
    ),
    "MG": (
        "A hierarquia de malhas combina transferências de memória e mensagens de curto e longo alcance. A relação entre computação local e comunicação pode variar por nível e decomposição.",
        "Tempos por nível do multigrid, tráfego de halo, contadores de memória e origem das diferenças dentro de um bloco.",
    ),
    "FT": (
        "As transposições da FFT 3D envolvem redistribuições coletivas. Custos de comunicação, sincronização e diferenças na decomposição são compatíveis com o salto de 4 para 8 processos e com a recuperação parcial em 32.",
        "Tempos por fase da FFT, duração e volume de coletivas, contadores de rede sincronizados à execução e repetição instrumentada da configuração de 32 processos.",
    ),
    "LU": (
        "O solver Gauss–Seidel inferior–superior envolve dependências entre subdomínios. Localidade intranó pode contribuir para a eficiência em dois processos. Os ganhos distribuídos podem depender da granularidade e da troca entre fronteiras.",
        "Contadores de memória/cache, tempos por fase do solver, comunicação de fronteira e frequência por núcleo em execuções repetidas.",
    ),
    "BT": (
        "A decomposição do solver por blocos e a troca de fronteiras podem contribuir para a regressão ao passar a três nós. A retomada em mais nós é compatível com um novo equilíbrio entre redução do trabalho local e comunicação.",
        "Tamanho das partições, ociosidade por rank, temporização de fases e mensagens e, se o desenho permitir, comparações controladas de mapeamento para o mesmo np.",
    ),
    "SP": (
        "O solver pentadiagonal escalar tem troca de dados entre partições. Diferenças de decomposição e condições térmicas durante a carga são hipóteses para testar diante da dispersão nas maiores configurações.",
        "Temperatura por sensor e frequência por núcleo durante o kernel, tempos por fase e repetições em blocos com a mesma condição térmica inicial.",
    ),
}


def fmt(value: Any, decimals: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "sim" if value else "não"
    if isinstance(value, (float, Decimal)):
        return f"{value:.{decimals}f}".replace(".", ",")
    return str(value)


def table(head: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
    columns = list(head)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value).replace("|", "\\|").replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


@dataclass
class Reports:
    out: Path
    raw: Path
    inventory: list[dict]
    campaigns: list[Campaign]
    attempts: list[Attempt]
    issues: list[Issue]
    analysis: Analysis

    def raw_ref(self, ref: str | None) -> str:
        if not ref:
            return "—"
        match = re.fullmatch(r"(.+?):(\d+)(?:-(\d+))?", ref)
        path = match[1] if match else ref
        if not path.startswith(f"{self.raw.name}/"):
            return f"`{ref}`"
        original = self.raw / path.removeprefix(f"{self.raw.name}/")
        target = quote(Path(relpath(original, self.out)).as_posix(), safe="/")
        if match:
            target += f"#L{match[2]}"
            if match[3]:
                target += f"-L{match[3]}"
        return f"[{ref}]({target})"

    @property
    def groups(self) -> list[Group]:
        return self.analysis.groups

    def coverage_summary(self) -> str:
        reference = [group for group in self.groups if group.reference]
        expected = {(group.benchmark, group.processes) for group in reference}
        seen = {(group.benchmark, group.processes) for group in reference if group.attempts}
        completed = {(group.benchmark, group.processes) for group in reference
                     if group.coverage["completude"] in ("completa", "acima_da_meta")}
        states = Counter(item.state for item in self.attempts)
        accepted = sum(item.data["aceita_coleta"] is True for item in self.attempts)
        row_accepts = sum(row.values.get("status") == "VALIDA" for c in self.campaigns for row in c.csv)
        in_sample = sum(group.description["n"] for group in reference)
        return (
            f"Foram examinados **{len(self.inventory)} arquivos** em {len(self.campaigns)} campanhas. "
            f"Das **{len(expected)} configurações** de referência, {len(seen)} foram observadas e {len(completed)} têm "
            f"dez posições lógicas confirmadas em alguma campanha. A meta documentada é {len(expected) * REPETITIONS} repetições válidas. "
            f"Há {sum(len(c.plan) for c in self.campaigns)} registros nos planos, "
            f"{sum(len(c.csv) for c in self.campaigns)} registros de resultados e {sum(len(c.blocks) for c in self.campaigns)} blocos TXT. "
            f"Foram agrupadas **{len(self.attempts)} tentativas**, das quais {accepted} aceitas pelo coletor "
            f"({row_accepts} linhas CSV com `VALIDA`). A auditoria confirmou **{states[VALID]} válidas**, "
            f"**{states[INVALID]} inválidas**, **{states[UNCERTAIN]} inconclusivas** e **{states[CONFLICT]} conflitantes**. "
            f"A amostra principal contém **{in_sample} tempos**."
        )

    def issues_table(self) -> str:
        all_issues = [
            *self.issues, *(issue for c in self.campaigns for issue in c.issues),
            *(issue for item in self.attempts for issue in item.issues),
        ]
        if not all_issues:
            return "O catálogo de ocorrências está vazio para este snapshot."
        classes: dict[tuple[str, str], list[Issue]] = defaultdict(list)
        for issue in all_issues:
            classes[issue.level, issue.code].append(issue)
        rows = []
        for (level, code), records in sorted(classes.items()):
            example = records[0]
            rows.append((level, code, len(records), example.detail, " · ".join(self.raw_ref(ref) for ref in example.sources)))
        return table(("Nível", "Ocorrência", "Registros", "Primeiro exemplo", "Fontes do exemplo"), rows)

    def campaigns_table(self) -> str:
        rows = []
        for campaign in self.campaigns:
            env = campaign.environment
            items = [item for item in self.attempts if item.campaign is campaign]
            starts = [item.data["inicio_observado"] for item in items if item.data["inicio_observado"]]
            ends = [item.data["fim_observado"] for item in items if item.data["fim_observado"]]
            def observed_range(key: str) -> str:
                readings = [x for item in items if (x := precheck(item, key)) is not None]
                if not readings:
                    return "—"
                return f"{fmt(min(readings), 1)}–{fmt(max(readings), 1)}"
            rows.append((
                campaign.benchmark, campaign.experiment,
                min(starts).isoformat() if starts else None, max(ends).isoformat() if ends else None,
                observed_range("temp_max_antes_c"), env.values.get("temp_max_c") if env else None,
                observed_range("mem_disp_min_antes_mb"),
                self.raw_ref(env.ref("temp_max_c")) if env else "—",
            ))
        return table(("Benchmark", "Campanha", "Início", "Fim", "Pré-temp. (°C)", "Limite (°C)", "Pré-RAM (MB)", "Fonte do limite"), rows)

    def environment_summary(self) -> str:
        envs = [c.environment for c in self.campaigns if c.environment]
        if not envs:
            return "Os registros de ambiente estão indisponíveis neste snapshot."
        fields = ("plataforma_declarada_sha256", "secoes_2_3_sha256", "script_sha256",
                  "hostfile_declarado_sha256", "make_def_declarado_sha256", "npb_pacote",
                  "open_mpi_coordenador", "compilador_binario")
        rows = []
        for key in fields:
            occurrences = Counter(env.values.get(key) for env in envs)
            display = ", ".join(f"`{fmt(item)}` ({count})" for item, count in sorted(occurrences.items(), key=lambda pair: str(pair[0])))
            source = next((env.ref(key) for env in envs if key in env.values), None)
            rows.append((key, display, self.raw_ref(source)))
        return table(("Campo", "Valor e número de campanhas", "Exemplo de fonte"), rows)

    def coverage_table(self) -> str:
        rows = []
        for group in self.groups:
            cov = group.coverage
            rows.append((
                group.benchmark, group.campaign.experiment if group.campaign else None, group.processes,
                cov["posicoes_no_plano"], cov["tentativas_agrupadas"], cov["ordinais_validos_coletor"],
                cov["aceitas_coleta"], cov["validas_confirmadas"], cov["invalidas_confirmadas"],
                cov["inconclusivas"], cov["conflitantes"], cov["completude"].replace("_", " "),
            ))
        return table(("NPB", "Camp.", "p", "Plano", "Tent.", "Ord. válidos", "Aceitas", "Confirmadas", "Inválidas",
                      "Inconc.", "Confl.", "Cobertura"), rows)

    def coverage_exceptions(self) -> str:
        gaps = [group for group in self.groups if group.reference and group.coverage["completude"] != "completa"]
        rejects = sum(group.coverage["nps_rejeitados_no_stdout"] for group in self.groups)
        uncertain_config = sum(item.data["np_solicitado"] is None for item in self.attempts)
        note = f"Há {rejects} rejeições explícitas de quantidade MPI no stdout/stderr e {uncertain_config} tentativas sem np unívoco."
        if not gaps:
            return f"Todas as configurações da grade têm dez posições confirmadas. {note}"
        gap_table = table(("Benchmark", "p", "Campanha", "Cobertura", "Blocos sem válida"), (
            (g.benchmark, g.processes, g.campaign.key if g.campaign else None, g.coverage["completude"],
             g.coverage["blocos_sem_valida_na_referencia"]) for g in gaps
        ))
        return note + "\n\n" + gap_table

    def performance_summary(self) -> str:
        return table(("NPB", "Campanha", "Média 1 p (s)", "Melhor p", "Melhor média (s)", "Redução (%)", "Maior S",
                      "Maior p com tempos", "E no maior p (%)"), (
            (row["benchmark"], row["campanha"], row["tempo_medio_1p_s"], row["melhor_np"], row["menor_media_s"],
             fmt(row["reducao_na_melhor_pct"], 2), row["maior_speedup"], row["maior_np_com_tempos"],
             fmt(row["eficiencia_maior_np_pct"], 2)) for row in self.analysis.summaries
        ))

    def metrics_table(self) -> str:
        return table(("NPB", "Camp.", "p", "n", "Nós", "Média (s)", "IC 95% (s)", "CV (%)", "S(p)", "E(p) (%)"), (
            (g.benchmark, g.campaign.experiment if g.campaign else None, g.processes, g.description["n"],
             ", ".join(map(str, g.coverage["n_nos_observados"])) or "—", g.description["media_s"],
             interval(g.description), fmt(g.description["cv_pct"], 2), g.scaling["speedup"],
             fmt(g.scaling["eficiencia_pct"], 2)) for g in self.groups
        ))

    def high_impact_points(self) -> str:
        if not self.analysis.outliers:
            return "Não houve pontos sinalizados pelo critério exploratório de Tukey."
        top = sorted(self.analysis.outliers, key=lambda row: abs(row["variacao_media_sem_ponto_pct"]), reverse=True)[:6]
        rows = [
            (r["benchmark"], r["np"], r["bloco"], r["exec_id"], r["tempo_npb_s"], r["tempo_parede_s"], r["media_original_s"],
             r["media_sem_ponto_s"], fmt(r["variacao_media_sem_ponto_pct"], 2), fmt(r["temp_max_antes_c"], 1),
             fmt(r["mediana_temp_antes_demais_c"], 1), self.raw_ref(r["fonte_csv"]) + " · " + self.raw_ref(r["fonte_npb"]))
            for r in top
        ]
        return f"Foram sinalizadas **{len(self.analysis.outliers)} observações**, preservadas nas médias. A tabela lista as seis de maior impacto absoluto na média ao omitir uma observação por vez.\n\n" + table(
            ("NPB", "p", "Bloco", "Execução", "NPB (s)", "Parede (s)", "Média (s)", "Média sem ponto (s)", "Variação (%)",
             "Temp. prévia (°C)", "Mediana prévia das demais (°C)", "Fontes"), rows,
        )

    def thermal_sensitivity(self) -> str:
        thermal = [row for row in self.analysis.sensitivity if row["cenario"] == "limite_termico_comum"]
        limits = {r["limite_c"] for r in thermal if r["limite_c"] is not None}
        if not limits:
            return "O cenário térmico comum é indeterminado na ausência de limites documentados."
        changed = [r for r in thermal if r["n_principal"] != r["n_cenario"]]
        limit = min(limits)
        text = f"O cenário com temperatura prévia de até **{limit} °C** usa o menor limite documentado e recalcula as médias e a referência de um processo sobre os registros abaixo ou no limite."
        if not changed:
            return text + " Este cenário preserva todas as amostras principais."
        rows = [(
            r["benchmark"], r["np"], r["n_principal"], r["n_cenario"], r["media_principal_s"],
            r["media_cenario_s"], r["speedup_principal"], r["speedup_cenario"],
        ) for r in changed]
        return text + "\n\n" + table(("NPB", "p", "n principal", "n no cenário", "Média principal (s)",
                                        "Média no cenário (s)", "S principal", "S no cenário"), rows) + (
            "\n\nO recorte é posterior à coleta, desbalanceia os blocos e reduz a precisão. "
            "A associação com temperatura prévia fica confundida com posição temporal e outras condições da campanha."
        )


def interval(row: dict) -> str:
    return f"[{fmt(row['ic95_inf_s'])} a {fmt(row['ic95_sup_s'])}]" if row["ic95_inf_s"] is not None else "—"


def figures_section() -> str:
    titles = (
        "Tempo médio e intervalo t de 95%", "Speedup e referência ideal", "Eficiência paralela",
        "Distribuição dos tempos", "Completude experimental", "Variação dos tempos por bloco",
    )
    return "\n".join(f"- {title} · [PDF](../graficos/{name}.pdf) · [PNG](../graficos/{name}.png)" for title, name in zip(titles, FIGURES))


def experimental(r: Reports) -> str:
    internal_wall = [
        item.data["tempo_parede_coletor_s"] - item.data["tempo_npb_s"]
        for item in r.attempts if item.data["tempo_parede_coletor_s"] is not None and item.data["tempo_npb_s"] is not None
    ]
    offset = [abs(item.data["duracao_relogio_s"] - item.data["tempo_parede_coletor_s"]) for item in r.attempts
              if item.data["duracao_relogio_s"] is not None and item.data["tempo_parede_coletor_s"] is not None]
    paired = [(item.csv.values["tempo_s"], item.data["tempo_npb_s"]) for item in r.attempts
              if item.csv and "tempo_s" in item.csv.values and item.data["tempo_npb_s"] is not None]
    verified_maps = sum(item.data["estado_mapa"] == "confirmado" for item in r.attempts)
    verified_bindings = sum(item.data["estado_binding"] == "confirmado" for item in r.attempts)
    map_copies = Counter(item.data["mapas_mpi"] for item in r.attempts if item.data.get("mapas_mpi") is not None)
    plan_hashes = Counter(c.sources["plano"].sha for c in r.campaigns if "plano" in c.sources)
    plan_hash_table = table(("SHA-256 do plano", "Campanhas com bytes iguais"), ((f"`{k}`", n) for k, n in sorted(plan_hashes.items())))
    identity = "O vínculo usa `exec_id` no mesmo conjunto, conferido pela referência `saida_arquivo` e linha de abertura. O identificador de auditoria inclui a campanha. Na ausência de um ID, um ponteiro inequívoco permite associação ou é registrada a chave derivada da linha. Blocos e registros ambíguos ficam preservados em tabelas próprias. Cada posição lógica do plano usa campanha, bloco e np. O total de tentativas agrupadas inclui candidatos cuja identidade física ainda precise de revisão."
    timing = (
        f"Nas {len(internal_wall)} tentativas com ambas as métricas, a diferença parede − NPB vai de {fmt(min(internal_wall))} "
        f"a {fmt(max(internal_wall))} s. " if internal_wall else ""
    )
    if offset:
        timing += f"A maior diferença absoluta entre parede e fim − início foi {fmt(max(offset), 2)} s, a confrontar com a resolução de um segundo dos horários. "
    if paired:
        timing += f"Em {sum(left == right for left, right in paired)} dos {len(paired)} pares CSV–TXT, os tempos internos têm valores idênticos. "
    timing += ("O valor principal é o campo `Time in seconds` emitido pelo NPB, inclusive quando o CSV apresenta precisão diferente compatível com arredondamento. "
               "No confronto entre números copiados, representações de igual precisão devem ter o mesmo valor. Em precisões distintas, as faixas implícitas de arredondamento precisam se sobrepor no interior. "
               "O relatório de ambiente define tempo do NPB como resposta. O tempo de parede inclui a inicialização MPI e tem tabela própria.")
    return f"""# 02 — Auditoria experimental

{r.coverage_summary()}

## Validação e rastreabilidade

{identity}

{POLICY}

Código 124 documenta timeout. Código 137 documenta encerramento por SIGKILL, com timeout confirmado quando há duração externa pelo menos igual ao limite da campanha. Outros códigos diferentes de zero evidenciam falha de execução. O diagnóstico de causa usa mensagens específicas e sua linha de origem. A declaração `VALIDA` em um envelope não decide a classificação.

## Cobertura por configuração

{r.coverage_exceptions()}

{r.coverage_table()}

Os planos documentam uma medida por configuração e bloco, sem reposição. A auditoria identifica a ordem pelo sufixo de `exec_id`, confrontando posições do TXT, linhas do CSV, horários e plano. A mesma semente pode gerar as mesmas permutações entre campanhas. Os hashes abaixo indicam repetição de arquivo de plano, enquanto cada conjunto de resultado tem suas próprias tentativas.

{plan_hash_table}

## Mapeamento e tempos

Verificações de mapa completo e afinidade confirmada por tentativa totalizam {verified_maps} e {verified_bindings}, respectivamente. As frequências de número de representações do mapa por bloco são {dict(sorted(map_copies.items()))}. O arquivo [ranks_mpi.csv](../tabelas/ranks_mpi.csv) traz host, socket, núcleo e linhas de evidência por rank e tentativa.

{timing}

## Ambiente documentado

{r.environment_summary()}

{r.campaigns_table()}

O hash calculado do trecho 2/3 permite comparar o texto observado. O hash declarado do coletor tem procedimento próprio. Os snapshots e a sondagem anterior delimitam a evidência ambiental. Hashes distintos entre executáveis de benchmarks diferentes são esperados. A auditoria compara as opções de compilação comuns com o `make.def` documentado e preserva o `RAND` específico de cada carga. Tamanho e iterações são verificados pelos parâmetros de classe A. Os resumos NPB reportam a versão completa 3.4.4. [Tamanhos de problema, NASA](https://nas.nasa.gov/software/npb_problem_sizes.html)

O nome comercial das TV Boxes é H7. O device tree usado na inicialização registra o modelo `SEI Robotics SEI610`. [Informações manuais de SP](../../../raw/SP/npb_9_SP_A_ambiente.txt#L114-L127)

## Ocorrências com fontes

{r.issues_table()}

As referências usam linhas físicas contadas a partir de 1. A tabela [inconsistencias.csv](../tabelas/inconsistencias.csv) traz todos os casos, inclusive os exemplos acima e as listas de fontes. [Base consolidada](../tabelas/execucoes_consolidadas.csv) · [Classificação por tentativa](../tabelas/auditoria_execucoes.csv) · [Cobertura completa](../tabelas/cobertura_experimental.csv)
"""


def stats_report(r: Reports) -> str:
    desc = table(("NPB", "Camp.", "p", "n", "Média (s)", "Mediana (s)", "DP (s)", "Variância (s²)", "Mín.–máx. (s)",
                  "Q1–Q3 (s)", "IQR (s)", "CV (%)", "IC 95% (s)"), (
        (g.benchmark, g.campaign.experiment if g.campaign else None, g.processes, d["n"], d["media_s"], d["mediana_s"],
         d["dp_amostral_s"], fmt(d["variancia_amostral_s2"], 6),
         f"{fmt(d['min_s'])}–{fmt(d['max_s'])}" if d["n"] else None,
         f"{fmt(d['q1_s'])}–{fmt(d['q3_s'])}" if d["n"] else None,
         d["iqr_s"], fmt(d["cv_pct"], 2), interval(d))
        for g in r.groups for d in (g.description,)
    ))
    high = [g for g in r.groups if (g.description["cv_pct"] or 0) >= 5]
    skew = [g for g in r.groups if abs(g.description["assimetria_ajustada"] or 0) >= 1]
    high_labels = ", ".join(f"{g.benchmark}/{g.processes} p" for g in high) or "nenhuma configuração"
    temp_rows = [row for row in r.analysis.temporal if row["n_com_ordem"]]
    notable = [row for row in temp_rows if abs(row["rho_spearman_ordem"] or 0) >= .55
               or abs(row["metade_final_vs_inicial_pct"] or 0) >= 3 or abs(row["primeiro_vs_seguintes_pct"] or 0) >= 3]
    temporal = table(("NPB", "p", "n", "Primeiro vs. seguintes (%)", "Última vs. primeira metade (%)", "ρ ordinal", "r lag 1"), (
        (row["benchmark"], row["np"], row["n_com_ordem"], fmt(row["primeiro_vs_seguintes_pct"], 2),
         fmt(row["metade_final_vs_inicial_pct"], 2), row["rho_spearman_ordem"], row["r_lag1"]) for row in notable
    )) if notable else "Nenhuma configuração com ordem atingiu os limiares descritivos desta seção."
    slower = sum((row["primeiro_vs_seguintes_pct"] or 0) > 0 for row in temp_rows)
    faster = sum((row["primeiro_vs_seguintes_pct"] or 0) < 0 for row in temp_rows)
    map_change = sum(rw["n_cenario"] != rw["n_principal"] for rw in r.analysis.sensitivity
                     if rw["cenario"] == "mapeamento_ou_binding_sem_evidencia")
    superlinear = table(("NPB", "p", "S(p)", "E(p) (%)", "S(p) − p"), (
        (g.benchmark, g.processes, fmt(g.scaling["speedup"], 5), fmt(g.scaling["eficiencia_pct"], 3),
         fmt(g.scaling["desvio_speedup_do_ideal"], 5)) for g in r.groups if g.scaling["superlinear"]
    ))
    return f"""# 03 — Análise estatística

{r.coverage_summary()}

A série usa a média aritmética de `Time in seconds` das tentativas confirmadas. Os quartis usam interpolação linear, tipo 7 do NumPy. O desvio-padrão e a variância amostrais usam divisor `n−1`. O coeficiente de variação é `100 × s/média`. O IC de 95% bilateral para a média é `média ± t(0,975; n−1) × s/√n` com n observado, definido a partir de duas medidas. Uma medida isolada sustenta média e mediana descritivas. Um grupo vazio tem métricas ausentes. Amostras da ordem de dez têm pouca resolução para caracterizar a forma da distribuição. A interpretação nominal do IC supõe observações independentes e uma aproximação distributiva adequada. [NIST/SEMATECH](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)

Os intervalos da tabela referem-se ao tempo médio. O speedup usa `S(p) = média(1)/média(p)` e a eficiência é `100 × S(p)/p` em porcentagem. A referência precisa ser comparável em plataforma, binário, tamanho, iterações, versão, compilação e parâmetros MPI na mesma campanha. O cálculo deixa o speedup vazio se essa evidência está ausente. O ideal é `p`, e `desvio_speedup_do_ideal` registra `S(p) − p`. A análise apresenta estimativas pontuais das razões. Os ICs dos tempos e suas sobreposições servem à inspeção descritiva.

## Estatísticas por configuração

{desc}

A tabela [estatisticas_tempo_parede.csv](../tabelas/estatisticas_tempo_parede.csv) conserva a duração externa em uma série própria, sobre o mesmo filtro de elegibilidade e com n de durações efetivamente registradas.

## Escalabilidade

{r.performance_summary()}

O desempenho com eficiência observada acima de 100% aparece na tabela seguinte. Localidade de cache e memória, conduta da frequência e dispersão podem influir em razões de médias. Valores muito próximos de 100% também são sensíveis à resolução de 0,01 s emitida pelo resumo.

{superlinear}

## Dispersão e observações atípicas

As cercas de Tukey usam `Q1 − 1,5 × IQR` e `Q3 + 1,5 × IQR` quando há pelo menos quatro observações e IQR positivo. O teste exploratório usa desigualdade estrita com tolerância numérica de 10⁻¹⁰ s na fronteira. Os tempos confirmados continuam elegíveis independentemente desse sinalizador. CV de pelo menos 5% aparece em {high_labels}. A assimetria de Fisher–Pearson ajustada tem magnitude ≥ 1 em {len(skew)} configurações. Pontos muito próximos do centro em segundos podem ser detectados em séries de pequena dispersão ou resolução limitada. Consulte [estatisticas_descritivas.csv](../tabelas/estatisticas_descritivas.csv) e [observacoes_atipicas.csv](../tabelas/observacoes_atipicas.csv).

{r.high_impact_points()}

## Ordem das execuções

A ordem verificada permite comparar a primeira repetição com as posteriores e metades com o mesmo tamanho, com descarte da medida central apenas nesse contraste descritivo para n ímpar. Usa-se ρ de Spearman entre bloco e tempo e r de Pearson entre tempos adjacentes quando há sequência consecutiva, n ≥ 4 e variação. A tabela mostra casos com |ρ| ≥ 0,55 ou diferença de pelo menos 3% na primeira medida ou entre metades. De {len(temp_rows)} configurações com ordem, {slower} começam acima da média seguinte e {faster} abaixo. Há dependência temporal plausível. A ordem é entrelaçada com outros níveis em cada bloco e as condições mudam ao longo das campanhas. O protocolo documenta ausência de aquecimento específico e de reposição de tentativas. Consulte [comportamento_temporal.csv](../tabelas/comportamento_temporal.csv).

{temporal}

## Sensibilidade

Conservar as tentativas cujo único impedimento seria evidência incompleta de mapa ou afinidade, com conclusão numérica e posição unívocas, altera o n de {map_change} configurações. As perdas por conflito ou falha permanecem fora desse cenário. [Tabela de sensibilidade](../tabelas/sensibilidade.csv)

{r.thermal_sensitivity()}

## Figuras exploratórias

Os painéis mantêm a escala de tempo por benchmark. Speedup e eficiência mostram p no eixo horizontal em log₂. A figura temporal usa diferença percentual da mediana do próprio grupo para comparar flutuações relativas. Os ganhos percentuais nas transições referem-se à mudança de médias entre níveis adjacentes.

{figures_section()}
"""


def benchmark_details(r: Reports) -> str:
    parts = []
    for summary in r.analysis.summaries:
        benchmark = summary["benchmark"]
        campaign = summary["campanha"]
        groups = [group for group in r.groups if group.benchmark == benchmark and (group.campaign.key if group.campaign else None) == campaign]
        headline = f"## {benchmark}" + (f" · {campaign}" if sum(row["benchmark"] == benchmark for row in r.analysis.summaries) > 1 else "")
        if summary["melhor_np"] is None:
            parts.append(headline + "\n\nOs dados disponíveis não sustentam uma média elegível nesta série.")
            continue
        highest = summary["maior_np_com_tempos"]
        best = summary["melhor_np"]
        base = summary["tempo_medio_1p_s"]
        best_g = next(group for group in groups if group.processes == best)
        largest_cv = max((g for g in groups if g.description["cv_pct"] is not None),
                         key=lambda g: g.description["cv_pct"], default=None)
        if base is not None and summary["maior_speedup"] is not None:
            lead = (f"A menor média foi **{fmt(summary['menor_media_s'])} s em {best} processos**, redução de "
                    f"**{fmt(summary['reducao_na_melhor_pct'], 2)}%** frente a {fmt(base)} s em um processo. "
                    f"O maior speedup foi **{fmt(summary['maior_speedup'])}×** em {summary['np_maior_speedup']} processos. "
                    f"A eficiência foi {fmt(best_g.scaling['eficiencia_pct'], 2)}% no ponto de menor média e "
                    f"{fmt(summary['eficiencia_maior_np_pct'], 2)}% no maior np ({highest}).")
        else:
            lead = f"A menor média foi **{fmt(summary['menor_media_s'])} s em {best} processos**. A razão convencional carece de uma referência comparável."
        if largest_cv:
            lead += f" A maior dispersão relativa foi CV de {fmt(largest_cv.description['cv_pct'], 2)}% em {largest_cv.processes} processos."
        changes = table(("p", "Nós", "Média (s)", "CV (%)", "S", "E (%)", "Ganho vs. anterior (%)", "Transição"), (
            (g.processes, g.scaling["nos_atuais"], g.description["media_s"], fmt(g.description["cv_pct"], 2),
             g.scaling["speedup"], fmt(g.scaling["eficiencia_pct"], 2), fmt(g.scaling["ganho_tempo_vs_anterior_pct"], 2),
             " · ".join(value for value in (g.scaling["escopo_transicao"], g.scaling["transicao"]) if value) or None)
            for g in groups
        ))
        negative = [
            f"{g.scaling['np_anterior']}→{g.processes} p ({fmt(-g.scaling['ganho_tempo_vs_anterior_pct'], 2)}% de aumento no tempo)"
            for g in groups if g.scaling["transicao"] == "piora"
        ]
        monotone = ("As médias aumentam nas transições " + ", ".join(negative) + "." if negative
                    else "As médias comparáveis diminuem nas transições observadas, com ganhos relativos de magnitude variada.")
        flagged = [row for row in r.analysis.outliers if row["campanha"] == campaign]
        if flagged:
            standout = max(flagged, key=lambda row: abs(row["variacao_media_sem_ponto_pct"]))
            monotone += (f" O ponto mais influente entre os sinalizados, `{standout['exec_id']}`, tem "
                         f"{fmt(standout['tempo_npb_s'])} s em {standout['np']} processos. Mantido na análise, "
                         f"ele produz uma diferença de {fmt(standout['variacao_media_sem_ponto_pct'], 2)}% na média "
                         f"se omitido apenas na sensibilidade individual. {r.raw_ref(standout['fonte_npb'])}")
        hypothesis, further = PROFILES.get(benchmark, ("O mecanismo precisa ser investigado nesta carga.", "Medidas de fase e uma coleta controlada."))
        parts.append(f"""{headline}

### Observações

{lead}

{changes}

{monotone}

### Hipótese para investigação

{hypothesis} {NASA}

### Evidência adicional necessária

{further}
""")
    return "\n\n".join(parts)


def specific_cases(r: Reports) -> str:
    """Acrescenta relações verificáveis dos casos prioritários desta coleta."""
    cases = []
    for id_, label in (("5-0028", "FT com 32 processos"), ("9-0041", "SP com 16 processos"), ("9-0046", "SP com 25 processos")):
        row = next((point for point in r.analysis.outliers if point["exec_id"] == id_), None)
        if row is None:
            continue
        internal = f"A inicialização registrada pelo próprio FT foi {fmt(row['tempo_inicializacao_npb_s'], 4)} s. " if row["tempo_inicializacao_npb_s"] is not None else ""
        cases.append(
            f"- **{label}.** `{id_}` no bloco {row['bloco']} registrou {fmt(row['tempo_npb_s'], 2)} s no NPB e "
            f"{fmt(row['tempo_parede_s'], 2)} s de parede. {internal}"
            f"A temperatura prévia máxima foi {fmt(row['temp_max_antes_c'], 1)} °C, ante mediana de "
            f"{fmt(row['mediana_temp_antes_demais_c'], 1)} °C nas demais repetições do grupo. "
            f"{r.raw_ref(row['fonte_csv'])} · {r.raw_ref(row['fonte_npb'])}"
        )
    return "\n".join(cases) if cases else "O conjunto atual não contém os casos prioritários encontrados na inspeção inicial."


def diagnostics(r: Reports) -> str:
    return f"""# 04 — Diagnóstico dos benchmarks

{r.performance_summary()}

A comparação usa tempo relativo ao baseline de cada carga. As transições mostram os nós efetivamente mapeados. Mudanças em p e número de nós também mudam a decomposição do trabalho. A atribuição causal exige medir fases, comunicação e condições dos nós durante a execução.

{benchmark_details(r)}

## Casos prioritários com rastreabilidade

{specific_cases(r)}

FT em 32 processos apresenta uma observação lenta no meio da campanha. SP tem pontos mais lentos nos blocos finais e uma condição prévia mais permissiva. Esses padrões orientam investigação, com as leituras prévias e a posição dos blocos como evidência descritiva. As temperaturas durante esses kernels são desconhecidas.

[Speedup por configuração](../tabelas/speedup_eficiencia.csv) · [Dispersão e IC](../tabelas/estatisticas_descritivas.csv) · [Posição temporal](../tabelas/comportamento_temporal.csv)
"""


def synthesis(r: Reports) -> str:
    c = Counter((h.get("link_mbit_s"), h.get("duplex")) for campaign in r.campaigns if campaign.environment for h in campaign.environment.hosts)
    readings = [h for campaign in r.campaigns if campaign.environment for h in campaign.environment.hosts if h.get("papel") == "computação MPI"]
    frequencies = sorted({v for host in readings for v in host.get("freq_instante_mhz_por_cpu", {}).values()})
    pre_ram = [value_ for item in r.attempts if (value_ := precheck(item, "mem_disp_min_antes_mb")) is not None]
    pre_temp = [value_ for item in r.attempts if (value_ := precheck(item, "temp_max_antes_c")) is not None]
    temperatures = f"{fmt(min(pre_temp), 1)}–{fmt(max(pre_temp), 1)} °C" if pre_temp else "indisponível"
    memory = f"{fmt(min(pre_ram), 0)}–{fmt(max(pre_ram), 0)} MB" if pre_ram else "indisponível"
    preconditions = f"A RAM disponível mínima antes dos lançamentos varia entre {memory}. A temperatura máxima prévia varia entre {temperatures}."
    superlinear = ", ".join(f"{g.benchmark} em {g.processes} p ({fmt(g.scaling['eficiencia_pct'], 3)}%)"
                            for g in r.groups if g.scaling["superlinear"])
    return f"""# 05 — Síntese experimental

A auditoria abrange a campanha de novembro de 2026 com o NAS Parallel Benchmarks 3.4.4 MPI, classe A. O cluster tem oito nós H7 de cálculo, com quatro núcleos Cortex-A55 cada, e um servidor NFS dedicado. O problema de cada benchmark permanece fixo ao variar o número de processos. BT e SP usam 1, 4, 9, 16 e 25 processos. EP, IS, CG, MG, FT e LU usam 1, 2, 4, 8, 16 e 32. [Parâmetros de classe A, NASA](https://nas.nasa.gov/software/npb_problem_sizes.html)

## Dados e decisão de validade

Cada campanha tem CSV de resultados, CSV de plano, TXT com mapa/saída e registro de ambiente. O plano tem dez blocos com cada np uma vez por bloco. A ordem foi permutada com semente 20261114, com repetição de arquivo de plano para os mesmos conjuntos de níveis. O coletor v5.4 documenta ausência de aquecimento deliberado e ausência de reposição. `exec_id` identifica a tentativa dentro da campanha. `tentativa` conta lançamentos por np. `repeticao_valida` é o ordinal aceito pelo coletor. `(campanha, bloco, np)` identifica a posição planejada. As tabelas retêm nomes de arquivo, linhas físicas e intervalos correspondentes.

{POLICY}

{r.coverage_summary()}

{r.coverage_exceptions()}

A duração usada nas estatísticas é `Time in seconds` do resumo do NPB. `tempo_parede_s` tem série própria e inclui o lançamento MPI. Médias, DP com `ddof=1`, quartis tipo 7 e IC de 95% t bilateral usam o n observado. Uma medida isolada não gera IC. O speedup usa a razão de médias com um processo na mesma campanha e `E% = 100 × S(p)/p`. Os intervalos da tabela são de tempo médio. As amostras têm pouca resolução para inferir distribuição e as campanhas com medidas ordenadas podem ter dependência temporal. {NIST}

## Melhor configuração e estimativas por nível

{r.performance_summary()}

{r.metrics_table()}

EP preserva boa escalabilidade até 32 processos, com speedup de cerca de 30. IS e FT têm as menores médias com quatro processos em um nó e regressão na transição para oito processos em dois nós. IS permanece mais lento que a referência de um processo em todos os níveis distribuídos. FT recupera parte do desempenho com 32 processos, com dispersão elevada. CG tem mínimo com oito processos e regressão com 16 e 32. MG e LU atingem seus menores tempos com 32 processos, com eficiência inferior à de EP. BT regride de quatro para nove processos e melhora até 25. SP melhora ao longo da grade, com ganho menor entre 16 e 25 processos. As razões usam a referência de um processo de cada benchmark. {NASA}

As médias incluem valores de eficiência acima de 100% neste snapshot. Os casos são {superlinear or "indisponíveis na entrada atual"}. O ponto de EP muito próximo de 100% é sensível à resolução do cronômetro exibido. Em CG e LU, localidade e comportamento de memória são hipóteses que exigem contadores e perfil por fase.

## Ambiente, anomalias e limites de interpretação

Os snapshots documentam Armbian bullseye em AArch64 nos nós de cálculo, kernel 6.1.11-meson64, Open MPI 4.1.0, GCC/GFortran 10.2.1 e NPB 3.4.4. H7 é o nome comercial, e `SEI Robotics SEI610` é o modelo registrado no device tree. A plataforma SM1 consta do registro do coordenador. As contagens por velocidade de enlace e modo duplex são {dict(sorted(c.items(), key=lambda pair: str(pair[0])))} nos registros por equipamento e coleta. A identificação do switch consta das informações manuais. [Ambiente SP, seções 2.1–3.3](../../../raw/SP/npb_9_SP_A_ambiente.txt#L46-L916)

A capacidade é de quatro slots por host e 32 na alocação. O número de nós observado segue `ceil(p/4)` nas tentativas confirmadas. O layout é recuperado por rank, host e núcleo a partir das representações de job e das linhas individuais de binding. A trilha por rank está em [ranks_mpi.csv](../tabelas/ranks_mpi.csv).

O teto CPUFreq documentado é 1.500 MHz com `ondemand`. O máximo informado pelo driver é 2.100 MHz. As frequências pontuais nos snapshots dos nós de cálculo incluem {", ".join(map(str, frequencies)) or "nenhuma leitura"} MHz. {preconditions} Os campos contemporâneos ao kernel ficam vazios com monitoramento desativado. As sondagens são agregados dos nós antes da execução, incluindo nós que podem estar ociosos para aquele np. A rede tem ping e contadores acumulados de abertura, sem vazão de cada tentativa no conjunto disponível. [Snapshot inicial de SP](../../../raw/SP/npb_9_SP_A_ambiente.txt#L950-L1165)

{r.campaigns_table()}

O protocolo tem um limite térmico prévio de 85 °C em SP e 80 °C nas outras campanhas desta auditoria. A validação usa o limite documentado de cada série.

{r.thermal_sensitivity()}

A detecção por intervalo interquartil preserva todos os tempos válidos na amostra principal. Os casos de FT e SP abaixo ilustram a ocorrência de observações atípicas em diferentes posições das séries.

{specific_cases(r)}

As assinaturas de ambiente e os trechos estáveis documentados são compatíveis entre campanhas no snapshot inspecionado. Isso sustenta comparação de configuração dentro de cada série, sob as condições arquivadas. A amostragem disponível deixa indeterminados o pico de memória, a frequência efetiva, a temperatura durante o NPB, a saturação de enlace e o comportamento de cada rank sob carga. Também ficam indeterminados efeitos causais de aquecimento, contenção e diferenças da vazão, mecanismos de superlinearidade, desempenho de outros problemas e viabilidade econômica. Custo, energia e resfriamento requerem dados próprios.

Custos de redistribuição e sincronização são hipóteses para as regressões de IS e FT. Localidade, comunicação e mudanças de decomposição podem contribuir para o comportamento de CG, LU, BT e SP. Na campanha, a transição entre nós também altera o número de processos. Isolar o efeito de rede exige observar alocações distintas com o mesmo número de processos e medir fases, comunicação e condições dos nós sob carga.

## Limites de reprodução experimental

Os registros identificam o coletor v5.4, os binários e as configurações por seus hashes declarados. A reprodução da coleta depende da obtenção do código do coletor, da imagem usada e dos arquivos integrais de compilação. A explicação causal das anomalias requer medições por fase e observações de temperatura, frequência, memória e comunicação durante a execução.

## Artefatos da auditoria

- [Exploração e dicionário dos dados](01_exploracao_dos_arquivos.md) · [Auditoria experimental](02_auditoria_experimental.md)
- [Análise estatística e sensibilidade](03_analise_estatistica.md) · [Diagnóstico por benchmark](04_diagnostico_dos_benchmarks.md)
- [Execuções consolidadas](../tabelas/execucoes_consolidadas.csv) · [Cobertura](../tabelas/cobertura_experimental.csv) · [Ocorrências com fontes](../tabelas/inconsistencias.csv)
- [Estatísticas](../tabelas/estatisticas_descritivas.csv) · [Speedup e eficiência](../tabelas/speedup_eficiencia.csv) · [Cenários de sensibilidade](../tabelas/sensibilidade.csv)
- [Ambientes](../tabelas/ambientes.csv) · [Snapshots por nó](../tabelas/nos_ambiente.csv) · [Observações atípicas](../tabelas/observacoes_atipicas.csv)
- [Hashes da entrada](../manifestos/dados_entrada.json) · [Versão do código e dependências](../manifestos/reproducibilidade.json) · [Guia da auditoria](../../../README.md)

{figures_section()}
"""


def write_reports(
    stage: Path, destination: Path, raw: Path, inventory: list[dict],
    campaigns: list[Campaign], attempts: list[Attempt], issues: list[Issue], analysis: Analysis,
) -> None:
    """Escreve os cinco relatórios e usa caminhos relativos às fontes originais."""
    stage.mkdir(parents=True, exist_ok=True)
    reports = Reports(destination, raw, inventory, campaigns, attempts, issues, analysis)
    inv = table(("Arquivo", "Tipo", "Bytes", "Linhas", "Codificação", "SHA-256"), (
        (reports.raw_ref(row["arquivo"]), row["tipo"], row["bytes"], row["linhas"], row["codificacao"], f"`{row['sha256']}`")
        for row in inventory
    ))
    template = Path(__file__).with_name("exploracao.md").read_text(encoding="utf-8")
    artifacts = {
        "01_exploracao_dos_arquivos.md": template.replace("<!-- INVENTARIO -->", inv),
        "02_auditoria_experimental.md": experimental(reports),
        "03_analise_estatistica.md": stats_report(reports),
        "04_diagnostico_dos_benchmarks.md": diagnostics(reports),
        "05_sintese_experimental.md": synthesis(reports),
    }
    raw_prefix = quote(Path(relpath(raw, destination)).as_posix(), safe="/")
    readme = quote(Path(relpath(Path(__file__).resolve().parents[2] / "README.md", destination)).as_posix(), safe="/")
    for name, content in artifacts.items():
        content = content.replace("(../../../raw/", f"({raw_prefix}/").replace("(../../../README.md)", f"({readme})")
        (stage / name).write_text(content.rstrip() + "\n", encoding="utf-8")
