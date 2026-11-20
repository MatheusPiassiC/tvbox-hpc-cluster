"""Extração e comparação dos snapshots de plataforma e do protocolo v5.4."""

from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
from hashlib import sha256
import re
from typing import Any

from .model import Campaign, Environment, Issue, MISSING, Source, WARNING
from .parsing import decode, timestamp

ENV_ID = re.compile(r"DOCUMENTAÇÃO DO AMBIENTE EXPERIMENTAL - experimento (\d+) \(([A-Z]{2}), classe ([A-Z])\)")
SECTION = re.compile(r"^(\d)\. ")
HOST_SECTION = re.compile(r"^  ---------- (\S+)(?:  \[papel: (.*?)\])? ----------\s*$")
HOST_SLOT = re.compile(r"^\s+\| (\S+) slots=(\d+)\s*$")
FREQ_SNAPSHOT = re.compile(r"\bcpu(\d+): cur=(\d+) MHz max_permitida=(\d+) MHz")
TEMP_SNAPSHOT = re.compile(r"Temperatura (\S+ \([^)]+\)):\s*([\d.]+) C")
ENV_FIELDS = {
    "gerado_em": r"^  Gerado em\s*\.+:\s*(\S+)",
    "script": r"^  Script\s*\.+:\s*(.*)",
    "script_sha256": r"^  SHA-256 do script\s*:\s*([a-f0-9]{64})",
    "comando_modelo": r"^  Comando de execução \(modelo\):\s*(.+)",
    "processos_documentados": r"^    Nº de processos MPI \(np\)\s*\.+:\s*([0-9 ]+)",
    "repeticoes_protocolo": r"^  Repetições:\s*(\d+) blocos completos",
    "timeout_s": r"^  Timeout:\s*(\d+)s;",
    "cpu_max_pct": r"Condição prévia: CPU <= (\d+)%",
    "temp_max_c": r"Condição prévia:.*temperatura <= (\d+) C",
    "plataforma_declarada_sha256": r"SHA-256 da plataforma .*:\s*([a-f0-9]{64})",
    "binario": r"^  Caminho\s*\.+:\s*(\S+)",
    "binario_sha256": r"^  SHA-256\s*\.+:\s*([a-f0-9]{64})",
    "binario_bytes": r"^  Tamanho\s*\.+:\s*(\d+) bytes",
    "compilador_binario": r"^\s*\[\s*0\]\s+(.+)",
    "npb_pacote": r"versão pelo caminho: NPB([\d.]+)",
    "npb_fonte_declarado_sha256": r"^    Código-fonte idêntico ao tarball original .*sha256 ([a-f0-9]{64})",
}
PLAN_DECLARATION = re.compile(r"Semente aleatória: (\d+); plano: ([^;]+); SHA-256: ([a-f0-9]{64})")
HOST_FIELDS = {
    "hostname": "Hostname", "device_tree": "Modelo (device-tree)", "compatible": "Compatible (device-tree)",
    "distribuicao_so": "Distribuição", "debian": "Debian", "kernel": "Kernel", "arquitetura": "Architecture",
    "cpus": "CPU(s)", "nucleos_por_socket": "Core(s) per socket", "threads_por_nucleo": "Thread(s) per core",
    "cpu_modelo": "Model name", "driver_cpufreq": "Driver cpufreq", "governor": "Governor(es)",
    "cpuinfo_min_freq_mhz": "cpuinfo_min_freq", "cpuinfo_max_freq_mhz": "cpuinfo_max_freq",
    "scaling_min_freq_mhz": "scaling_min_freq", "scaling_max_freq_mhz": "scaling_max_freq",
    "memtotal_kb": "MemTotal", "swaptotal_kb": "SwapTotal", "link_mbit_s": "speed", "duplex": "duplex",
    "mtu": "mtu", "open_mpi": "Open MPI", "gcc": "gcc", "gfortran": "gfortran", "libc6": "pacote libc6",
    "snapshot_hora": "Data/hora", "uptime": "Uptime", "carga_1_5_15": "Load average (1/5/15 min)",
    "memavailable_snap_kb": "MemAvailable", "swapfree_snap_kb": "SwapFree",
}
HOST_KEYS = {label: key for key, label in HOST_FIELDS.items()}
HOST_INTS = {
    "cpus", "nucleos_por_socket", "threads_por_nucleo", "link_mbit_s", "mtu",
    "cpuinfo_min_freq_mhz", "cpuinfo_max_freq_mhz", "scaling_min_freq_mhz", "scaling_max_freq_mhz",
    "memtotal_kb", "swaptotal_kb", "memavailable_snap_kb", "swapfree_snap_kb",
}


