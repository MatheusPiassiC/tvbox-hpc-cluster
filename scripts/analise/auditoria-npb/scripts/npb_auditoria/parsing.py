"""Leitura dos CSVs v5.4 e dos envelopes de stdout/stderr, com linhas físicas."""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from io import StringIO
from math import isfinite
from pathlib import Path
import re
from typing import Any, Callable

from .model import Block, Campaign, CONTRADICTION, CsvRecord, Issue, MISSING, Source, WARNING

CSV_FIELDS = tuple("""
experimento_id exec_id benchmark classe np n_nos distribuicao tentativa repeticao_valida
inicio fim tempo_s mops_total mops_por_processo processos_ativos verificacao exit_code
status motivo tempo_parede_s cpu_ocupada_max_antes_pct mem_disp_min_antes_mb temp_max_antes_c
temp_max_durante_c freq_min_durante_mhz mem_disp_min_durante_mb binario_sha256
ambiente_sha256 comando saida_arquivo saida_linha_inicial fase bloco governor_antes
freq_max_permitida_antes_mhz swap_livre_min_antes_mb
""".split())
PLAN_FIELDS = ("bloco", "ordem_no_bloco", "np")
FILE_PATTERN = re.compile(r"npb_(\d+)_([A-Z]{2})_([A-Z])(?:(-plano)\.csv|(_ambiente|_saidas)\.txt|(\.csv))")
ROLES = {"-plano": "plano", "_ambiente": "ambiente", "_saidas": "saidas", ".csv": "resultados"}
SHA_PATTERN = re.compile(r"[0-9a-fA-F]{64}")
NUMBER = r"[+-]?\d+(?:\.\d+)?(?:[eEdD][+-]?\d{1,3})?"
HEADER = re.compile(r"^##### EXEC\b(?:\s+([^|\s]+))?(.*)$")
FOOTER = re.compile(r"^----- fim EXEC\b(?:\s+(\S+))?(.*?)\s*-----\s*$")
CAPTURE = "----- saída original (stdout+stderr) -----"
COMPLETED = re.compile(r"^\s*([A-Z]{2}) Benchmark Completed\.?\s*$")
OUTPUT_ID = re.compile(r"SAÍDAS ORIGINAIS DO NPB - experimento (\d+) \(([A-Z]{2}), classe ([A-Z])\)")
PRECHECK = re.compile(
    rf"^Pré-condições: cpu_max=({NUMBER})% mem_min=({NUMBER})MB "
    rf"temp_max=({NUMBER})C freq_max=({NUMBER}) kHz governor=(\S+)\s*$"
)
BANNER = re.compile(r"^\s*NAS Parallel Benchmarks\s+(\S+)\s+--\s+([A-Z]{2}) Benchmark\b")
EARLY_PROCESSES = re.compile(r"^\s*(?:Total number of processes|Number of processes)\s*:\s*(\d+)\s*$")
EARLY_SUCCESS = re.compile(r"^\s*(?:Result )?Verification Successful\s*$", re.I)
EARLY_FAILURE = re.compile(r"^\s*(?:Result )?Verification (?:Failed|Unsuccessful)\b.*$", re.I)
INIT_TIME = re.compile(rf"^\s*Initialization time\s*[:=]\s*({NUMBER})(?:\s+seconds)?\s*$")
EP_TIME = re.compile(rf"^\s*CPU Time\s*=\s*({NUMBER})\s*$")
COMPILE_OPTION = re.compile(r"^\s+([A-Z][A-Z0-9_]+)\s*=\s*(.*?)\s*$")


def integer(value: str) -> int:
    if not re.fullmatch(r"[+-]?[0-9]+", value):
        raise ValueError("esperado inteiro")
    return int(value)


def positive(value: str) -> int:
    result = integer(value)
    if result < 1:
        raise ValueError("esperado inteiro positivo")
    return result


def decimal(value: str) -> Decimal:
    if not re.fullmatch(NUMBER, value):
        raise ValueError("esperado número finito com ponto decimal")
    parsed = Decimal(value.replace("d", "e").replace("D", "E"))
    if not isfinite(float(parsed)):
        raise ValueError("número excede a precisão suportada")
    return parsed


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None or "T" not in value:
        raise ValueError("esperado ISO 8601 com horário e fuso")
    return result


def digest(value: str) -> str:
    if not SHA_PATTERN.fullmatch(value):
        raise ValueError("esperado SHA-256 hexadecimal")
    return value.lower()


def distribution(value: str) -> dict[str, int]:
    hosts = {}
    for item in value.split(";"):
        host, sep, count = item.partition("=")
        if not sep or not re.fullmatch(r"[a-zA-Z0-9_.-]+", host) or host in hosts:
            raise ValueError("esperado host=qtd, com hosts únicos")
        hosts[host] = positive(count)
    return hosts


