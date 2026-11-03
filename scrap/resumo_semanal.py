"""Job semanal (ponto 9 do Wagner): cofre (append-only, ~57 mil contemplações) -> tabela fato dos ~70 grupos ativos.
Calcula c1..c6, M1..M6, p1..p6, qtd_fixo_contemplado_mes, n_ofertantes_fixo_medio, mediana_lance_livre
(só dado comercial), data_coleta (validade) e repassa proxima_assembleia do catálogo; grava um snapshot JSON local
(e, com --linhas-fato, as linhas da fato_cotas com as colunas tipadas da 0005 + extra);
troca o ponteiro ATUAL.json de forma atômica (os.replace). O solver só lê a tabela fato.

uso: python scrap/resumo_semanal.py --cofre cofre.csv --ativos ativos.csv --catalogo catalogo.json --saida dir
catalogo.json: lista de cotas (campos de Cota, sem estatísticas; dinheiro/frações como string)."""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solver"))  # contrato, modelos, niveis
import cofre  # noqa: E402
from contrato import snapshot_de_dict, snapshot_para_dict  # noqa: E402
from fato_colunas import COLUNAS_I1, colunas_de_extra  # noqa: E402
from modelos import Parametros  # noqa: E402
from niveis import niveis_livres  # noqa: E402

# Revisão N8: a data de coleta é a data LOCAL da operação (Bahia), não a data UTC do servidor. O job roda de madrugada
# e, entre 21h e 24h locais, a data UTC já é o dia seguinte. Sem base tz (imagem slim/Windows), cai em UTC-3 fixo
# (a Bahia não tem horário de verão desde 2012).
try:
    from zoneinfo import ZoneInfo
    TZ_LOCAL = ZoneInfo("America/Bahia")
except Exception:  # noqa: BLE001  (ZoneInfoNotFoundError, ImportError, base tz ausente)
    TZ_LOCAL = timezone(timedelta(hours=-3), "UTC-03")


def gerar_snapshot(rows, ativos, catalogo, agora=None):
    """rows: contemplações; ativos: dict (cofre.ler_ativos); catalogo: lista de dicts de cota. Devolve dict da tabela fato."""
    agora = agora or datetime.now(TZ_LOCAL)
    if agora.tzinfo is None:                               # datetime ingênuo = hora local da operação
        agora = agora.replace(tzinfo=TZ_LOCAL)
    hoje_local = agora.astimezone(TZ_LOCAL).date()
    agora_utc = agora.astimezone(timezone.utc)
    por_grupo = cofre.assembleias([r for r in rows if str(r["grupo"]).strip().zfill(6) in ativos])
    cotas = []
    for item in catalogo:
        g = str(item["grupo"]).strip().zfill(6)
        if g not in ativos:
            continue
        st = cofre.stats_grupo(por_grupo.get(g, []))
        cotas.append({**item, "grupo": g, "c": [None if x is None else str(x) for x in st["c"]],
                      "qtd_fixo_contemplado_mes": None if st["qtd_fixo_contemplado_mes"] is None
                      else str(st["qtd_fixo_contemplado_mes"]),
                      "n_ofertantes_fixo_medio": None if st["n_ofertantes_fixo_medio"] is None
                      else str(st["n_ofertantes_fixo_medio"]),
                      "mediana_lance_livre": None if st["mediana_lance_livre"] is None else str(st["mediana_lance_livre"]),
                      # data_coleta: do catálogo se vier (data da coleta no Clique Vendas); senão a data da execução do job
                      "data_coleta": item.get("data_coleta") or hoje_local.isoformat()})
    snap = snapshot_de_dict({"snapshot_id": "snap-" + agora_utc.strftime("%Y%m%dT%H%M%SZ"),
                             "atualizado_em": agora_utc.isoformat(timespec="seconds"), "cotas": cotas})
    d = snapshot_para_dict(snap)
    P = Parametros()
    for r, c in zip(d["cotas"], snap.cotas):             # colunas derivadas (informativas; o solver recalcula)
        _, _, W, niv = niveis_livres(c.c, P)
        r["M"] = [str(max(c.c[:w])) if w <= W else None for w in range(1, 7)]
        r["p"] = [str(Fraction(n.p)) for n in niv]
    return d


# Colunas da `fato_cotas` (0002 + 0005). O que não é coluna vai para `extra` (jsonb).
COLUNAS_FATO_BASE = ("cota_id", "grupo", "serie", "tipo_bem", "plano_pct", "credito", "taxa_pct", "parcela",
                     "pct_embutido_max", "tem_lance_fixo", "c", "qtd_fixo_contemplado_mes", "mediana_lance_livre",
                     "data_coleta", "proxima_assembleia")


def linhas_fato_cotas(d):
    """I1: snapshot (dict de `gerar_snapshot`) -> linhas da `fato_cotas` com as 8 colunas tipadas (0005).
    As colunas tipadas saem da MESMA regra da migration (`fato_colunas.colunas_de_extra`); os valores originais
    continuam em `extra` (compatibilidade com leitores antigos). `proxima_assembleia` em lista: coluna = 1ª data."""
    linhas = []
    for r in d["cotas"]:
        base = {k: r.get(k) for k in COLUNAS_FATO_BASE}
        if isinstance(base["proxima_assembleia"], (list, tuple)):
            base["proxima_assembleia"] = base["proxima_assembleia"][0] if base["proxima_assembleia"] else None
        extra = {k: v for k, v in r.items() if k not in COLUNAS_FATO_BASE}
        tip = {k: (str(v) if v is not None and k in ("lance_fixo_pct", "n_ofertantes_fixo_medio", "lance_ref_irmaos")
                   else v) for k, v in colunas_de_extra(extra).items()}
        linhas.append({"snapshot_id": d["snapshot_id"], **base, **{k: tip[k] for k in COLUNAS_I1}, "extra": extra})
    return linhas


def gravar(d, pasta):
    os.makedirs(os.path.join(pasta, "snapshots"), exist_ok=True)
    alvo = os.path.join(pasta, "snapshots", d["snapshot_id"] + ".json")
    with open(alvo + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(alvo + ".tmp", alvo)
    ptr = os.path.join(pasta, "ATUAL.json")                # troca atômica do ponteiro
    with open(ptr + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"snapshot_id": d["snapshot_id"]}, f)
    os.replace(ptr + ".tmp", ptr)
    return alvo


def main(argv=None):
    ap = argparse.ArgumentParser()
    for a in ("cofre", "ativos", "catalogo", "saida"):
        ap.add_argument("--" + a, required=True)
    ap.add_argument("--linhas-fato", help="opcional: grava as linhas da fato_cotas (colunas tipadas I1 + extra) em JSON")
    a = ap.parse_args(argv)
    with open(a.catalogo, encoding="utf-8") as f:
        catalogo = json.load(f)
    d = gerar_snapshot(cofre.ler_tabela(a.cofre), cofre.ler_ativos(a.ativos), catalogo)
    print(gravar(d, a.saida), len(d["cotas"]), "cotas")
    if a.linhas_fato:
        with open(a.linhas_fato + ".tmp", "w", encoding="utf-8") as f:
            json.dump(linhas_fato_cotas(d), f, ensure_ascii=False)
        os.replace(a.linhas_fato + ".tmp", a.linhas_fato)


if __name__ == "__main__":
    main()
