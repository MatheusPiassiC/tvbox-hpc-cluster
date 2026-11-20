"""Critérios independentes de validade, cruzamento de fontes e classificação."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from math import ceil
from pathlib import Path
import re
import shlex
from typing import Any

from .model import (
    Attempt, CLASS, CORES_PER_HOST, CONTRADICTION, CsvRecord, FAILURE, HOSTS, LEVELS, MISSING,
    NPB_VERSION, WARNING, WORKLOADS, equal_observed, exec_sequence, first_known, rounded_agreement, seconds_between,
)
from .mpi import read_mpi

KNOWN_STATUSES = {"VALIDA", "TIMEOUT", "FALHA_EXECUCAO", "FALHA_VERIFICACAO", "INVALIDA"}
FAIL_VERIFICATION = {"UNSUCCESSFUL", "FAILED", "NOT PERFORMED", "NOT VERIFIED"}
MAP_GAPS = {"mapa_ranks_incompleto", "binding_individual_ausente"}
DIAGNOSTICS = {
    "np_nao_aceito": r"number of (?:active )?(?:processes|processors).*(?:perfect square|power of two|not supported|invalid)|"
                    r"invalid number of (?:processes|processors)|must (?:be|use) a (?:perfect square|power of two)|"
                    r"must use (?:a|at least|only).*(?:processes|processors)",
    "erro_memoria": r"out of memory|cannot allocate memory|std::bad_alloc|oom.kill",
    "erro_filesystem": r"no such file or directory|stale file handle|read-only file system|input/output error",
    "erro_comunicacao": r"connection (?:reset by peer|refused|timed out)|broken pipe|MPI_ERR_(?:COMM|TRUNCATE)",
    "falha_inicializacao_mpi": r"error (?:in|occurred in) MPI_Init|not enough slots available|"
                              r"was unable to (?:launch|start)|failed to start (?:local|remote) daemon",
    "mpi_abort": r"^\s*(?:MPI_ABORT was invoked|\*\*\* MPI_ERR_|mpirun has exited due to)",
    "interrupcao_sinal": r"exited on signal|terminated by signal|killed by signal",
}
FATAL_PATTERNS = {key: re.compile(value, re.I) for key, value in DIAGNOSTICS.items()}


def compare(attempt: Attempt, field: str, sources: list[tuple[Any, str]], *, rounding: bool = False,
            level: str = CONTRADICTION) -> None:
    known = [(value, ref) for value, ref in sources if value is not None]
    for idx, (left, _) in enumerate(known):
        for right, _ in known[idx + 1:]:
            if left == right:
                continue
            if rounding and rounded_agreement(left, right):
                continue
            formatted = ", ".join(str(value) for value, _ in known)
            attempt.add(level, f"divergencia_{field}", f"{field}: {formatted}.", *(ref for _, ref in known))
            return
    if rounding and len({value for value, _ in known}) > 1:
        attempt.add(WARNING, f"arredondamento_{field}", f"{field} compatível com precisões diferentes.",
                    *(ref for _, ref in known))


def command_parts(command: str | None) -> tuple[list[str] | None, int | None, tuple[str, ...] | None]:
    """Separa np, opções e executável sem executar o comando registrado."""
    if not command:
        return None, None, None
    try:
        parts = shlex.split(command)
        index = parts.index("-np")
        count = parts[index + 1]
        if len(parts) < 4 or index + 1 >= len(parts) - 1 or Path(parts[0]).name not in {"mpirun", "mpiexec"}:
            return None, None, None
        return parts, int(count) if count.isascii() and count.isdecimal() else None, tuple(parts[1:index] + parts[index + 2:-1])
    except (ValueError, IndexError):
        return None, None, None


def relate_plan(attempt: Attempt, positions: dict[tuple[int, int], list[CsvRecord]]) -> None:
    data = attempt.data
    b, p = data["bloco_observado"], data["np_solicitado"]
    rows = positions.get((b, p), [])
    attempt.plan_rows = rows
    data["ordem_planejada"] = rows[0].values["ordem_no_bloco"] if len(rows) == 1 else None
    if rows:
        data["id_repeticao_logica"] = f"{attempt.campaign.key}/bloco-{b:02d}/np-{p}"
        for row in rows:
            for issue in row.issues:
                if issue not in attempt.issues:
                    attempt.issues.append(issue)
    elif b is not None and p is not None and positions:
        attempt.add(CONTRADICTION, "fora_do_plano_arquivado", f"Par (bloco={b}, np={p}) ausente no plano da campanha.",
                    *attempt.refs, attempt.campaign.sources["plano"].name)
    else:
        attempt.add(MISSING, "posicao_plano_nao_verificada", "Sem associação a uma posição no plano arquivado.")


def validate_logs(attempt: Attempt) -> None:
    log = attempt.log
    if log is None:
        return
    source, summary, extra = log.source, log.summary, log.additional
    if log.footer_line is None:
        attempt.add(MISSING, "saida_sem_rodape", "Captura sem rodapé do coletor. Possível truncamento.", log.ref)
    if not summary:
        attempt.add(MISSING, "saida_sem_resumo_npb", "Ausência do resumo de conclusão do NPB.", log.ref)
    for line_no, line in log.output:
        if re.search(r"\bwarning\b|\baviso\b", line, re.I):
            attempt.add(WARNING, "aviso_stdout_stderr", line.strip(), source.ref(line_no))
            continue
        for key, pattern in FATAL_PATTERNS.items():
            if pattern.search(line):
                attempt.add(FAILURE, key, line.strip(), source.ref(line_no))
                break
    verdict = summary.get("verificacao")
    earlier_ok = extra.get("linha_verificacao_intermediaria_sucesso")
    earlier_failed = extra.get("linha_verificacao_intermediaria_falha")
    if (earlier_ok and verdict in FAIL_VERIFICATION) or (earlier_failed and (verdict == "SUCCESSFUL" or earlier_ok)):
        line = log.summary_lines.get("verificacao")
        attempt.add(CONTRADICTION, "verificacao_interna_divergente", "Diagnóstico intermediário e resumo incompatíveis.",
                    source.ref(earlier_failed or earlier_ok), source.ref(line or earlier_ok))
    if verdict in FAIL_VERIFICATION or earlier_failed:
        attempt.add(FAILURE, "verificacao_npb_malsucedida", f"Verificação NPB registrada: {verdict!r}.",
                    source.ref(log.summary_lines.get("verificacao") or earlier_failed))
    elif verdict != "SUCCESSFUL":
        attempt.add(MISSING, "verificacao_npb_nao_confirmada", f"Resumo sem verificação de sucesso reconhecível: {verdict!r}.", log.ref)


def validate_mapping(attempt: Attempt, hostfile: list[tuple[str, int]] | None) -> None:
    log, data = attempt.log, attempt.data
    processes = data["np_solicitado"]
    data["nos_minimos_esperados"] = ceil(processes / CORES_PER_HOST) if processes is not None else None
    data.update(estado_mapa="inconclusivo", estado_binding="inconclusivo")
    if log is None:
        return
    mpi = read_mpi(log)
    attempt.issues.extend(mpi.issues)
    hosts = mpi.hosts
    counts = mpi.distribution
    observed_ranks = set(hosts)
    expected_ranks = set(range(processes)) if processes is not None else None
    complete = expected_ranks is not None and observed_ranks == expected_ranks and len(mpi.rows) == len(expected_ranks)
    declared_hosts = hostfile or [(host, CORES_PER_HOST) for host in HOSTS]
    expected_hosts = [name for name, slots in declared_hosts for _ in range(min(slots, CORES_PER_HOST))]
    known_hosts = set(HOSTS)
    wrong_hosts = sorted({host for row in mpi.rows for host in row["hosts_observados"] if host not in known_hosts})
    incorrect = False
    if wrong_hosts:
        code = "participacao_nfs" if any(h.lower().split(".")[0] == "nfs" for h in wrong_hosts) else "host_fora_do_cluster"
        attempt.add(FAILURE, code, f"Hosts inesperados {wrong_hosts}.", log.ref)
        incorrect = True
    if counts and max(counts.values()) > CORES_PER_HOST:
        attempt.add(FAILURE, "mais_de_quatro_ranks_no_host", f"Ranks por host: {counts}.", log.ref)
        incorrect = True
    if expected_ranks is not None:
        unexpected = sorted({row["rank"] for row in mpi.rows} - expected_ranks)
        if unexpected:
            attempt.add(FAILURE, "ranks_fora_da_faixa", f"Ranks fora de 0..{processes - 1}: {unexpected}.", log.ref)
            incorrect = True
        unslotted = sorted(rank for rank, host in hosts.items() if rank >= len(expected_hosts) or host != expected_hosts[rank])
        if unslotted:
            attempt.add(FAILURE, "distribuicao_fora_de_slot", f"Ranks fora da sequência de slots: {unslotted}.", log.ref)
            incorrect = True
    if complete and len(counts) != data["nos_minimos_esperados"]:
        attempt.add(FAILURE, "numero_de_nos_incompativel", f"{len(counts)} hosts para {processes} processos.", log.ref)
        incorrect = True
    if not complete:
        attempt.add(MISSING, "mapa_ranks_incompleto", f"Mapeados {len(hosts)} ranks unívocos, {processes} solicitados.", log.ref)
    cores = Counter((row["host"], row["socket"], row["core"]) for row in mpi.rows if row["host"] and row["core"] is not None)
    overlapping = [list(core) for core, n in sorted(cores.items()) if n > 1]
    unbound = [row["rank"] for row in mpi.rows if row["sem_binding_explicito"]]
    has_binding = sum(cores.values())
    if overlapping or unbound:
        attempt.add(FAILURE, "afinidade_incompativel", f"Núcleos compartilhados {overlapping}; ranks sem binding {unbound}.", log.ref)
    if processes is not None and has_binding < processes:
        attempt.add(MISSING, "binding_individual_ausente", f"{has_binding} de {processes} ranks com host e núcleo unívocos.", log.ref)
    if len(mpi.slots) > 1:
        attempt.add(WARNING, "slots_mpi_divergentes", f"Capacidades registradas {sorted(mpi.slots)}.", log.ref)
    codes = {item.code for item in mpi.issues if item.level == CONTRADICTION}
    state = "incompativel" if incorrect else "conflitante" if codes else "confirmado" if complete else "inconclusivo"
    affinity = ("incompativel" if overlapping or unbound else "conflitante" if "binding_rank_divergente" in codes
                else "confirmado" if complete and has_binding == processes else "inconclusivo")
    data.update(
        estado_mapa=state, estado_binding=affinity, ranks_distintos=len(mpi.rows) if mpi.rows else None,
        ranks_com_host=len(hosts) if mpi.rows else None, n_nos_observados=len(counts) if complete else None,
        distribuicao_ranks_observados=counts or None, ranks_com_binding=has_binding if mpi.rows else None,
        mapas_mpi=mpi.map_count, mapas_mpi_fechados=mpi.map_closed, mapas_mpi_layouts_distintos=mpi.map_layouts,
        jobs_mpi=sorted(mpi.jobs), cabecalhos_job_mpi=mpi.job_lines, slots_total_allocated=sorted(mpi.slots),
        ranks_mpi=mpi.rows, hostfile_evidencia="ambiente" if hostfile else "referencia_experimental",
    )
    record = attempt.csv
    if record and complete:
        compare(attempt, "n_nos", [(record.values.get("n_nos"), record.ref), (len(counts), log.ref)])
        compare(attempt, "distribuicao", [(record.values.get("distribuicao"), record.ref), (counts, log.ref)])


def validate_runtime(attempt: Attempt, csv: dict, footer: dict, env: dict) -> None:
    data = attempt.data
    record, log = attempt.csv, attempt.log
    exit_code = first_known(footer.get("exit_code"), csv.get("exit_code")) if equal_observed(footer.get("exit_code"), csv.get("exit_code")) else None
    start, end = data["inicio_observado"], data["fim_observado"]
    wall, elapsed = csv.get("tempo_parede_s"), seconds_between(start, end)
    limit = env.get("timeout_s")
    ref = log.source.ref(log.footer_line) if log and log.footer_line else record.ref if record else None
    refs = (ref,) if ref else ()
    timed_out = None
    data.update(exit_code_observado=exit_code, tempo_parede_coletor_s=wall, duracao_relogio_s=elapsed, timeout_limite_s=limit)
    if exit_code == 124 or (exit_code == 137 and limit is not None and wall is not None and wall >= limit):
        timed_out = True
        attempt.add(FAILURE, "timeout_confirmado", f"Código de saída {exit_code} e duração externa {wall}.", *refs)
    elif exit_code == 137:
        attempt.add(FAILURE, "encerramento_sigkill", f"Código 137. Duração externa {wall}.", *refs)
        timed_out = False if limit is not None and wall is not None and wall < limit else None
    elif exit_code is not None:
        timed_out = False
        if exit_code != 0:
            attempt.add(FAILURE, "exit_code_nao_zero", f"mpirun terminou com código {exit_code}.", *refs)
    if exit_code is None:
        attempt.add(MISSING, "exit_code_nao_confirmado", "Código de saída unívoco ausente.")
    if elapsed is not None and elapsed < 0:
        attempt.add(CONTRADICTION, "horarios_invertidos", f"Fim antecede o início em {-elapsed} s.")
    if wall is not None and wall <= 0:
        attempt.add(CONTRADICTION, "tempo_parede_nao_positivo", f"Duração externa {wall} s.", record.ref)
    internal = data["tempo_npb_s"]
    if wall is not None and internal is not None and wall < internal and not rounded_agreement(wall, internal):
        attempt.add(CONTRADICTION, "tempo_parede_menor_npb", f"Parede {wall} s, NPB {internal} s.")
    if wall is not None and elapsed is not None and abs(elapsed - wall) > Decimal("1.005"):
        attempt.add(WARNING, "relogio_e_parede_divergem", f"Relógio {elapsed} s, parede {wall} s.")
    if exit_code == 0 and limit is not None:
        if wall is not None and wall >= limit:
            attempt.add(CONTRADICTION, "sucesso_fora_limite_timeout", f"Parede {wall} s, limite {limit} s.")
            timed_out = None
        elif wall is None and (elapsed is None or elapsed + 1 >= limit):
            attempt.add(MISSING, "prazo_timeout_nao_verificado", "Duração insuficiente para verificar o limite.")
            timed_out = None
    if data["status_coleta"] == "TIMEOUT" and timed_out is not True:
        attempt.add(WARNING, "timeout_coletor_sem_evidencia", "Classificação do coletor sem corroborar pelo código e duração.", *refs)
    data["timeout_confirmado"] = timed_out


def validate_workload(attempt: Attempt, summary: dict, ref: str) -> None:
    if not summary:
        return
    mandatory = ("classe", "tamanho", "iteracoes", "versao", "processos_total", "processos_ativos", "tempo_s")
    lacking = [field for field in mandatory if summary.get(field) is None]
    if lacking:
        attempt.add(MISSING, "resumo_npb_incompleto", f"Campos obrigatórios ausentes {lacking}.", ref)
    p = attempt.data["np_solicitado"]
    if p is not None and any(summary.get(key) not in (None, p) for key in ("processos_total", "processos_ativos")):
        attempt.add(FAILURE, "processos_npb_incompativeis", f"Solicitados {p}, total {summary.get('processos_total')}, ativos {summary.get('processos_ativos')}.", ref)
    if summary.get("versao") not in (None, NPB_VERSION):
        attempt.add(FAILURE, "versao_npb_fora_do_protocolo", f"Versão no resumo: {summary['versao']}.", ref)
    benchmark, cls = attempt.campaign.benchmark, attempt.campaign.problem_class
    expected = WORKLOADS.get(benchmark) if cls == CLASS else None
    if expected and any(summary.get(key) not in (None, value) for key, value in zip(("tamanho", "iteracoes"), expected)):
        attempt.add(FAILURE, "carga_fora_da_classe_a", f"Tamanho, iterações observados: {summary.get('tamanho')}, {summary.get('iteracoes')}. Esperados {expected}.", ref)
    if summary.get("tempo_s") is not None and summary["tempo_s"] <= 0:
        attempt.add(FAILURE, "tempo_npb_nao_positivo", f"Tempo NPB {summary['tempo_s']} s.", ref)


def validate_attempt(attempt: Attempt, positions: dict[tuple[int, int], list[CsvRecord]]) -> None:
    """Valida identidade, evidências da execução, plano, ambiente e medições."""
    campaign = attempt.campaign
    record, log, data = attempt.csv, attempt.log, attempt.data
    environment = campaign.environment
    env = environment.values if environment else {}
    csv = record.values if record else {}
    header, footer, summary = (log.header, log.footer, log.summary) if log else ({}, {}, {})
    extra = log.additional if log else {}
    cref, lref = record.ref if record else "", log.ref if log else ""
    sref = log.source.ref(log.summary_lines.get("benchmark"), log.summary_lines.get("verificacao")) if summary else lref
    for key, expected in (("benchmark", campaign.benchmark), ("classe", campaign.problem_class), ("experimento_id", campaign.experiment)):
        nodes = [(expected, campaign.key), (csv.get(key), cref), (header.get(key), lref),
                 (summary.get(key), sref), (env.get(key), environment.ref(key) if environment else "")]
        if key == "benchmark":
            nodes.append((extra.get("benchmark_banner"), log.source.ref(extra.get("linha_banner")) if log else ""))
        compare(attempt, key, nodes)
    command_csv, np_csv_cmd, options_csv = command_parts(csv.get("comando"))
    command_txt, np_txt_cmd, mpi_options = command_parts(log.command if log else None)
    command = first_known(command_txt, command_csv)
    compare(attempt, "comando", [(command_csv, cref), (command_txt, log.source.ref(log.command_line) if log else "")])
    if not command or (csv.get("comando") and command_csv is None) or (log and log.command and command_txt is None):
        attempt.add(WARNING, "comando_incompleto", "Comando ausente ou sintaxe MPI não reconhecida.")
    if command:
        binary = Path(command[-1]).name
        expected = f"{campaign.benchmark.lower()}.{campaign.problem_class}.x"
        if binary != expected:
            attempt.add(CONTRADICTION, "binario_comando_divergente", f"Executável {binary!r}, esperado {expected!r}.")
        model, _, options = command_parts(env.get("comando_modelo"))
        if model and command_txt and (mpi_options != options or command_txt[-1] != model[-1]):
            attempt.add(CONTRADICTION, "comando_difere_modelo", "Opções ou caminho diferem do modelo do ambiente.",
                        log.source.ref(log.command_line), environment.ref("comando_modelo"))
    requests = [csv.get("np"), header.get("np"), np_csv_cmd, np_txt_cmd]
    compare(attempt, "np_solicitado", list(zip(requests, (cref, lref, cref, lref))))
    requested = first_known(*requests) if equal_observed(*requests) else None
    if requested is None:
        attempt.add(MISSING, "np_nao_determinado", "Quantidade solicitada ausente ou ambígua.")
    resolved = {}
    for key in ("bloco", "tentativa", "fase", "inicio", "fim"):
        value = first_known(header.get(key), footer.get(key))
        compare(attempt, key, [(csv.get(key), cref), (value, lref)])
        resolved[key] = first_known(value, csv.get(key)) if equal_observed(value, csv.get(key)) else None
    for key in ("exit_code", "status", "motivo"):
        compare(attempt, key, [(csv.get(key), cref), (footer.get(key), log.source.ref(log.footer_line) if log else "")],
                level=CONTRADICTION if key == "exit_code" else WARNING)
    status = first_known(csv.get("status"), footer.get("status")) if equal_observed(csv.get("status"), footer.get("status")) else None
    for value, ref in ((csv.get("status"), cref), (footer.get("status"), lref)):
        if value is not None and value not in KNOWN_STATUSES:
            attempt.add(WARNING, "status_coletor_desconhecido", f"Status {value!r}.", ref)
    for key in ("tempo_s", "mops_total", "mops_por_processo", "processos_ativos", "verificacao"):
        collected = csv.get(key)
        if key == "verificacao" and collected is not None:
            collected = None if collected.upper() == "NAO_ENCONTRADA" else collected.upper()
        compare(attempt, key, [(collected, cref), (summary.get(key), log.source.ref(log.summary_lines.get(key)) if log else "")],
                rounding=key in {"tempo_s", "mops_total", "mops_por_processo"})
    for key in ("binario_sha256", "ambiente_sha256"):
        env_key = "plataforma_declarada_sha256" if key == "ambiente_sha256" else key
        compare(attempt, key, [(csv.get(key), cref), (env.get(env_key), environment.ref(env_key) if environment else "")])
    tex_pre = log.precheck if log else {}
    for key, setting in tex_pre.items():
        compare(attempt, key, [(csv.get(key), cref), (setting, log.source.ref(log.precheck_line))],
                rounding=key != "governor_antes", level=WARNING if key == "mem_disp_min_antes_mb" else CONTRADICTION)
    for key, threshold in (("cpu_ocupada_max_antes_pct", "cpu_max_pct"), ("temp_max_antes_c", "temp_max_c")):
        value = first_known(tex_pre.get(key), csv.get(key))
        if value is not None and env.get(threshold) is not None and value > env[threshold]:
            attempt.add(FAILURE, "limite_precondicao_excedido", f"{key}={value}, limite {env[threshold]}.",
                        *attempt.refs, environment.ref(threshold))
    policy = first_known(tex_pre.get("governor_antes"), csv.get("governor_antes"))
    freq_limit = first_known(tex_pre.get("freq_max_permitida_antes_mhz"), csv.get("freq_max_permitida_antes_mhz"))
    if environment:
        for key, observed in (("governor", policy), ("scaling_max_freq_mhz", freq_limit)):
            mpi_hosts = [host for host in environment.hosts if host.get("papel") == "computação MPI" and host.get(key) is not None]
            if observed is not None and any(host[key] != observed for host in mpi_hosts):
                refs = tuple(environment.source.ref(h["linha_plataforma"]) for h in mpi_hosts if h[key] != observed)
                attempt.add(CONTRADICTION, "politica_cpufreq_divergente", f"{key} antes da tentativa diverge do snapshot.",
                            *(attempt.refs + refs))
    compile_options = extra.get("opcoes_compilacao_npb", {})
    make_def = env.get("make_def_opcoes", {})
    for option in sorted(compile_options.keys() & make_def.keys() - {"RAND"}):
        observed = "" if compile_options[option] == "(none)" else compile_options[option]
        compare(attempt, "opcao_compilacao", [(observed, log.source.ref(extra.get("linha_compilacao_npb"))),
                                              (make_def[option], environment.ref("make_def_opcoes"))])
    early = extra.get("processos_cabecalho")
    compare(attempt, "processos_npb", [(early, log.source.ref(extra.get("linha_processos_cabecalho")) if log else ""),
                                       (summary.get("processos_total"), sref), (summary.get("processos_ativos"), sref)])
    data.update(
        benchmark_auditado=campaign.benchmark, classe_auditada=campaign.problem_class,
        np_solicitado=requested, np_npb_total=summary.get("processos_total"), np_npb_ativos=summary.get("processos_ativos"),
        ordem_execucao=exec_sequence(attempt.key, campaign.experiment) if attempt.identity_method == "exec_id" else None,
        inicio_observado=resolved["inicio"], fim_observado=resolved["fim"], bloco_observado=resolved["bloco"],
        tentativa_observada=resolved["tentativa"], fase_observada=resolved["fase"],
        status_coleta=status, status_txt=footer.get("status"), motivo_txt=footer.get("motivo"), exit_code_txt=footer.get("exit_code"),
        aceita_coleta=status == "VALIDA" if status in KNOWN_STATUSES else None,
        tempo_npb_s=summary.get("tempo_s"), verificacao_npb=summary.get("verificacao"),
        tamanho_npb=summary.get("tamanho"), iteracoes_npb=summary.get("iteracoes"), versao_npb=summary.get("versao"),
        compilacao_npb=summary.get("data_compilacao"), operacao_npb=summary.get("operacao"),
        mops_total_npb=summary.get("mops_total"), mops_por_processo_npb=summary.get("mops_por_processo"),
        binario_identificado_sha256=first_known(csv.get("binario_sha256"), env.get("binario_sha256")),
        plataforma_identificada_sha256=first_known(csv.get("ambiente_sha256"), env.get("plataforma_declarada_sha256"), env.get("secoes_2_3_sha256")),
        opcoes_mpi_observadas=first_known(mpi_options, options_csv), id_repeticao_logica=None,
        compilacao_opcoes_normalizadas=tuple(sorted(compile_options.items())) or None,
        governor_previo_observado=policy, limite_cpufreq_previo_observado_mhz=freq_limit,
        saida_sha256_normalizado=log.output_sha if log else None, inicio_txt=header.get("inicio"), fim_txt=footer.get("fim"),
        np_txt_envelope=header.get("np"), benchmark_txt_resumo=summary.get("benchmark"), classe_txt_resumo=summary.get("classe"),
        linha_resumo_npb=log.summary_lines.get("benchmark") if log else None,
        linha_verificacao_npb=log.summary_lines.get("verificacao") if log else None,
        linha_tempo_npb=log.summary_lines.get("tempo_s") if log else None, **extra,
    )
    if data["fase_observada"] not in (None, "MEDICAO"):
        attempt.add(FAILURE, "fase_fora_das_medicoes", f"Fase {data['fase_observada']!r}.")
    if requested is not None and (campaign.benchmark not in LEVELS or requested not in LEVELS[campaign.benchmark] or campaign.problem_class != CLASS):
        attempt.add(WARNING, "configuracao_fora_da_referencia", "Configuração fora do plano documentado de classe A.")
    campaign_conflicts = [issue for issue in campaign.issues if issue.level == CONTRADICTION and issue.code != "chave_plano_duplicada"]
    attempt.issues.extend(campaign_conflicts)
    relate_plan(attempt, positions)
    validate_runtime(attempt, csv, footer, env)
    validate_logs(attempt)
    validate_workload(attempt, summary, sref)
    validate_mapping(attempt, env.get("hostfile_slots"))