CONVERTERS: dict[str, Callable[[str], Any]] = dict.fromkeys((
    "experimento_id", "np", "n_nos", "tentativa", "repeticao_valida", "processos_ativos",
    "saida_linha_inicial", "bloco", "ordem_no_bloco",
), positive)
CONVERTERS["exit_code"] = integer
CONVERTERS.update(dict.fromkeys((
    "tempo_s", "mops_total", "mops_por_processo", "tempo_parede_s", "cpu_ocupada_max_antes_pct",
    "mem_disp_min_antes_mb", "temp_max_antes_c", "temp_max_durante_c", "freq_min_durante_mhz",
    "mem_disp_min_durante_mb", "freq_max_permitida_antes_mhz", "swap_livre_min_antes_mb",
), decimal))
CONVERTERS.update(dict.fromkeys(("inicio", "fim"), timestamp))
CONVERTERS.update(dict.fromkeys(("binario_sha256", "ambiente_sha256"), digest))
CONVERTERS["distribuicao"] = distribution

SUMMARY_FIELDS: dict[str, tuple[str, Callable[[str], Any]]] = {
    "Class": ("classe", str),
    "Size": ("tamanho", lambda text: re.sub(r"\s*[xX]\s*", "x", text)),
    "Iterations": ("iteracoes", integer),
    "Time in seconds": ("tempo_s", decimal),
    "Total processes": ("processos_total", positive),
    "Active processes": ("processos_ativos", positive),
    "Mop/s total": ("mops_total", decimal),
    "Mop/s/process": ("mops_por_processo", decimal),
    "Operation type": ("operacao", str),
    "Verification": ("verificacao", str.upper),
    "Version": ("versao", str),
    "Compile date": ("data_compilacao", str),
}


def decode(source: Source, issues: list[Issue]) -> str | None:
    try:
        return source.text
    except UnicodeDecodeError as error:
        issues.append(Issue(MISSING, "codificacao_invalida", f"UTF-8 inválido no byte {error.start}.", (source.name,)))
        return None


def discover(root: Path) -> tuple[list[Source], list[Campaign], list[Issue]]:
    """Identifica conjuntos pelos nomes e deixa a semântica a cargo dos parsers."""
    sources, campaigns, issues = [], {}, []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        name = (Path(root.name) / relative).as_posix()
        match = FILE_PATTERN.fullmatch(path.name)
        kind = next((role for suffix, role in ROLES.items() if match and suffix in match.groups()[3:]), "outro")
        source = Source(path, name, kind, path.read_bytes())
        sources.append(source)
        if match is None:
            issues.append(Issue(WARNING, "arquivo_fora_do_esquema", "Arquivo inventariado fora dos formatos reconhecidos.", (name,)))
            continue
        experiment, benchmark, cls = match.group(1, 2, 3)
        stem = f"npb_{experiment}_{benchmark}_{cls}"
        key = (relative.parent / stem).as_posix()
        campaign = campaigns.setdefault(key, Campaign(key, int(experiment), benchmark, cls))
        campaign.sources[kind] = source
        if relative.parent.name != benchmark:
            campaign.issues.append(Issue(WARNING, "diretorio_benchmark", f"Diretório diferente de {benchmark}.", (name,)))
    return sources, list(campaigns.values()), issues


def read_csv(source: Source, kind: str, issues: list[Issue]) -> list[CsvRecord]:
    """Lê registros com csv estrito, inclusive campos cotados e linhas múltiplas."""
    content = decode(source, issues)
    if content is None:
        return []
    reader = csv.reader(StringIO(content, newline=""), strict=True)
    expected = PLAN_FIELDS if kind == "plano" else CSV_FIELDS
    records: list[CsvRecord] = []
    first = 1
    try:
        header = next(reader, [])
        if not header or len(header) != len(set(header)):
            issues.append(Issue(MISSING, "cabecalho_csv_inutilizavel", "Cabeçalho vazio ou com colunas duplicadas.", (source.ref(1),)))
            return records
        missing = sorted(set(expected) - set(header))
        extra = sorted(set(header) - set(expected))
        if missing or extra:
            detail = f"Colunas ausentes {missing}, adicionais {extra}."
            issues.append(Issue(WARNING, "esquema_csv_divergente", detail, (source.ref(1),)))
        elif tuple(header) != expected:
            issues.append(Issue(WARNING, "ordem_colunas_csv", "Ordem das colunas diferente do esquema v5.4.", (source.ref(1),)))
        first = reader.line_num + 1
        for row in reader:
            last = reader.line_num
            raw = {key: row[idx] if idx < len(row) else None for idx, key in enumerate(header)}
            record = CsvRecord(source, first, last, raw, {}, row[len(header):])
            records.append(record)
            first = last + 1
            if len(row) != len(header):
                record.issues.append(Issue(
                    MISSING, "largura_csv", f"{len(row)} valores para {len(header)} colunas.", (record.ref,),
                ))
            for key, value in raw.items():
                clean = value.strip() if value is not None else ""
                if not clean:
                    continue
                try:
                    record.values[key] = CONVERTERS.get(key, str)(clean)
                except ValueError as error:
                    level = WARNING if key not in {"np", "bloco", "ordem_no_bloco", "experimento_id"} else MISSING
                    record.issues.append(Issue(level, "campo_csv_malformado", f"{key}={value!r}. {error}.", (record.ref,)))
    except csv.Error as error:
        issues.append(Issue(MISSING, "sintaxe_csv", f"Leitura interrompida. {error}.", (source.ref(first, reader.line_num),)))
    return records


