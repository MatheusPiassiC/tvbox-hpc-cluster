"""Confere os SHA-256 dos arquivos listados nos manifestos da auditoria."""

from hashlib import sha256
import json
from pathlib import Path
import sys


RAIZ = Path(__file__).resolve().parents[2]
AUDITORIA = RAIZ / "results/processed/auditoria"
MANIFESTOS = AUDITORIA / "manifestos"


def main() -> int:
    try:
        entrada = json.loads((MANIFESTOS / "dados_entrada.json").read_bytes())
        artefatos = json.loads((MANIFESTOS / "artefatos.json").read_bytes())
        reproducao = json.loads((MANIFESTOS / "reproducibilidade.json").read_bytes())
        grupos = (
            ("dados brutos", RAIZ / "results", {item["arquivo"]: item["sha256"] for item in entrada["arquivos"]}),
            ("artefatos da auditoria", AUDITORIA, artefatos["sha256"]),
            ("código e dependências", RAIZ / "scripts/analise/auditoria-npb", reproducao["arquivos_codigo_sha256"]),
        )
        if any(not isinstance(arquivos, dict) or not arquivos for _, _, arquivos in grupos):
            raise ValueError("lista de arquivos vazia ou inválida")
    except (OSError, ValueError, KeyError, TypeError) as erro:
        print(f"Erro ao ler os manifestos: {erro}", file=sys.stderr)
        return 1

    falhas = 0
    for rotulo, base, arquivos in grupos:
        conferidos = 0
        for relativo, esperado in arquivos.items():
            caminho = base / relativo
            try:
                if not caminho.resolve().is_relative_to(base):
                    print(f"Caminho fora da pasta do conjunto {rotulo}: {relativo}", file=sys.stderr)
                    continue
                atual = sha256(caminho.read_bytes()).hexdigest()
            except OSError:
                print(f"Arquivo ausente ou inacessível: {caminho.relative_to(RAIZ)}", file=sys.stderr)
                continue
            if atual != esperado:
                print(f"SHA-256 divergente: {caminho.relative_to(RAIZ)}", file=sys.stderr)
                continue
            conferidos += 1
        falhas += len(arquivos) - conferidos
        print(f"{rotulo}: {conferidos}/{len(arquivos)} arquivos conferidos")
    return int(falhas != 0)


if __name__ == "__main__":
    raise SystemExit(main())