def read_hosts(source: Source, stable: list[str], first: int, volatile: list[str], snapshot_first: int) -> list[dict[str, Any]]:
    hosts: dict[str, dict[str, Any]] = {}
    for chunk, base, is_snapshot in ((stable, first, False), (volatile, snapshot_first, True)):
        host = None
        for number, line in enumerate(chunk, base):
            header = HOST_SECTION.fullmatch(line)
            if header:
                name, role = header.groups()
                host = hosts.setdefault(name, {"host": name})
                host["linha_snapshot" if is_snapshot else "linha_plataforma"] = number
                if role:
                    host["papel"] = role
                continue
            if SECTION.match(line):
                host = None
            if host is None:
                continue
            label, colon, raw = line.strip().partition(":")
            value = raw.strip()
            key = HOST_KEYS.get(label)
            if colon and key and value:
                if key in HOST_INTS:
                    token = value.split()[0]
                    if token.isdecimal():
                        host[key] = int(token)
                else:
                    host[key] = value
            frequency = FREQ_SNAPSHOT.search(line)
            if is_snapshot and frequency:
                host.setdefault("freq_instante_mhz_por_cpu", {})[frequency[1]] = int(frequency[2])
                host.setdefault("freq_limite_snapshot_mhz_por_cpu", {})[frequency[1]] = int(frequency[3])
            temperature = TEMP_SNAPSHOT.search(line)
            if is_snapshot and temperature:
                host.setdefault("temperatura_snapshot_c", {})[temperature[1]] = float(temperature[2])
    return [{"arquivo_ambiente": source.name, **host} for host in hosts.values()]


def read_environment(source: Source) -> Environment:
    issues: list[Issue] = []
    content = decode(source, issues)
    values: dict[str, Any] = {}
    refs: dict[str, int] = {}
    if content is None:
        return Environment(source, values, refs, [], [], issues)
    lines = source.lines
    sections = {int(match[1]): n for n, line in enumerate(lines, 1) if (match := SECTION.match(line))}
    for key, pattern in ENV_FIELDS.items():
        match = re.search(pattern, content, re.M)
        if match:
            found: Any = match[1].strip()
            if key in {"timeout_s", "repeticoes_protocolo", "binario_bytes", "cpu_max_pct", "temp_max_c"}:
                found = int(found)
            if key == "processos_documentados":
                found = [int(item) for item in found.split()]
            values[key] = found
            refs[key] = content.count("\n", 0, match.start()) + 1
    header = ENV_ID.search(content)
    if header:
        values.update(experimento_id=int(header[1]), benchmark=header[2], classe=header[3])
        for key in ("experimento_id", "benchmark", "classe"):
            refs[key] = content.count("\n", 0, header.start()) + 1
    if "gerado_em" in values:
        try:
            values["gerado_em"] = timestamp(values["gerado_em"])
        except ValueError:
            issues.append(Issue(WARNING, "hora_ambiente_malformada", values["gerado_em"], (source.ref(refs["gerado_em"]),)))
            del values["gerado_em"]
    declared = PLAN_DECLARATION.search(content)
    if declared:
        values.update(semente=int(declared[1]), plano_arquivo=declared[2], plano_declarado_sha256=declared[3])
        for key in ("semente", "plano_arquivo", "plano_declarado_sha256"):
            refs[key] = content.count("\n", 0, declared.start()) + 1
    first, end = sections.get(2, 1), sections.get(4, 1)
    snapshot_first, snapshot_end = sections.get(5, 1), sections.get(6, len(lines) + 1)
    stable = lines[first - 1:end - 1] if end > first else []
    raw_stable = content.splitlines(keepends=True)[first - 1:end - 1]
    if stable:
        values["secoes_2_3_sha256"] = sha256("".join(raw_stable).encode()).hexdigest()
        values["linha_secoes_2_3_fim"] = end - 1
        refs["secoes_2_3_sha256"] = first
    else:
        issues.append(Issue(MISSING, "secoes_ambiente_ausentes", "Seções 2 e 3 sem limites reconhecíveis.", (source.name,)))
    hosts = read_hosts(source, stable, first, lines[snapshot_first - 1:snapshot_end - 1], snapshot_first)
    slots = []
    compilation = {}
    segment = None
    for number, line in enumerate(stable, first):
        subsection = re.match(r"^2\.(\d) ", line)
        if subsection:
            segment = subsection[1]
        if segment == "2":
            match = HOST_SLOT.fullmatch(line)
            if match:
                slots.append((match[1], int(match[2])))
                refs.setdefault("hostfile_slots", number)
            fingerprint = re.search(r"SHA-256:\s*([a-f0-9]{64})", line)
            if fingerprint:
                values["hostfile_declarado_sha256"] = fingerprint[1]
                refs["hostfile_declarado_sha256"] = number
        if line.startswith("3.3 ") and number < len(lines):
            segment = "compilacao"
            match = re.search(r"SHA-256:\s*([a-f0-9]{64})", lines[number])
            if match:
                values["make_def_declarado_sha256"] = match[1]
                refs["make_def_declarado_sha256"] = number + 1
        if segment == "compilacao":
            option = re.fullmatch(r"\s+\| ([A-Z][A-Z0-9_]+)\s*=\s*(.*?)\s*", line)
            if option:
                compilation[option[1]] = option[2]
                refs.setdefault("make_def_opcoes", number)
    if slots:
        values["hostfile_slots"] = slots
    if compilation:
        values["make_def_opcoes"] = compilation
    executable = re.search(r"^  mpirun \(Open MPI\) (\S+)\s*$", content, re.M)
    if executable:
        values["open_mpi_coordenador"] = executable[1]
        refs["open_mpi_coordenador"] = content.count("\n", 0, executable.start()) + 1
    stable_manual = [
        (number, line.strip()) for number, line in enumerate(stable, first)
        if re.match(r"\s*\| (?:TV Box|SoC |Switch \(|Velocidade nominal)", line) and not line.endswith(":")
    ]
    if stable_manual:
        refs["linhas_info_manual"] = stable_manual[0][0]
        values["linhas_info_manual"] = [number for number, _ in stable_manual]
    values["sem_reposicao_documentada"] = "sem reposição de inválidas." in content
    values["sem_aquecimento_documentado"] = "Aquecimento: NÃO realizado." in content
    values["monitoramento_desativado_documentado"] = "Monitoramento durante a execução: DESATIVADO" in content
    values["secao_snapshot"] = source.ref(snapshot_first, snapshot_end - 1) if 5 in sections else None
    return Environment(source, values, refs, stable, hosts, issues)


