"""Testes da auditoria com dados sintéticos, sem escrever em raw/."""

from __future__ import annotations

import csv
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.npb_auditoria.cli import run
from scripts.npb_auditoria.environment import read_environment
from scripts.npb_auditoria.model import (
    Attempt, Campaign, CONFLICT, Environment, INVALID, MISSING, Source, UNCERTAIN, VALID,
)
from scripts.npb_auditoria.mpi import read_mpi
from scripts.npb_auditoria.output import publish
from scripts.npb_auditoria.parsing import CAPTURE, CSV_FIELDS, read_csv, read_output
from scripts.npb_auditoria.reconcile import associate, plan_positions, reconcile_repetitions, verify_campaign_sequence
from scripts.npb_auditoria.statistics import build_analysis, describe, scaling
from scripts.npb_auditoria.validation import validate_attempt

EXEC_ID = "1-0001"
START = "2026-01-01T12:00:00-03:00"
END = "2026-01-01T12:00:16-03:00"
LOG_NAME = "npb_1_EP_A_saidas.txt"
BIN = "a" * 64
PLATFORM = "b" * 64


def source(name: str, role: str, value: str) -> Source:
    return Source(Path(name), f"raw/EP/{name}", role, value.encode("utf-8"))


def csv_text(rows: list[dict], columns: tuple[str, ...] = CSV_FIELDS) -> str:
    rendered = StringIO(newline="")
    writer = csv.DictWriter(rendered, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return rendered.getvalue()


def command(p: int) -> str:
    return f"mpirun -np {p} --map-by slot --bind-to core /synthetic/ep.A.x"


def mpi_output(p: int, host: str, binding: bool, same_core: bool) -> str:
    job = " Data for JOB [91,1] offset 0 Total slots allocated 32"
    head = " ========== JOB MAP =========="
    tail = " ================================="
    node = f" Data for node: {host}\tNum slots: 4\tMax slots: 0\tNum procs: {p}"
    ranks = [f" Process OMPI jobid: [91,1] App: 0 Process rank: {i} Bound: N/A" for i in range(p)]
    report = [
        f"[{host}:123] MCW rank {i} bound to socket 0[core {0 if same_core else i}[hwt 0]]: [B/././.]"
        for i in range(p) if binding
    ]
    return "\n".join([job, head, node, *ranks, tail, job, head, node, *ranks, tail, *report])


def output_text(
    *, time: str = "14.00", p: int = 2, active: str | None = None, verification: str = "SUCCESSFUL",
    status: str = "VALIDA", exit_code: str = "0", host: str = "server", footer: bool = True, mapping: bool = True,
    binding: bool = True, same_core: bool = False, diagnostic: str = "", summary: bool = True,
) -> str:
    end = f"----- fim EXEC {EXEC_ID} | exit_code={exit_code} | status={status} | motivo=fixture | fim={END} -----"
    size = [
        " NAS Parallel Benchmarks 3.4 -- EP Benchmark", f" Total number of processes: {p}",
        " EP Benchmark Completed.", " Class = A", " Size = 536870912", " Iterations = 0",
        f" Time in seconds = {time}", f" Total processes = {p}", f" Active processes= {active if active is not None else p}",
        " Mop/s total = 38.00", " Mop/s/process = 19.00", f" Verification = {verification}",
        " Version = 3.4.4", " Compile date = 01 Oct 2026", " Compile options:", "    MPIFC = mpif90",
    ]
    return "\n".join([
        " SAÍDAS ORIGINAIS DO NPB - experimento 1 (EP, classe A)",
        f"##### EXEC {EXEC_ID} | EP.A | np={p} | fase=MEDICAO | bloco=1 | tentativa=1 | inicio={START}",
        f"Comando: {command(p)}",
        "Pré-condições: cpu_max=3% mem_min=1520MB temp_max=40.0C freq_max=1500000 kHz governor=ondemand",
        CAPTURE, mpi_output(p, host, binding, same_core) if mapping else "", diagnostic,
        *(size if summary else []), end if footer else "", "",
    ])


def fixture(
    *, csv_overrides: dict | None = None, n_csv_rows: int = 1, second_csv: dict | None = None,
    plan: str | None = None, **log_options,
) -> tuple[Campaign, list[Attempt], dict]:
    p = log_options.get("p", 2)
    row = {
        "experimento_id": 1, "exec_id": EXEC_ID, "benchmark": "EP", "classe": "A", "np": p,
        "n_nos": 1, "distribuicao": f"{log_options.get('host', 'server')}={p}", "tentativa": 1,
        "repeticao_valida": 1, "inicio": START, "fim": END, "bloco": 1, "fase": "MEDICAO",
        "tempo_s": log_options.get("time", "14.00"), "tempo_parede_s": "16.50",
        "processos_ativos": p, "verificacao": log_options.get("verification", "SUCCESSFUL"),
        "exit_code": log_options.get("exit_code", "0"), "status": log_options.get("status", "VALIDA"),
        "motivo": "fixture", "binario_sha256": BIN, "ambiente_sha256": PLATFORM, "comando": command(p),
        "saida_arquivo": LOG_NAME, "saida_linha_inicial": 2,
        "governor_antes": "ondemand", "freq_max_permitida_antes_mhz": 1500,
    }
    row.update(csv_overrides or {})
    rows = [row] * n_csv_rows
    if second_csv:
        rows.append({**row, **second_csv})
    texts = {
        "resultados": source("npb_1_EP_A.csv", "resultados", csv_text(rows)),
        "saidas": source(LOG_NAME, "saidas", output_text(**log_options)),
        "plano": source("npb_1_EP_A-plano.csv", "plano", plan if plan is not None else f"bloco,ordem_no_bloco,np\n1,1,{p}\n"),
    }
    campaign = Campaign("EP/npb_1_EP_A", 1, "EP", "A", texts)
    campaign.csv = read_csv(texts["resultados"], "resultados", campaign.issues)
    campaign.plan = read_csv(texts["plano"], "plano", campaign.issues)
    campaign.output_header, campaign.blocks = read_output(texts["saidas"], campaign.issues)
    campaign.environment = Environment(
        source("synthetic_ambiente.txt", "ambiente", "fixture"),
        {"timeout_s": 3600, "temp_max_c": 80, "plataforma_declarada_sha256": PLATFORM, "binario_sha256": BIN},
        {}, [], [], [],
    )
    positions = plan_positions(campaign)
    attempts = associate(campaign)
    for item in attempts:
        validate_attempt(item, positions)
    verify_campaign_sequence(attempts)
    reconcile_repetitions(campaign, attempts)
    return campaign, attempts, positions


def codes(attempt: Attempt) -> set[str]:
    return {issue.code for issue in attempt.issues}


class CsvTests(unittest.TestCase):
    def test_quoted_values_and_physical_lines(self):
        campaign, attempts, _ = fixture(csv_overrides={"motivo": "com vírgula, e\ncom duas linhas"})
        record = campaign.csv[0]
        self.assertEqual((record.first, record.last), (2, 3))
        self.assertEqual(record.raw["motivo"], "com vírgula, e\ncom duas linhas")
        self.assertEqual(record.values["tempo_s"], Decimal("14.00"))
        self.assertNotIn("temp_max_durante_c", record.values)
        self.assertEqual(attempts[0].state, VALID)

    def test_malformed_values_are_preserved(self):
        sample = source("x.csv", "plano", "bloco,ordem_no_bloco,np\n1,1,bad\n2,1,4,extra\n")
        rows = read_csv(sample, "plano", [])
        self.assertEqual(rows[0].raw["np"], "bad")
        self.assertNotIn("np", rows[0].values)
        self.assertEqual(rows[0].issues[0].level, MISSING)
        self.assertEqual(rows[1].extra, ["extra"])
        self.assertEqual(rows[1].issues[0].code, "largura_csv")

    def test_csv_syntax_reports_unrecoverable_range(self):
        issues = []
        data = source("x.csv", "plano", 'bloco,ordem_no_bloco,np\n1,1,2\n2,1,"4\n')
        rows = read_csv(data, "plano", issues)
        self.assertEqual(len(rows), 1)
        self.assertEqual(issues[0].code, "sintaxe_csv")
        self.assertTrue(issues[0].sources[0].endswith(":3"))

    def test_ambiente_extracts_declared_hash_and_threshold(self):
        digest = "e" * 64
        snippet = (
            " DOCUMENTAÇÃO DO AMBIENTE EXPERIMENTAL - experimento 1 (EP, classe A)\n"
            "2. PLATAFORMA\n2.2 Hostfile\n    | server slots=4\n3. SOFTWARE\n"
            f" >>> SHA-256 da plataforma (sem dados): {digest}\n"
            "4. EXECUTÁVEL\n5. ESTADO\n6. LIMITAÇÕES\n"
            "  Condição prévia: CPU <= 10%, temperatura <= 85 C.\n"
        )
        env = read_environment(source("e.txt", "ambiente", snippet))
        self.assertEqual(env.values["hostfile_slots"], [("server", 4)])
        self.assertEqual(env.values["temp_max_c"], 85)
        self.assertEqual(env.values["plataforma_declarada_sha256"], digest)
        self.assertNotEqual(env.values["secoes_2_3_sha256"], digest)


class ExecutionTests(unittest.TestCase):
    def test_complete_exec_and_association(self):
        campaign, attempts, plan = fixture()
        item = attempts[0]
        self.assertEqual(len(attempts), 1)
        self.assertEqual(item.state, VALID, item.issues)
        self.assertTrue(item.data["aceita_coleta"])
        self.assertTrue(item.data["ordem_confiavel"])
        self.assertEqual(item.log.first, 2)
        self.assertIs(item.plan_rows[0], plan[(1, 2)][0])
        self.assertEqual(item.log.summary["tempo_s"], Decimal("14.00"))
        self.assertEqual(item.log.additional["opcoes_compilacao_npb"]["MPIFC"], "mpif90")
        self.assertIn(campaign.key, item.id)

    def test_completion_without_period(self):
        text = output_text().replace("EP Benchmark Completed.", "IS Benchmark Completed")
        _, blocks = read_output(source(LOG_NAME, "saidas", text), [])
        self.assertEqual(blocks[0].summary["benchmark"], "IS")

    def test_missing_values_can_use_independent_source(self):
        _, attempts, _ = fixture(csv_overrides={"exec_id": "", "tempo_s": "", "processos_ativos": "", "motivo": ""})
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].key, EXEC_ID)
        self.assertEqual(attempts[0].state, VALID)

    def test_repeated_maps_and_bindings_are_not_extra_ranks(self):
        _, (item,), _ = fixture()
        evidence = read_mpi(item.log)
        self.assertEqual(evidence.map_count, 2)
        self.assertEqual(evidence.map_layouts, 1)
        self.assertEqual(evidence.slots, {32})
        self.assertEqual(evidence.hosts, {0: "server", 1: "server"})
        self.assertEqual([row["core"] for row in evidence.rows], [0, 1])
        self.assertEqual(item.data["np_npb_ativos"], 2)

    def test_rank_reported_on_two_hosts_is_conflict(self):
        text = output_text(diagnostic="[node1:456] MCW rank 1 bound to socket 0[core 1[hwt 0]]: [./B/./.]")
        _, blocks = read_output(source(LOG_NAME, "saidas", text), [])
        evidence = read_mpi(blocks[0])
        self.assertEqual(evidence.hosts, {0: "server"})
        self.assertIn("rank_em_hosts_diferentes", {issue.code for issue in evidence.issues})

    def test_slot_and_affinity_violations(self):
        _, (nfs,), _ = fixture(host="nfs")
        _, (overlap,), _ = fixture(same_core=True)
        self.assertEqual(nfs.state, INVALID)
        self.assertIn("participacao_nfs", codes(nfs))
        self.assertEqual(overlap.state, INVALID)
        self.assertIn("afinidade_incompativel", codes(overlap))

    def test_missing_map_is_inconclusive(self):
        _, (item,), _ = fixture(mapping=False)
        self.assertEqual(item.state, UNCERTAIN)
        self.assertEqual(item.data["estado_mapa"], "inconclusivo")
        self.assertIsNone(item.data["n_nos_observados"])

    def test_absent_binding_is_inconclusive_with_map_confirmed(self):
        _, (item,), _ = fixture(binding=False)
        self.assertEqual(item.state, UNCERTAIN)
        self.assertEqual(item.data["estado_mapa"], "confirmado")
        self.assertEqual(item.data["estado_binding"], "inconclusivo")
        self.assertIn("binding_individual_ausente", codes(item))

    def test_collector_status_is_not_scientific_verification(self):
        _, (item,), _ = fixture(verification="FAILED")
        self.assertTrue(item.data["aceita_coleta"])
        self.assertEqual(item.state, INVALID)
        self.assertIn("verificacao_npb_malsucedida", codes(item))

    def test_absent_verification_and_truncation(self):
        _, (item,), _ = fixture(footer=False, summary=False)
        self.assertEqual(item.state, UNCERTAIN)
        self.assertTrue({"saida_sem_rodape", "saida_sem_resumo_npb", "verificacao_npb_nao_confirmada"} <= codes(item))

    def test_timeout_and_sigkill_are_distinct(self):
        _, (timeout,), _ = fixture(status="TIMEOUT", exit_code="124", summary=False)
        _, (killed,), _ = fixture(status="FALHA_EXECUCAO", exit_code="137", summary=False)
        self.assertEqual(timeout.state, INVALID)
        self.assertIs(timeout.data["timeout_confirmado"], True)
        self.assertEqual(killed.state, INVALID)
        self.assertIs(killed.data["timeout_confirmado"], False)
        self.assertNotIn("erro_memoria", codes(killed))

    def test_notice_and_rejection_patterns(self):
        _, (notice,), _ = fixture(diagnostic="plm:rsh: Warning: setpgid failed with Permission denied")
        _, (rejection,), _ = fixture(diagnostic="Number of processes must be a perfect square", summary=False)
        self.assertEqual(notice.state, VALID)
        self.assertIn("aviso_stdout_stderr", codes(notice))
        self.assertEqual(rejection.state, INVALID)
        self.assertIn("np_nao_aceito", codes(rejection))

    def test_requested_and_active_mismatch(self):
        _, (attempt,), _ = fixture(active="1", csv_overrides={"processos_ativos": 1})
        self.assertIn(attempt.state, (INVALID, CONFLICT))
        self.assertIn("processos_npb_incompativeis", codes(attempt))
        self.assertEqual(attempt.data["np_solicitado"], 2)
        self.assertEqual(attempt.data["np_npb_ativos"], 1)

    def test_rounding_and_material_time_conflict(self):
        _, (rounded,), _ = fixture(time="14.04", csv_overrides={"tempo_s": "14.0"})
        _, (different,), _ = fixture(csv_overrides={"tempo_s": "14.01"})
        self.assertEqual(rounded.state, VALID)
        self.assertIn("arredondamento_tempo_s", codes(rounded))
        self.assertEqual(different.state, CONFLICT)
        self.assertIn("divergencia_tempo_s", codes(different))

    def test_duplicate_csv_preserves_records_and_counts_once(self):
        _, attempts, _ = fixture(n_csv_rows=2)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(len(attempts[0].csvs), 2)
        self.assertEqual(attempts[0].state, VALID)
        self.assertIn("id_csv_repetido", codes(attempts[0]))

    def test_divergent_duplicate_is_conflict(self):
        _, (item,), _ = fixture(second_csv={"tempo_s": "15.00"})
        self.assertEqual(item.state, CONFLICT)
        self.assertIsNone(item.csv)
        self.assertEqual(len(item.csvs), 2)

    def test_pointer_to_other_identity(self):
        _, attempts, _ = fixture(csv_overrides={"exec_id": "1-0099"})
        self.assertEqual(len(attempts), 2)
        self.assertTrue(all(item.state == CONFLICT for item in attempts))
        self.assertEqual(sum(len(item.blocks) for item in attempts), 1)

    def test_conflicting_logical_plan_rows(self):
        _, (item,), _ = fixture(plan="bloco,ordem_no_bloco,np\n1,1,2\n1,2,2\n")
        self.assertEqual(item.state, CONFLICT)
        self.assertEqual(len(item.plan_rows), 2)
        self.assertIn("chave_plano_duplicada", codes(item))