def envelope_fields(parts: list[str], source_ref: str, issues: list[Issue]) -> dict[str, Any]:
    fields = {}
    for part in parts:
        key, sep, value = part.strip().partition("=")
        if not sep or not key or key in fields:
            issues.append(Issue(CONTRADICTION, "campo_envelope_ambiguo", repr(part), (source_ref,)))
            continue
        if not value:
            continue
        try:
            fields[key] = CONVERTERS.get(key, str)(value)
        except ValueError as error:
            issues.append(Issue(MISSING, "campo_envelope_malformado", f"{key}={value!r}. {error}.", (source_ref,)))
    return fields


def parse_summary(
    output: list[tuple[int, str]], source: Source, issues: list[Issue],
) -> tuple[dict[str, Any], dict[str, int], dict[str, Any]]:
    """Extrai o resumo final e mantém diagnósticos internos como evidência adicional."""
    summary: dict[str, Any] = {}
    lines: dict[str, int] = {}
    additional: dict[str, Any] = {}
    compile_options: dict[str, str] = {}
    in_compile_options = False
    for line_no, line in output:
        completed = COMPLETED.fullmatch(line)
        if completed:
            if "benchmark" in summary:
                issues.append(Issue(CONTRADICTION, "multiplos_resumos_npb", "Mais de um resumo no bloco.",
                                    (source.ref(lines["benchmark"]), source.ref(line_no))))
            else:
                summary["benchmark"], lines["benchmark"] = completed[1], line_no
            continue
        if "benchmark" in summary:
            if line.strip() == "Compile options:":
                in_compile_options = True
                additional["linha_compilacao_npb"] = line_no
                continue
            if in_compile_options:
                option = COMPILE_OPTION.fullmatch(line)
                if option:
                    name, setting = option.groups()
                    if name in compile_options and compile_options[name] != setting:
                        issues.append(Issue(CONTRADICTION, "opcao_compilacao_repetida", line.strip(), (source.ref(line_no),)))
                    compile_options.setdefault(name, setting)
                elif line.strip():
                    in_compile_options = False
                continue
            name, sep, raw = line.partition("=")
            field = SUMMARY_FIELDS.get(name.strip()) if sep else None
            if field is not None:
                key, convert = field
                try:
                    value = convert(raw.strip()) if raw.strip() else None
                except ValueError:
                    issues.append(Issue(MISSING, "campo_npb_malformado", line.strip(), (source.ref(line_no),)))
                    continue
                if key in summary and summary[key] != value:
                    issues.append(Issue(CONTRADICTION, "campo_npb_repetido", f"Valores divergentes de {name.strip()}.",
                                        (source.ref(lines[key]), source.ref(line_no))))
                elif key not in summary:
                    summary[key], lines[key] = value, line_no
            continue
        banner = BANNER.match(line)
        if banner:
            additional.update(benchmark_banner=banner[2], serie_npb_banner=banner[1], linha_banner=line_no)
        processes = EARLY_PROCESSES.fullmatch(line)
        if processes:
            additional.update(processos_cabecalho=int(processes[1]), linha_processos_cabecalho=line_no)
        if EARLY_SUCCESS.fullmatch(line):
            additional["linha_verificacao_intermediaria_sucesso"] = line_no
        if EARLY_FAILURE.fullmatch(line):
            additional["linha_verificacao_intermediaria_falha"] = line_no
        for pattern, key in ((INIT_TIME, "tempo_inicializacao_npb_s"), (EP_TIME, "tempo_cpu_ep_s")):
            timer = pattern.fullmatch(line)
            if timer:
                additional[key] = decimal(timer[1])
                additional[f"linha_{key}"] = line_no
    if compile_options:
        additional["opcoes_compilacao_npb"] = compile_options
    return summary, lines, additional


