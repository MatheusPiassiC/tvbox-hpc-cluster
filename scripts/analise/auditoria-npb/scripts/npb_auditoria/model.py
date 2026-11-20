"""Modelo de proveniência e referência experimental para NPB-MPI classe A."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from functools import cached_property
from hashlib import sha256
from pathlib import Path
from typing import Any

LEVELS = dict.fromkeys(("EP", "IS", "CG", "MG", "FT", "LU"), (1, 2, 4, 8, 16, 32))
LEVELS.update(dict.fromkeys(("BT", "SP"), (1, 4, 9, 16, 25)))
REPETITIONS = 10
CLASS = "A"
NPB_VERSION = "3.4.4"
HOSTS = ("server", *(f"node{i}" for i in range(1, 8)))
CORES_PER_HOST = 4
# O resumo de EP conta os números, dois por par, e imprime zero iterações.
WORKLOADS = {
    "EP": ("536870912", 0), "IS": ("8388608", 10), "CG": ("14000", 15),
    "MG": ("256x256x256", 4), "FT": ("256x256x128", 6),
    "LU": ("64x64x64", 250), "BT": ("64x64x64", 200), "SP": ("64x64x64", 400),
}
VALID, INVALID, UNCERTAIN, CONFLICT = (
    "valida_confirmada", "invalida_confirmada", "inconclusiva", "conflitante",
)
FAILURE, MISSING, CONTRADICTION, WARNING = ("falha", "lacuna", "conflito", "alerta")


@dataclass(frozen=True)
class Source:
    """Cópia em memória dos bytes de entrada, com caminho para o original."""

    path: Path
    name: str
    role: str
    data: bytes

    @cached_property
    def sha(self) -> str:
        return sha256(self.data).hexdigest()

    @cached_property
    def text(self) -> str:
        return self.data.decode("utf-8-sig")

    @cached_property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    def ref(self, first: int | None = None, last: int | None = None) -> str:
        if first is None:
            return self.name
        suffix = f"-{last}" if last is not None and last > first else ""
        return f"{self.name}:{first}{suffix}"

    def inventory(self) -> dict[str, Any]:
        try:
            self.text
            encoding = "UTF-8 com BOM" if self.data.startswith(b"\xef\xbb\xbf") else "UTF-8"
        except UnicodeDecodeError:
            encoding = "UTF-8 inválido"
        crlf = self.data.count(b"\r\n")
        lf = self.data.count(b"\n") - crlf
        cr = self.data.count(b"\r") - crlf
        return {
            "arquivo": self.name, "tipo": self.role, "bytes": len(self.data),
            "linhas": len(self.data.splitlines()), "sha256": self.sha,
            "codificacao": encoding, "linhas_lf": lf, "linhas_crlf": crlf, "linhas_cr": cr,
        }


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    detail: str
    sources: tuple[str, ...]

    def row(self, campaign: str = "", attempt: str = "") -> dict[str, Any]:
        return {
            "campanha": campaign, "id_auditoria": attempt, "nivel": self.level,
            "codigo": self.code, "detalhe": self.detail, "fontes": list(self.sources),
        }


@dataclass
class CsvRecord:
    source: Source
    first: int
    last: int
    raw: dict[str, str | None]
    values: dict[str, Any]
    extra: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def ref(self) -> str:
        return self.source.ref(self.first, self.last)


@dataclass
class Block:
    source: Source
    first: int
    last: int
    exec_id: str | None
    header: dict[str, Any]
    footer: dict[str, Any]
    footer_line: int | None
    command: str | None
    command_line: int | None
    precheck: dict[str, Any]
    precheck_line: int | None
    output: list[tuple[int, str]]
    output_sha: str | None
    summary: dict[str, Any]
    summary_lines: dict[str, int]
    additional: dict[str, Any]
    issues: list[Issue]

    @property
    def ref(self) -> str:
        return self.source.ref(self.first, self.last)


@dataclass
class Environment:
    source: Source
    values: dict[str, Any]
    lines: dict[str, int]
    stable_lines: list[str]
    hosts: list[dict[str, Any]]
    issues: list[Issue]

    def ref(self, field: str) -> str:
        return self.source.ref(self.lines.get(field))


@dataclass
class Campaign:
    key: str
    experiment: int
    benchmark: str
    problem_class: str
    sources: dict[str, Source] = field(default_factory=dict)
    csv: list[CsvRecord] = field(default_factory=list)
    plan: list[CsvRecord] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)
    environment: Environment | None = None
    output_header: dict[str, Any] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)


@dataclass
class Attempt:
    """Grupo de registros para uma identidade física ou um candidato sem chave."""

    campaign: Campaign
    key: str
    identity_method: str
    csvs: list[CsvRecord]
    blocks: list[Block]
    issues: list[Issue] = field(default_factory=list)
    plan_rows: list[CsvRecord] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.campaign.key}/{self.key}"

    @property
    def csv(self) -> CsvRecord | None:
        if self.csvs and all(record.raw == self.csvs[0].raw for record in self.csvs):
            return self.csvs[0]
        return None

    @property
    def log(self) -> Block | None:
        return self.blocks[0] if len(self.blocks) == 1 else None

    @property
    def refs(self) -> tuple[str, ...]:
        return tuple(row.ref for row in [*self.csvs, *self.blocks, *self.plan_rows])

    def add(self, level: str, code: str, detail: str, *sources: str) -> None:
        self.issues.append(Issue(level, code, detail, sources or self.refs))

    @property
    def state(self) -> str:
        levels = {issue.level for issue in self.issues}
        if CONTRADICTION in levels:
            return CONFLICT
        if FAILURE in levels:
            return INVALID
        if MISSING in levels:
            return UNCERTAIN
        return VALID


def first_known(*values: Any) -> Any:
    """Preserva zero e False entre valores ausentes."""
    return next((value for value in values if value is not None), None)


def rounded_agreement(left: Decimal, right: Decimal) -> bool:
    """Testa sobreposição interior das faixas implícitas de arredondamento."""
    if left == right:
        return True
    left_exp = left.as_tuple().exponent
    right_exp = right.as_tuple().exponent
    if left_exp == right_exp:
        return False
    return abs(left - right) < (Decimal(10) ** left_exp + Decimal(10) ** right_exp) / 2


def equal_observed(*values: Any) -> bool:
    """Só avalia contradição entre valores presentes."""
    known = [value for value in values if value is not None]
    return not known or all(value == known[0] for value in known)


def exec_sequence(exec_id: str | None, experiment: int) -> int | None:
    if not exec_id:
        return None
    prefix, _, suffix = exec_id.partition("-")
    if prefix == str(experiment) and suffix.isascii() and suffix.isdecimal():
        return int(suffix) or None
    return None


def seconds_between(start: datetime | None, end: datetime | None) -> Decimal | None:
    if start is None or end is None:
        return None
    return Decimal(str((end - start).total_seconds()))