class StatisticTests(unittest.TestCase):
    def test_sample_moments_and_t_interval(self):
        row = describe([1, 2, 3])
        self.assertEqual(row["media_s"], 2)
        self.assertEqual(row["dp_amostral_s"], 1)
        self.assertEqual(row["variancia_amostral_s2"], 1)
        self.assertEqual((row["q1_s"], row["q3_s"]), (1.5, 2.5))
        self.assertAlmostEqual(row["ic95_inf_s"], 2 - 4.302652729696142 / 3**.5, places=9)
        self.assertAlmostEqual(row["ic95_sup_s"], 2 + 4.302652729696142 / 3**.5, places=9)

    def test_sparse_groups_have_missing_interval(self):
        self.assertIsNone(describe([])["media_s"])
        desc = describe([2])
        self.assertEqual(desc["media_s"], 2)
        self.assertIsNone(desc["dp_amostral_s"])
        self.assertIsNone(desc["ic95_inf_s"])

    def test_speedup_efficiency_and_reference_requirements(self):
        row = scaling(4, 6.0, 18.0, ("same",), ("same",))
        self.assertEqual((row["speedup"], row["eficiencia_pct"], row["desvio_speedup_do_ideal"]), (3, 75.0, -1))
        self.assertIsNone(scaling(4, 6.0, None, None, None)["speedup"])
        self.assertIsNone(scaling(4, 6.0, 18.0, ("a",), ("b",))["speedup"])
        self.assertTrue(scaling(2, 8.0, 18.0, ("a",), ("a",))["superlinear"])

    def test_incomplete_and_absent_levels(self):
        campaign, attempts, positions = fixture()
        analysis = build_analysis([campaign], attempts, {campaign.key: positions})
        ep = [row for row in analysis.groups if row.benchmark == "EP"]
        p1, p2 = ep[:2]
        self.assertEqual(p1.coverage["completude"], "ausente")
        self.assertEqual(p2.coverage["completude"], "incompleta")
        self.assertEqual(p2.description["n"], 1)
        self.assertIsNone(p2.scaling["speedup"])

    def test_sensitivity_to_missing_binding_does_not_enter_primary(self):
        campaign, attempts, positions = fixture(binding=False, p=1)
        analysis = build_analysis([campaign], attempts, {campaign.key: positions})
        scenario = next(r for r in analysis.sensitivity if r["benchmark"] == "EP" and r["np"] == 1 and "binding" in r["cenario"])
        self.assertEqual((scenario["n_principal"], scenario["n_cenario"]), (0, 1))
        self.assertFalse(attempts[0].data["inclusao_estatistica_principal"])


