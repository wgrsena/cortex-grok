#!/usr/bin/env python3
"""Injetor de dados dos cards de oportunidade do Midas (v0.8.0, stdlib pura).

Reaproveita o gerador da rota /oportunidades (tools/oportunidades/gerar.py, sem alteração): roda a mesma rodada
(coleta Drive 25/10 -> entrada.py -> Arquimedes) e renderiza o MESMO card da página /oportunidades/<faixa>/
(gerar.card), lendo dele os campos públicos (data-campo). Por isso os números são idênticos aos da página.

Regra de dado: só número com fonte. Entrada e lance não têm base verificada -> texto da rota ("dado não disponível").
A mediana de lance e o embutido ficam só no ranking e não saem daqui.

Uso: python3 midas/cards/injetar.py [--hoje AAAA-MM-DD] [--faixas 50000,100000,200000] -> midas/cards/dados-cards.json
"""
import argparse
import html
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "oportunidades"))
import gerar  # noqa: E402  (rota /oportunidades, reaproveitada)

VERSAO = "0.8.0"
SAIDA = Path(__file__).resolve().parent / "dados-cards.json"


def campos_do_card(card_html: str) -> dict:
    """{campo: {"texto", "fonte"|None, "lacuna"|None}} a partir do HTML do card da rota."""
    out = {}
    for m in re.finditer(r"<dd\b([^>]*)>(.*?)</dd>", card_html, re.S):
        attrs, corpo = m.group(1), m.group(2)
        c = re.search(r'data-campo="(\w+)"', attrs)
        if not c:
            continue
        fonte = re.search(r'data-fonte="([\w-]+)"', attrs)
        lac = re.search(r'data-lacuna="([\w-]+)"', attrs)
        out[c.group(1)] = {"texto": html.unescape(re.sub(r"<[^>]+>", "", corpo)).strip(),
                           "fonte": fonte.group(1) if fonte else None, "lacuna": lac.group(1) if lac else None}
    return out


def injetar(hoje: date, faixas) -> dict:
    res, por_item = gerar.rodar(hoje)
    fx = json.loads((ROOT / gerar.CFG["coleta_dir"] / "fontes.json").read_text(encoding="utf-8"))
    base = {"versao": VERSAO, "hoje": hoje.isoformat(), "data_coleta": res["data_coleta"],
            "idade_coleta_dias": res["idade_coleta_dias"], "max_dias_coleta": gerar.CFG["max_dias_coleta"],
            "fr": gerar.CFG["fr_padrao"], "lacuna_texto": gerar.GAP,
            "fontes": {"fonte-portal": f"Portal Clique Vendas (Disal), coleta {res['data_coleta']}, Drive "
                                      f"{fx['arquivos']['grupos_a_venda.csv']['drive_id']}",
                       "fonte-calendario": f"WebDisal, calendário de assembleias, coleta {res['data_coleta']}, Drive "
                                           f"{fx['arquivos']['calendario.csv']['drive_id']}",
                       "fonte-motor": "Arquimedes (vendor/arquimedes), posição 1 do ordenamento da faixa"},
            "cards": []}
    if not res["fresca"]:
        raise SystemExit(f"coleta de {res['data_coleta']} tem {res['idade_coleta_dias']} dias (> {gerar.CFG['max_dias_coleta']}): "
                         "nenhum card é gerado com dado velho")
    for f in faixas:
        ops = res["faixas"][f]["ops"]
        if not ops:
            base["cards"].append({"faixa": f, "combinacao": None, "vazio": "o motor não achou nada hoje"})
            continue
        o = ops[0]  # mesmo card F<faixa>-1 da página /oportunidades/<faixa>/
        c = campos_do_card(gerar.card(o, 1, f, por_item, None, gerar.imagens_faixa(f), res))
        for k in ("credito", "parcela", "assembleia"):
            assert c[k]["fonte"] or c[k]["lacuna"], f"campo {k} sem fonte nem lacuna"
        base["cards"].append({
            "faixa": f, "combinacao": f"F{f // 1000}-1", "n_cartas": o.n_cartas, "pagina": gerar.url_pagina(f),
            "credito": c["credito"], "parcela": c["parcela"], "assembleia": c["assembleia"],
            "entrada": c["entrada"],
            "lance": {"texto": gerar.GAP, "fonte": None, "lacuna": "lance"},  # sem base verificada (mesma regra da rota)
        })
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoje", default=datetime.now(gerar.BAHIA).date().isoformat())
    ap.add_argument("--faixas", default="50000,100000,200000")
    a = ap.parse_args()
    d = injetar(date.fromisoformat(a.hoje), [int(x) for x in a.faixas.split(",")])
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for c in d["cards"]:
        print(c["faixa"], c.get("combinacao"), c["credito"]["texto"], c["parcela"]["texto"], c["assembleia"]["texto"],
              "| entrada:", c["entrada"]["texto"], "| lance:", c["lance"]["texto"])
    print("coleta", d["data_coleta"], f"({d['idade_coleta_dias']} dias) ->", SAIDA.relative_to(ROOT))


if __name__ == "__main__":
    main()
