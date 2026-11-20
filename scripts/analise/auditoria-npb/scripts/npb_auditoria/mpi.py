"""Reconcilia as representações Open MPI 4.1 de job, rank, host e afinidade."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import re
from typing import Any

from .model import Block, CONTRADICTION, Issue, WARNING

JOB = re.compile(r"^\s*Data for JOB \[([^]]+)\] offset \d+ Total slots allocated (\d+)\s*$")
MAP = re.compile(r"^\s*=+\s+JOB MAP\s+=+\s*$")
END = re.compile(r"^\s*={8,}\s*$")
NODE = re.compile(r"^\s*Data for node:\s*(\S+)\s+Num slots:\s*\d+\s+Max slots:\s*\d+\s+Num procs:\s*(\d+)\s*$")
RANK = re.compile(r"^\s*Process OMPI jobid: \[([^]]+)\] App: \d+ Process rank:\s*(\d+) Bound:\s*(.*?)\s*$")
BIND = re.compile(r"^\s*\[([^:\]]+):\d+\]\s+MCW rank (\d+)(?:\s+bound to (.+?)|\s+is not bound.*?)\s*$")
CORE = re.compile(r"socket\s+(\d+)\[core\s+(\d+)\[")


@dataclass
class MapEvidence:
    rows: list[dict[str, Any]]
    jobs: set[str]
    slots: set[int]
    map_count: int
    map_closed: int
    map_layouts: int
    job_lines: int
    issues: list[Issue]

    @property
    def hosts(self) -> dict[int, str]:
        return {row["rank"]: row["host"] for row in self.rows if row["host"] is not None}

    @property
    def distribution(self) -> dict[str, int]:
        return dict(Counter(self.hosts.values()))


def socket_core(text: str) -> tuple[int, int] | None:
    match = CORE.search(text)
    return (int(match[1]), int(match[2])) if match else None


def read_mpi(block: Block) -> MapEvidence:
    """Conta ranks e bindings distintos após reconciliar cópias redundantes."""
    ranks: dict[int, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    cores: dict[int, dict[tuple[str, int, int], list[int]]] = defaultdict(lambda: defaultdict(list))
    report_lines: dict[int, list[int]] = defaultdict(list)
    unbound: dict[int, list[int]] = defaultdict(list)
    issues: list[Issue] = []
    jobs: set[str] = set()
    slots: set[int] = set()
    layouts: set[tuple] = set()
    hosts_in_map: dict[str, tuple[int, int, set[int]]] | None = None
    host: str | None = None
    map_count = map_closed = job_lines = 0
    for number, line in block.output:
        job = JOB.fullmatch(line)
        if job:
            jobs.add(job[1])
            slots.add(int(job[2]))
            job_lines += 1
        if MAP.fullmatch(line):
            map_count += 1
            hosts_in_map, host = {}, None
        elif hosts_in_map is not None and END.fullmatch(line):
            map_closed += 1
            layout = tuple(sorted((name, tuple(sorted(observed))) for name, (_, _, observed) in hosts_in_map.items()))
            if layout:
                layouts.add(layout)
            for name, (declared, source_line, observed) in hosts_in_map.items():
                if declared != len(observed):
                    level = CONTRADICTION if len(observed) > declared else WARNING
                    issues.append(Issue(level, "contagem_host_no_mapa",
                                        f"{name}: Num procs={declared}, {len(observed)} ranks distintos nesta representação.",
                                        (block.source.ref(source_line),)))
            hosts_in_map, host = None, None
        elif hosts_in_map is not None:
            node = NODE.fullmatch(line)
            if node:
                host = node[1]
                hosts_in_map[host] = (int(node[2]), number, set())
            rank = RANK.fullmatch(line)
            if rank:
                jobs.add(rank[1])
                ident = int(rank[2])
                if host is not None:
                    ranks[ident][host].append(number)
                    hosts_in_map[host][2].add(ident)
                    core = socket_core(rank[3])
                    if core is not None:
                        cores[ident][(host, *core)].append(number)

        binding = BIND.fullmatch(line)
        if binding:
            name, ident = binding[1], int(binding[2])
            ranks[ident][name].append(number)
            report_lines[ident].append(number)
            core = socket_core(binding[3] or "")
            if core is not None:
                cores[ident][(name, *core)].append(number)
            if binding[3] is None:
                unbound[ident].append(number)

    if len(jobs) > 1:
        issues.append(Issue(CONTRADICTION, "multiplos_jobs_mpi", f"Jobs encontrados {sorted(jobs)}.", (block.ref,)))
    if map_count != map_closed:
        issues.append(Issue(WARNING, "mapa_sem_fecho", f"{map_count} aberturas de mapa e {map_closed} fechos.", (block.ref,)))

    rows = []
    for ident, observed in sorted(ranks.items()):
        binding = cores.get(ident, {})
        not_bound = unbound.get(ident, [])
        if len(observed) > 1:
            refs = tuple(block.source.ref(lines[0]) for lines in observed.values())
            issues.append(Issue(CONTRADICTION, "rank_em_hosts_diferentes", f"Rank {ident}: {list(observed)}.", refs))
        if len(binding) > 1 or (not_bound and binding):
            refs = tuple(block.source.ref(lines[0]) for lines in binding.values())
            refs += tuple(block.source.ref(n) for n in not_bound[:1])
            issues.append(Issue(CONTRADICTION, "binding_rank_divergente", f"Rank {ident}: {list(binding)}.", refs))
        host = next(iter(observed)) if len(observed) == 1 else None
        _, socket, core = next(iter(binding)) if len(binding) == 1 and not not_bound else (None, None, None)
        lines = sorted(number for obs in observed.values() for number in obs)
        rows.append({
            "rank": ident, "host": host, "socket": socket, "core": core,
            "sem_binding_explicito": bool(not_bound), "hosts_observados": sorted(observed),
            "linha_rank": lines[0], "n_registros_rank": len(lines),
            "linha_binding": next((numbers[0] for numbers in binding.values()), None),
            "linhas_report_bindings": report_lines.get(ident, []),
        })
    return MapEvidence(rows, jobs, slots, map_count, map_closed, len(layouts), job_lines, issues)