class PublicationTests(unittest.TestCase):
    def test_protects_preexisting_data_and_supports_updates(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            old, new = root / "publicado", root / "preparado"
            old.mkdir()
            new.mkdir()
            (old / "nota.md").write_text("trabalho anterior")
            (new / "tabela.csv").write_text("edicao 1")
            publish(new, old)
            (new / "tabela.csv").write_text("edicao 2")
            publish(new, old)
            self.assertEqual((old / "tabela.csv").read_text(), "edicao 2")
            (old / "tabela.csv").write_text("edicao manual")
            (new / "tabela.csv").write_text("edicao 3")
            with self.assertRaisesRegex(ValueError, "Arquivo preexistente"):
                publish(new, old)
            self.assertEqual((old / "tabela.csv").read_text(), "edicao manual")
            self.assertEqual((old / "nota.md").read_text(), "trabalho anterior")

    def test_identical_foreign_file_is_preserved_on_later_update(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            old, new = root / "publicado", root / "preparado"
            old.mkdir()
            new.mkdir()
            (old / "tabela.csv").write_text("conteudo igual de outra origem")
            (new / "tabela.csv").write_text("conteudo igual de outra origem")
            self.assertEqual(publish(new, old), 0)
            (new / "tabela.csv").write_text("conteudo posterior")
            with self.assertRaisesRegex(ValueError, "Arquivo preexistente"):
                publish(new, old)

    def test_rejects_output_inside_raw(self):
        with TemporaryDirectory() as temp:
            raw = Path(temp) / "raw"
            raw.mkdir()
            with self.assertRaisesRegex(ValueError, "diretórios separados"):
                run(raw, raw / "resultado")
            self.assertEqual(list(raw.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
