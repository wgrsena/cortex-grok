#!/usr/bin/env python3
"""Troca o número do WhatsApp em todos os links wa.me pelo valor de config/site.json.

Fluxo: editar "whatsapp_oficial" em config/site.json (só dígitos, com 55 + DDD) e rodar
    python3 tools/set_whatsapp.py && python3 tools/check.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
num = cfg["whatsapp_oficial"]
assert re.fullmatch(r"55\d{10,11}|55X+", num), "whatsapp_oficial deve ser 55 + DDD + número, só dígitos"
for p in ROOT.rglob("*.html"):
    if ".git" in p.parts:
        continue
    t = p.read_text(encoding="utf-8")
    novo = re.sub(r"https://wa\.me/[0-9X]+", f"https://wa.me/{num}", t)
    if novo != t:
        p.write_text(novo, encoding="utf-8")
        print("atualizado:", p.relative_to(ROOT))
