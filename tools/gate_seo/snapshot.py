#!/usr/bin/env python3
"""Grava o sidecar .meta.json de um snapshot do arquivo canônico (exportado do Drive como Markdown).

Uso: python3 tools/gate_seo/snapshot.py docs/seo-canonico/<arquivo>.md --drive-id ID --nome NOME \
        --pasta-id PASTA --pasta-nome NOME --modified 2026-11-02T15:18:40.588Z
O export em si é feito pelo conector do Drive (leitura). Este script nunca escreve no Drive.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canonico import parse  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--drive-id", required=True)
    ap.add_argument("--nome", required=True)
    ap.add_argument("--pasta-id", required=True)
    ap.add_argument("--pasta-nome", required=True)
    ap.add_argument("--modified", required=True, help="modifiedTime do Drive (UTC, ISO 8601)")
    a = ap.parse_args(argv)
    md = Path(a.md)
    dados = md.read_bytes()
    c = parse(dados.decode("utf-8"))
    meta = {
        "arquivo": md.name,
        "sha256": hashlib.sha256(dados).hexdigest(),
        "drive_id": a.drive_id,
        "drive_link": f"https://docs.google.com/document/d/{a.drive_id}/edit",
        "nome_drive": a.nome,
        "pasta_drive_id": a.pasta_id,
        "pasta_drive_nome": a.pasta_nome,
        "drive_modified_utc": a.modified,
        "versao_declarada": c.versao,
        "requisitos_lidos": len(c.requisitos),
        "exportado_em_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out = md.with_suffix(".meta.json")
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
