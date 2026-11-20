"""Serialização reproduzível e publicação que protege arquivos preexistentes."""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
import fcntl
from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
from typing import Any, Iterable

MANAGED_MANIFEST = Path("manifestos/artefatos.json")
OWNER = "auditoria-npb:v1"


def hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Tipo sem representação JSON na auditoria: {type(value)}")


def json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, default=json_default, allow_nan=False,
                      separators=(",", ":"))


def write_json(path: Path, data: Any) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, default=json_default, allow_nan=False)
    path.write_text(content + "\n", encoding="utf-8")


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "sim" if value else "nao"
    if isinstance(value, (list, tuple, dict)):
        return json_text(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def write_csv(path: Path, rows: Iterable[dict], fields: Iterable[str] = ()) -> None:
    records = list(rows)
    columns = list(dict.fromkeys([*fields, *(key for row in records for key in row)]))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in records:
            writer.writerow({key: csv_value(value) for key, value in row.items()})


def code_manifest(project: Path) -> dict[str, Any]:
    """Identifica a versão por conteúdo, inclusive em cópias sem metadados Git."""
    listing = [
        project / "scripts/auditar_npb.py",
        *sorted((project / "scripts/npb_auditoria").glob("*.py")),
        *sorted((project / "scripts/npb_auditoria").glob("*.md")),
        *sorted((project / "tests").glob("test_*.py")),
        project / "requirements-auditoria.txt",
    ]
    files = {file.relative_to(project).as_posix(): hash_file(file) for file in listing if file.is_file()}
    return {
        "versao_formato": 1,
        "codigo_sha256": sha256(json_text(files).encode()).hexdigest(),
        "arquivos_codigo_sha256": files,
        "python": platform.python_version(),
        "dependencias": {name: version(name) for name in (
            "numpy", "scipy", "matplotlib", "contourpy", "cycler", "fonttools", "kiwisolver",
            "packaging", "pillow", "pyparsing", "python-dateutil", "six",
        )},
    }


def managed_paths(out: Path, relative: Path) -> Path:
    """Rejeita redirecionamentos de escrita por links na árvore de saída."""
    target = out
    for part in relative.parts:
        target /= part
        if target.is_symlink():
            raise ValueError(f"Link simbólico em caminho gerenciado: {target}")
    return target


def publish(staged: Path, out: Path) -> int:
    """Confere a propriedade de todos os destinos antes de substituir arquivos."""
    out.mkdir(parents=True, exist_ok=True)
    files = {
        file.relative_to(staged).as_posix(): hash_file(file)
        for file in sorted(staged.rglob("*")) if file.is_file()
    }
    if MANAGED_MANIFEST.as_posix() in files:
        raise ValueError("A lista de artefatos deve ser criada durante a publicação.")
    descriptor = os.open(out, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        manifest = managed_paths(out, MANAGED_MANIFEST)
        previous = {}
        if manifest.exists():
            try:
                loaded = json.loads(manifest.read_text(encoding="utf-8"))
                if (loaded.get("proprietario") != OWNER or not isinstance(loaded.get("sha256"), dict)
                        or not isinstance(loaded.get("preexistentes_preservados", []), list)):
                    raise ValueError("metadados de propriedade inválidos")
                preserved = set(loaded.get("preexistentes_preservados", []))
                previous = {name: checksum for name, checksum in loaded["sha256"].items() if name not in preserved}
            except (OSError, ValueError, AttributeError, TypeError) as error:
                raise ValueError(f"Manifesto de artefatos preexistente sem propriedade verificável: {manifest}") from error
        updates = []
        identical_foreign = []
        for name, checksum in files.items():
            destination = managed_paths(out, Path(name))
            if destination.exists():
                if not destination.is_file():
                    raise ValueError(f"Destino ocupado por item que não é arquivo: {destination}")
                existing = hash_file(destination)
                if existing == checksum:
                    if previous.get(name) != existing:
                        identical_foreign.append(name)
                    continue
                if existing != previous.get(name):
                    raise ValueError(f"Arquivo preexistente ou editado fora da auditoria: {destination}. Use outro --out.")
            updates.append((staged / name, destination))
        for _, destination in updates:
            parent = destination.parent
            while parent != out:
                if parent.exists() and not parent.is_dir():
                    raise ValueError(f"Diretório de destino ocupado: {parent}")
                parent = parent.parent
        staged_manifest = staged / MANAGED_MANIFEST
        staged_manifest.parent.mkdir(parents=True, exist_ok=True)
        if manifest.parent.exists() and not manifest.parent.is_dir():
            raise ValueError(f"Diretório de manifesto ocupado: {manifest.parent}")
        write_json(staged_manifest, {"proprietario": OWNER, "sha256": files, "preexistentes_preservados": identical_foreign})
        # O manifesto é publicado ao final. Uma execução igual pode retomar um lote parcial.
        for source, destination in updates:
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        if not manifest.is_file() or hash_file(manifest) != hash_file(staged_manifest):
            os.replace(staged_manifest, manifest)
        return len(updates)
    finally:
        os.close(descriptor)
