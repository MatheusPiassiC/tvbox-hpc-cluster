"""Cruza campanhas, posições do plano e registros das tentativas."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from .environment import read_environment
from .model import (
    Attempt, Campaign, CONTRADICTION, CsvRecord, Issue, LEVELS, MISSING, REPETITIONS, WARNING,
    VALID, exec_sequence,
)
from .parsing import read_csv, read_output


def load_campaign(campaign: Campaign) -> None:
    """Lê os arquivos disponíveis e valida as referências no nível da campanha."""
    sources = campaign.sources
    for role in ("resultados", "plano", "saidas", "ambiente"):
        if role not in sources:
            campaign.issues.append(Issue(MISSING, "arquivo_esperado_ausente", f"Arquivo de {role} ausente.",
                                         tuple(source.name for source in sources.values())))
    if source := sources.get("resultados"):
        campaign.csv = read_csv(source, "resultados", campaign.issues)
    if source := sources.get("plano"):
        campaign.plan = read_csv(source, "plano", campaign.issues)
        for record in campaign.plan:
            campaign.issues.extend(record.issues)
    if source := sources.get("saidas"):
        campaign.output_header, campaign.blocks = read_output(source, campaign.issues)
    if source := sources.get("ambiente"):
        campaign.environment = read_environment(source)
        campaign.issues.extend(campaign.environment.issues)
    env = campaign.environment
    ident = {"experimento_id": campaign.experiment, "benchmark": campaign.benchmark, "classe": campaign.problem_class}
    for key, value in ident.items():
        for fields, source, line in (
            (campaign.output_header, sources.get("saidas"), campaign.output_header.get("linha")),
            (env.values if env else {}, env.source if env else None, env.lines.get(key) if env else None),
        ):
            if key in fields and fields[key] != value:
                campaign.issues.append(Issue(CONTRADICTION, "identidade_campanha", f"{key}: arquivo {value!r}, registro {fields[key]!r}.",
                                             (source.ref(line),)))
    for key in ("ambiente", "resultados"):
        expected = campaign.output_header.get(key)
        if expected and key in sources and sources[key].path.name != expected:
            campaign.issues.append(Issue(WARNING, "arquivo_referido_preambulo", f"TXT refere {expected!r}.",
                                         (sources["saidas"].ref(campaign.output_header.get("linha_arquivos")), sources[key].name)))
    if env and "plano" in sources:
        plan = sources["plano"]
        expect = env.values.get("plano_declarado_sha256")
        if expect and expect != plan.sha:
            campaign.issues.append(Issue(CONTRADICTION, "hash_plano_divergente", f"Declarado {expect}; calculado {plan.sha}.",
                                         (env.ref("plano_declarado_sha256"), plan.name)))
        name = env.values.get("plano_arquivo")
        if name and name != plan.path.name:
            campaign.issues.append(Issue(CONTRADICTION, "nome_plano_divergente", f"Plano declarado {name!r}, observado {plan.path.name!r}.",
                                         (env.ref("plano_arquivo"), plan.name)))
        observed = sorted({row.values["np"] for row in campaign.plan if "np" in row.values})
        documented = env.values.get("processos_documentados")
        if documented and sorted(documented) != observed:
            campaign.issues.append(Issue(CONTRADICTION, "niveis_plano_divergentes", f"Ambiente {documented}, plano {observed}.",
                                         (env.ref("processos_documentados"), plan.name)))


def plan_positions(campaign: Campaign) -> dict[tuple[int, int], list[CsvRecord]]:
    """Indexa posições lógicas e aponta problemas na estrutura dos blocos."""
    positions: dict[tuple[int, int], list[CsvRecord]] = defaultdict(list)
    per_order: dict[tuple[int, int], list[CsvRecord]] = defaultdict(list)
    for row in campaign.plan:
        block, processes, order = (row.values.get(key) for key in ("bloco", "np", "ordem_no_bloco"))
        if None in (block, processes, order):
            campaign.issues.append(Issue(MISSING, "posicao_plano_incompleta", "A posição não tem bloco, ordem e np legíveis.", (row.ref,)))
            continue
        positions[block, processes].append(row)
        per_order[block, order].append(row)
    for rows in [*positions.values(), *per_order.values()]:
        if len(rows) > 1:
            refs = tuple(row.ref for row in rows)
            issue = Issue(CONTRADICTION, "chave_plano_duplicada", "Mais de um registro por posição ou ordem do bloco.", refs)
            if issue not in campaign.issues:
                campaign.issues.append(issue)
            for row in rows:
                row.issues.append(issue)
    if plan := campaign.sources.get("plano"):
        for block in sorted({key[0] for key in per_order}):
            observed = sorted(order for b, order in per_order if b == block)
            if observed != list(range(1, len(observed) + 1)):
                campaign.issues.append(Issue(WARNING, "ordens_plano_descontinuas", f"Bloco {block}, ordens {observed}.", (plan.name,)))
        levels = LEVELS.get(campaign.benchmark, ()) if campaign.problem_class == "A" else ()
        expected = {(block, p) for block in range(1, REPETITIONS + 1) for p in levels}
        if expected and (absent := sorted(expected - positions.keys())):
            campaign.issues.append(Issue(MISSING, "posicoes_planejadas_ausentes",
                                         f"Posições (bloco, np) ausentes segundo a referência: {absent}.", (plan.name,)))
        if expected and (extra := sorted(positions.keys() - expected)):
            refs = tuple(positions[key][0].ref for key in extra)
            campaign.issues.append(Issue(WARNING, "posicoes_fora_da_referencia", f"Posições adicionais: {extra}.", refs))
    return positions


def pointer(row: CsvRecord) -> tuple[str, int] | None:
    name = row.values.get("saida_arquivo")
    line = row.values.get("saida_linha_inicial")
    if name and line and Path(name).name == name:
        return name, line
    return None


def associate(campaign: Campaign) -> list[Attempt]:
    """Reconcilia pelo ID e pela linha exata, preservando os candidatos sem par."""
    blocks_at = {(block.source.path.name, block.first): block for block in campaign.blocks}
    claims: dict[tuple[str, int], list[CsvRecord]] = defaultdict(list)
    for row in campaign.csv:
        if loc := pointer(row):
            claims[loc].append(row)
    groups: dict[tuple[str, str], Attempt] = {}

    def group(identity: tuple[str, str]) -> Attempt:
        method, value = identity
        key = value if method == "exec_id" else f"{method}:{value}"
        return groups.setdefault(identity, Attempt(campaign, key, method, [], []))

    allocated = {}
    for loc, block in blocks_at.items():
        explicit = {row.values["exec_id"] for row in claims.get(loc, []) if row.values.get("exec_id")}
        declared_id = block.exec_id or block.footer.get("exec_id")
        if not declared_id and len(explicit) == 1:
            declared_id = next(iter(explicit))
        identity = ("exec_id", declared_id) if declared_id else ("derivado_txt", str(block.first))
        group(identity).blocks.append(block)
        allocated[loc] = identity
    for row in campaign.csv:
        loc = pointer(row)
        by_pointer = allocated.get(loc)
        exec_id = row.values.get("exec_id")
        identity = ("exec_id", exec_id) if exec_id else by_pointer or ("derivado_csv", str(row.first))
        attempt = group(identity)
        attempt.csvs.append(row)
        if by_pointer and by_pointer != identity:
            detail = f"ID {exec_id!r} aponta para um bloco de outra identidade."
            attempt.add(CONTRADICTION, "ponteiro_txt_outro_id", detail, row.ref, blocks_at[loc].ref)
            group(by_pointer).add(CONTRADICTION, "bloco_txt_referenciado_por_outro_id", detail, row.ref, blocks_at[loc].ref)
        elif loc and not by_pointer:
            attempt.add(WARNING, "ponteiro_txt_nao_localizado", f"Referência CSV {loc!r} sem bloco nessa posição.", row.ref)
        elif not loc and (row.values.get("saida_arquivo") or row.values.get("saida_linha_inicial")):
            attempt.add(WARNING, "ponteiro_txt_incompleto", "Nome ou linha de saída fora do formato documentado.", row.ref)
    attempts = list(groups.values())
    for attempt in attempts:
        if len(attempt.csvs) > 1:
            identical = attempt.csv is not None
            proven = identical and attempt.log is not None
            attempt.add(WARNING if proven else CONTRADICTION, "id_csv_repetido",
                        "Registros CSV idênticos para o mesmo ID." if identical else "Registros CSV divergentes para o mesmo ID.")
        if len(attempt.blocks) > 1:
            attempt.add(CONTRADICTION, "id_txt_repetido", "Mais de um bloco TXT com o mesmo identificador de tentativa.")
        if not attempt.csvs:
            attempt.add(WARNING, "sem_registro_csv", "Bloco TXT sem registro CSV associado.")
        if not attempt.blocks:
            attempt.add(MISSING, "sem_bloco_txt", "Registro CSV sem bloco TXT associado.")
        for row in attempt.csvs:
            attempt.issues.extend(row.issues)
        for block in attempt.blocks:
            attempt.issues.extend(block.issues)
    return sorted(attempts, key=order_key)


def order_key(attempt: Attempt) -> tuple[int, int, str]:
    seq = exec_sequence(attempt.key, attempt.campaign.experiment)
    if seq is not None:
        return 0, seq, attempt.key
    if attempt.blocks:
        return 1, attempt.blocks[0].first, attempt.key
    return 2, attempt.csvs[0].first, attempt.key


def mark_duplicate_values(
    attempts: list[Attempt], key: Callable[[Attempt], Any], code: str, detail: str,
) -> None:
    groups: dict[Any, list[Attempt]] = defaultdict(list)
    for attempt in attempts:
        value = key(attempt)
        if value is not None:
            groups[value].append(attempt)
    for value, aliases in groups.items():
        if len(aliases) > 1:
            refs = tuple(ref for attempt in aliases for ref in attempt.refs)
            for attempt in aliases:
                attempt.add(CONTRADICTION, code, f"{detail} Chave {value!r}.", *refs)


def verify_campaign_sequence(attempts: list[Attempt]) -> None:
    """Verifica a ordenação original e a correspondência sequencial com o plano."""
    def strictly_increasing(values: list) -> bool:
        return all(x < y for x, y in zip(values, values[1:]))

    sequence = [item.data["ordem_execucao"] for item in attempts]
    csv_order = [item.csv.first for item in attempts if item.csv]
    txt_order = [item.log.first for item in attempts if item.log]
    starts = [item.data["inicio_observado"] for item in attempts if item.data["inicio_observado"] is not None]
    ready = bool(attempts) and None not in sequence and all(
        strictly_increasing(values) for values in (sequence, csv_order, txt_order, starts)
    )
    overlap = False
    for left, right in zip(attempts, attempts[1:]):
        end, start = left.data["fim_observado"], right.data["inicio_observado"]
        if end is not None and start is not None and end > start:
            overlap = True
            right.add(WARNING, "horarios_sobrepostos", "O início antecede o fim da tentativa anterior na sequência.",
                      *left.refs, *right.refs)
    for item in attempts:
        item.data["ordem_confiavel"] = ready and not overlap
    if attempts and not ready:
        campaign = attempts[0].campaign
        campaign.issues.append(Issue(WARNING, "ordem_temporal_inconclusiva", "Sequência de IDs, linhas ou horários ausente ou não crescente.",
                                     tuple(source.name for source in campaign.sources.values() if source.role in ("saidas", "resultados"))))
    planned = [
        (item, (item.data["bloco_observado"], item.data["ordem_planejada"]))
        for item in attempts if item.data["ordem_planejada"] is not None
    ]
    if ready:
        for (left, first), (right, second) in zip(planned, planned[1:]):
            if first > second:
                right.add(WARNING, "ordem_real_difere_plano", "Sequência observada inverte posições no plano.",
                          *left.refs, *right.refs)


def reconcile_repetitions(campaign: Campaign, attempts: list[Attempt]) -> None:
    """Sinaliza colisões lógicas sem imputar repetição válida a um bloco vazio."""
    for column, code, label in (
        ("tentativa_observada", "contador_tentativa_duplicado", "Contador de tentativa reutilizado."),
        ("repeticao_valida", "repeticao_valida_duplicada", "O coletor reutilizou um ordinal de repetição válida."),
    ):
        def numbered(item: Attempt) -> tuple[int, int] | None:
            number = item.data.get(column) if column == "tentativa_observada" else item.csv.values.get(column) if item.csv else None
            processes = item.data.get("np_solicitado")
            return (processes, number) if processes is not None and number is not None else None

        mark_duplicate_values(attempts, numbered, code, label)
    mark_duplicate_values(attempts, lambda a: a.log.output_sha if a.log else None,
                          "corpo_txt_reutilizado", "Conteúdo de stdout+stderr igual em IDs distintos.")
    measurement_attempts = [item for item in attempts if item.data.get("id_repeticao_logica")]
    counts = Counter(item.data["id_repeticao_logica"] for item in measurement_attempts)
    no_replacement = bool(campaign.environment and campaign.environment.values.get("sem_reposicao_documentada"))
    for item in measurement_attempts:
        count = counts[item.data["id_repeticao_logica"]]
        item.data["tentativas_no_slot_logico"] = count
        if count > 1 and no_replacement:
            item.add(CONTRADICTION, "reposicao_contraria_protocolo", f"{count} tentativas para uma posição sem reposição prevista.")
        if item.data.get("aceita_coleta") is True and item.csv and "repeticao_valida" not in item.csv.values:
            item.add(WARNING, "aceita_sem_ordinal", "O coletor marcou VALIDA com ordinal vazio.", item.csv.ref)
        if item.data.get("aceita_coleta") is False and item.csv and "repeticao_valida" in item.csv.values:
            item.add(WARNING, "ordinal_em_tentativa_recusada", "Tentativa recusada contém ordinal válido.", item.csv.ref)
    mark_duplicate_values([item for item in measurement_attempts if item.state == VALID],
                          lambda a: a.data["id_repeticao_logica"], "duas_validas_no_mesmo_bloco",
                          "Mais de uma tentativa confirmável na mesma posição lógica.")

    for p in sorted({item.data["np_solicitado"] for item in attempts if item.data["np_solicitado"] is not None}):
        items = [item for item in attempts if item.data["np_solicitado"] == p]
        ordinals = [item.data["tentativa_observada"] for item in items]
        accepted = [item.csv.values.get("repeticao_valida") for item in items if item.csv and item.data.get("aceita_coleta")]
        if ((all(x is not None for x in ordinals) and ordinals != list(range(1, len(ordinals) + 1)))
                or (all(x is not None for x in accepted) and accepted != list(range(1, len(accepted) + 1)))):
            refs = tuple(ref for item in items for ref in item.refs)
            campaign.issues.append(Issue(WARNING, "ordinais_descontinuos",
                                         f"np={p}: tentativas {ordinals}, ordinais aceitos {accepted}.", refs))