def compare_environments(campaigns: list[Campaign]) -> list[Issue]:
    """Compara a plataforma documentada e mantém as coordenadas das diferenças."""
    have_env = [campaign.environment for campaign in campaigns if campaign.environment is not None]
    stable = [env for env in have_env if env.stable_lines]
    issues: list[Issue] = []
    if stable:
        base = stable[0]
        for other in stable[1:]:
            if base.values["secoes_2_3_sha256"] == other.values["secoes_2_3_sha256"]:
                continue
            changes = SequenceMatcher(None, base.stable_lines, other.stable_lines, autojunk=False)
            first_base = base.lines["secoes_2_3_sha256"]
            first_other = other.lines["secoes_2_3_sha256"]
            for tag, a, b, c, d in changes.get_opcodes():
                if tag != "equal":
                    refs = (base.source.ref(first_base + a, first_base + b - 1), other.source.ref(first_other + c, first_other + d - 1))
                    issues.append(Issue(WARNING, "texto_plataforma_divergente", f"Trechos das seções 2/3 diferem ({tag}).", refs))
    for field in ("plataforma_declarada_sha256", "script_sha256", "hostfile_declarado_sha256",
                  "make_def_declarado_sha256", "open_mpi_coordenador", "npb_pacote", "compilador_binario",
                  "timeout_s", "cpu_max_pct", "temp_max_c"):
        groups: dict[Any, list[str]] = defaultdict(list)
        for env in have_env:
            if field in env.values:
                groups[env.values[field]].append(env.ref(field))
        if len(groups) > 1:
            refs = tuple(ref for refs in groups.values() for ref in refs)
            issues.append(Issue(WARNING, "metadados_ambiente_divergentes", f"{field} varia entre campanhas: {list(groups)}.", refs))
    binaries: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for campaign in campaigns:
        env = campaign.environment
        if env and env.values.get("binario_sha256"):
            binaries[campaign.benchmark, campaign.problem_class][env.values["binario_sha256"]].append(env.ref("binario_sha256"))
    for (benchmark, cls), groups in binaries.items():
        if len(groups) > 1:
            refs = tuple(ref for refs in groups.values() for ref in refs)
            issues.append(Issue(WARNING, "binarios_distintos_mesmo_problema",
                                f"{benchmark}.{cls} tem campanhas com executáveis de hashes diferentes.", refs))
    return issues
