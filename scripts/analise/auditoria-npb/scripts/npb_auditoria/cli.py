"""Orquestra a auditoria completa e publica tabelas, manifestos, figuras e relatórios."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import logging
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from .environment import compare_environments
from .figures import make_all
from .model import Attempt, Campaign, Issue, VALID, WARNING
from .output import code_manifest, hash_file, json_text, publish, write_csv, write_json
from .parsing import CSV_FIELDS, PLAN_FIELDS, discover
from .reconcile import associate, load_campaign, plan_positions, reconcile_repetitions, verify_campaign_sequence
from .reports import write_reports
from .statistics import Analysis, DESCRIPTIVE_FIELDS, build_analysis
from .validation import validate_attempt

LOG = logging.getLogger("auditoria_npb")
PROJECT = Path(__file__).resolve().parents[2]
ISSUE_FIELDS = ("campanha", "id_auditoria", "nivel", "codigo", "detalhe", "fontes")
GROUP_FIELDS = ("campanha", "benchmark", "classe", "np")


def attempt_audit(item: Attempt) -> dict:
    return {
        "id_auditoria": item.id, "campanha": item.campaign.key,
        "benchmark_auditado": item.campaign.benchmark, "classe_auditada": item.campaign.problem_class,
        "np_solicitado": item.data["np_solicitado"], "id_repeticao_logica": item.data["id_repeticao_logica"],
        "estado_coleta": item.data["status_coleta"], "aceita_coleta": item.data["aceita_coleta"],
        "estado_auditoria": item.state, "estado_mapa": item.data["estado_mapa"], "estado_binding": item.data["estado_binding"],
        "verificacao_npb": item.data["verificacao_npb"], "timeout_confirmado": item.data["timeout_confirmado"],
        "inclusao_estatistica_principal": item.data["inclusao_estatistica_principal"],
        "motivo_inclusao_estatistica": item.data["motivo_inclusao_estatistica"],
        "n_registros_csv": len(item.csvs), "n_blocos_txt": len(item.blocks),
        "codigos_ocorrencias": sorted({issue.code for issue in item.issues}),
        "fontes": list(item.refs),
    }


def consolidated(item: Attempt) -> dict:
    csv, log = item.csv, item.log
    env = item.campaign.environment
    return {
        **attempt_audit(item), "metodo_identidade": item.identity_method,
        **{key: csv.raw.get(key) if csv else None for key in CSV_FIELDS},
        **{key: data for key, data in item.data.items() if key != "ranks_mpi"},
        "arquivo_csv": csv.source.name if csv else None,
        "linha_csv_inicio": csv.first if csv else None, "linha_csv_fim": csv.last if csv else None,
        "campos_csv_vazios": [key for key in CSV_FIELDS if not csv.raw.get(key)] if csv else None,
        "todos_registros_csv": [row.ref for row in item.csvs],
        "arquivo_txt": log.source.name if log else None,
        "linha_txt_inicio": log.first if log else None, "linha_txt_fim": log.last if log else None,
        "linha_txt_rodape": log.footer_line if log else None,
        "linha_txt_precondicoes": log.precheck_line if log else None, "comando_txt": log.command if log else None,
        "precondicoes_txt": log.precheck if log else None, "todos_blocos_txt": [block.ref for block in item.blocks],
        "posicoes_plano": [row.ref for row in item.plan_rows],
        "arquivo_ambiente": env.source.name if env else None, "inicio_snapshot_ambiente": env.values.get("gerado_em") if env else None,
    }


def write_tables(
    target: Path, attempts: list[Attempt], campaigns: list[Campaign], analysis: Analysis,
    issues: list[Issue], inventory: list[dict],
) -> None:
    files = {
        "inventario_arquivos": (inventory, ("arquivo", "tipo", "bytes", "linhas", "sha256")),
        "execucoes_consolidadas": ((consolidated(item) for item in attempts), ("id_auditoria", "campanha", "estado_auditoria")),
        "auditoria_execucoes": ((attempt_audit(item) for item in attempts), ("id_auditoria", "campanha", "estado_auditoria")),
        "cobertura_experimental": ((group.coverage for group in analysis.groups), GROUP_FIELDS),
        "estatisticas_descritivas": ((group.stat_row() for group in analysis.groups), GROUP_FIELDS),
        "estatisticas_tempo_parede": (analysis.wall, GROUP_FIELDS + DESCRIPTIVE_FIELDS),
        "speedup_eficiencia": ((group.scaling for group in analysis.groups), GROUP_FIELDS),
        "resumo_benchmarks": (analysis.summaries, GROUP_FIELDS[:-1]),
        "observacoes_atipicas": (analysis.outliers, GROUP_FIELDS + ("id_auditoria", "tempo_npb_s", "fonte_npb")),
        "comportamento_temporal": (analysis.temporal, GROUP_FIELDS),
        "sensibilidade": (analysis.sensitivity, GROUP_FIELDS + ("cenario",)),
        "inconsistencias": ([
            *(issue.row() for issue in issues),
            *(issue.row(campaign.key) for campaign in campaigns for issue in campaign.issues),
            *(issue.row(item.campaign.key, item.id) for item in attempts for issue in item.issues),
        ], ISSUE_FIELDS),
        "ambientes": ((
            {"campanha": campaign.key, "arquivo_ambiente": env.source.name, **env.values, "linhas_dos_campos": env.lines}
            for campaign in campaigns if (env := campaign.environment)
        ), ("campanha", "arquivo_ambiente")),
        "nos_ambiente": ((
            {"campanha": campaign.key, **host} for campaign in campaigns if campaign.environment
            for host in campaign.environment.hosts
        ), ("campanha", "host", "arquivo_ambiente")),
        "ranks_mpi": ((
            {"id_auditoria": item.id, "arquivo_txt": item.log.source.name, **row}
            for item in attempts if item.log for row in item.data.get("ranks_mpi", [])
        ), ("id_auditoria", "rank", "host", "arquivo_txt", "socket", "core")),
        "registros_csv": ((
            {"id_auditoria": item.id, "arquivo_csv": row.source.name, "linha_inicio": row.first, "linha_fim": row.last,
             "campos_sem_coluna": row.extra, **row.raw}
            for item in attempts for row in item.csvs
        ), ("id_auditoria", "arquivo_csv", "linha_inicio", "linha_fim") + CSV_FIELDS),
        "registros_plano": ((
            {"campanha": campaign.key, "arquivo_plano": row.source.name, "linha_inicio": row.first, "linha_fim": row.last,
             "campos_sem_coluna": row.extra, **row.raw}
            for campaign in campaigns for row in campaign.plan
        ), ("campanha", "arquivo_plano", "linha_inicio", "linha_fim") + PLAN_FIELDS),
        "blocos_txt": ((
            {"id_auditoria": item.id, "arquivo_txt": log.source.name, "linha_inicio": log.first, "linha_fim": log.last,
             "linha_rodape": log.footer_line, "sha256_captura_normalizada": log.output_sha, "exec_id_txt": log.exec_id,
             "cabecalho_txt": log.header, "rodape_txt": log.footer, "resumo_npb": log.summary, "linhas_resumo": log.summary_lines}
            for item in attempts for log in item.blocks
        ), ("id_auditoria", "arquivo_txt", "linha_inicio", "linha_fim")),
    }
    target.mkdir(parents=True, exist_ok=True)
    for name, (rows, fields) in files.items():
        write_csv(target / f"{name}.csv", rows, fields)


def run(raw: Path, out: Path) -> None:
    """Gera artefatos a partir do snapshot lido e confere os inputs antes de publicar."""
    raw = raw.resolve()
    if out.is_symlink():
        raise ValueError(f"Diretório de saída é um link simbólico: {out}")
    out = out.resolve()
    if not raw.is_dir():
        raise ValueError(f"Diretório de entrada não encontrado: {raw}")
    if out.is_relative_to(raw) or raw.is_relative_to(out):
        raise ValueError("As árvores de entrada e saída devem estar em diretórios separados.")
    sources, campaigns, issues = discover(raw)
    if not sources:
        raise ValueError(f"Nenhum arquivo de entrada em {raw}")
    attempts, plans = [], {}
    for campaign in campaigns:
        load_campaign(campaign)
        positions = plan_positions(campaign)
        plans[campaign.key] = positions
        items = associate(campaign)
        for item in items:
            validate_attempt(item, positions)
        verify_campaign_sequence(items)
        reconcile_repetitions(campaign, items)
        for item in items:
            accepted = item.data["aceita_coleta"]
            if accepted is not None and accepted != (item.state == VALID):
                item.add(WARNING, "coleta_e_auditoria_divergem", f"Coletor {item.data['status_coleta']}, auditoria {item.state}.")
        attempts.extend(items)
        LOG.info("%s · %d tentativas, %s", campaign.key, len(items), dict(sorted(Counter(item.state for item in items).items())))
    issues.extend(compare_environments(campaigns))
    inventory = [source.inventory() for source in sources]
    analysis = build_analysis(campaigns, attempts, plans)
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent, prefix=".npb-auditoria-") as tmp:
        stage = Path(tmp)
        (stage / "manifestos").mkdir()
        code = code_manifest(PROJECT)
        snapshot = sha256(json_text(inventory).encode()).hexdigest()
        write_json(stage / "manifestos/dados_entrada.json", {"estado_entrada_sha256": snapshot, "arquivos": inventory})
        write_json(stage / "manifestos/reproducibilidade.json", {
            **code, "estado_entrada_sha256": snapshot,
            "metrica_principal": "Time in seconds", "intervalo": "t bilateral 95%, ddof=1",
            "quartis": "linear (tipo 7)", "seed_analise": None,
        })
        write_tables(stage / "tabelas", attempts, campaigns, analysis, issues, inventory)
        LOG.info("Gerando gráficos e relatórios para %d linhas de cobertura.", len(analysis.groups))
        make_all(analysis.groups, stage / "graficos")
        write_reports(stage / "relatorios", out / "relatorios", raw, inventory, campaigns, attempts, issues, analysis)
        current_paths = {path for path in raw.rglob("*") if path.is_file()}
        if current_paths != {source.path for source in sources} or any(hash_file(source.path) != source.sha for source in sources):
            raise ValueError("O conjunto de entrada mudou durante a auditoria. Rode novamente sobre um snapshot estável.")
        updated = publish(stage, out)
    LOG.info("%d arquivos examinados, %d tentativas agrupadas, %d artefatos atualizados em %s.", len(sources), len(attempts), updated, out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audita saídas, planos e ambiente dos experimentos NPB-MPI.")
    parser.add_argument("--raw", type=Path, default=Path("raw"), help="diretório de arquivos brutos")
    parser.add_argument("--out", type=Path, default=Path("analysis/auditoria"), help="diretório de artefatos da auditoria")
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(levelname)s %(message)s", level=logging.WARNING, stream=sys.stderr)
    LOG.setLevel(logging.INFO)
    try:
        run(args.raw, args.out)
    except (OSError, ValueError) as error:
        LOG.error("%s", error)
        return 1
    return 0