def parse_block(source: Source, section: list[tuple[int, str]], match: re.Match[str]) -> Block:
    issues: list[Issue] = []
    first, last = section[0][0], section[-1][0]
    identity, tail = match.groups()
    parts = tail.strip().split("|")
    tag = parts[1].strip() if len(parts) > 1 else ""
    header = envelope_fields(parts[2:], source.ref(first), issues)
    if re.fullmatch(r"[A-Z]{2}\.[A-Z]", tag):
        header["benchmark"], header["classe"] = tag.split(".")
    else:
        issues.append(Issue(MISSING, "cabecalho_txt_parcial", "Identificação benchmark.classe ausente.", (source.ref(first),)))
    final = [(idx, FOOTER.fullmatch(line)) for idx, line in section[1:] if line.startswith("----- fim EXEC")]
    final = [(idx, item) for idx, item in final if item is not None]
    footer: dict[str, Any] = {}
    footer_line = None
    if final:
        footer_line, ending = final[0]
        if len(final) > 1:
            issues.append(Issue(CONTRADICTION, "multiplos_rodapes", "Mais de um rodapé na tentativa.", (source.ref(first, last),)))
        if identity is not None and ending[1] != identity:
            issues.append(Issue(CONTRADICTION, "ids_abertura_fechamento", f"{identity!r} x {ending[1]!r}.",
                                (source.ref(first), source.ref(footer_line))))
        footer = envelope_fields(ending[2].split("|")[1:], source.ref(footer_line), issues)
        footer["exec_id"] = ending[1]
    precheck: dict[str, Any] = {}
    command = None
    command_line = precheck_line = capture_line = None
    for line_no, line in section[1:]:
        if line.strip() == CAPTURE:
            capture_line = line_no
            break
        if line.startswith("Comando:"):
            command, command_line = line.partition(":")[2].strip() or None, line_no
        if line.startswith("Pré-condições:"):
            precheck_line = line_no
            before = PRECHECK.fullmatch(line)
            if before:
                cpu, mem, temp, khz = map(decimal, before.groups()[:4])
                precheck = dict(cpu_ocupada_max_antes_pct=cpu, mem_disp_min_antes_mb=mem, temp_max_antes_c=temp,
                                freq_max_permitida_antes_mhz=khz / Decimal(1000), governor_antes=before[5])
            else:
                issues.append(Issue(WARNING, "precondicoes_formato", "Formato não reconhecido.", (source.ref(line_no),)))
    lower = capture_line if capture_line is not None else first
    upper = footer_line if footer_line is not None else last + 1
    output = [(idx, line) for idx, line in section if lower < idx < upper]
    output_text = "\n".join(line for _, line in output).strip("\n")
    output_sha = sha256(output_text.encode()).hexdigest() if output_text else None
    summary, summary_lines, additional = parse_summary(output, source, issues)
    if capture_line is None:
        issues.append(Issue(MISSING, "delimitador_captura_ausente", "Marcador de stdout+stderr ausente.", (source.ref(first, last),)))
    return Block(source, first, last, identity, header, footer, footer_line, command, command_line,
                 precheck, precheck_line, output, output_sha, summary, summary_lines, additional, issues)


def read_output(source: Source, issues: list[Issue]) -> tuple[dict[str, Any], list[Block]]:
    content = decode(source, issues)
    if content is None:
        return {}, []
    lines = list(enumerate(source.lines, 1))
    starts = [(idx, match) for idx, line in lines if (match := HEADER.fullmatch(line))]
    preamble = lines[: starts[0][0] - 1] if starts else lines
    meta = {}
    for idx, line in preamble:
        match = OUTPUT_ID.search(line)
        if match:
            meta.update(experimento_id=int(match[1]), benchmark=match[2], classe=match[3], linha=idx)
        match = re.search(r"Documentação do ambiente:\s*(\S+)\s*\|\s*CSV:\s*(\S+)", line)
        if match:
            meta.update(ambiente=match[1], resultados=match[2], linha_arquivos=idx)
    if not starts:
        issues.append(Issue(MISSING, "saida_sem_blocos", "Nenhum marcador de abertura reconhecido.", (source.name,)))
    blocks = []
    for index, (first, opening) in enumerate(starts):
        upper = starts[index + 1][0] - 1 if index + 1 < len(starts) else len(lines)
        while upper > first and not lines[upper - 1][1].strip():
            upper -= 1
        blocks.append(parse_block(source, lines[first - 1:upper], opening))
    return meta, blocks
