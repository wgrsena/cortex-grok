"""Backtest ROLANTE da sequência (t61u, Wagner 01/11/2026). Cruza o resolvedor (solver/niveis.niveis_livres, o mesmo
código do runtime) contra uma CÓPIA somente-leitura do cofre (contemplações append-only).

Para cada data de referência D (corte mensal, dia 1 de cada mês, ou --datas):
  1. só entram grupos que EXISTIAM em D: com pelo menos uma assembleia ANTES de D (e ativos em D, se --ativos);
  2. a entrada do resolvedor usa SÓ assembleias < D (c1..c6 = menor lance livre contemplado das 6 últimas);
  3. o resolvedor devolve a sequência W (2..6) e o lance M_W que cobriu as W últimas assembleias seguidas; p = W/6;
  4. o desfecho é a 1ª assembleia do grupo em [D, próximo corte): ACERTO se M_W >= menor lance livre contemplado.
     Decisão Wagner 01/11: EMPATE = CONTEMPLAÇÃO (comparação inclusiva, em Decimal exato, sem float).
Mediana dos lances livres da janela: só desempate do ranking de grupos (nunca entra em p nem no acerto).

O cofre é aberto só para leitura (arquivo em 'rb'/'r', sqlite com ?mode=ro) e nunca é escrito.
uso: python scrap/backtest_rolante.py --cofre /caminho/copia.csv|.xlsx|.sqlite [--tabela T] [--ativos a.csv]
       [--saida DIR] [--datas 2025-01-01,2025-02-01] [--sha256 HEX]   (ou env COFRE_PATH / COFRE_SHA256)
"""
import argparse
import csv
import hashlib
import io
import json
import os
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from statistics import median

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solver"))
import cofre  # noqa: E402
from modelos import Parametros  # noqa: E402
from niveis import niveis_livres  # noqa: E402

W_MIN, W_MAX = 2, 6
N_MIN_RANKING = 12      # top/bottom do resumo só com grupos com >= 12 avaliações (a tabela completa lista todos)
PARAMS = Parametros(modo_probabilidade="sequencia_W_sobre_6")
CEM = Decimal(100)


# ----------------------------------------------------------------------------------------------- leitura (só leitura)
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def abrir_cofre_ro(path, tabela="cofre"):
    """Linhas do cofre como dicts, abrindo a fonte SÓ para leitura. Nenhuma escrita é possível pelo handle."""
    p = str(path)
    if p.lower().endswith((".sqlite", ".db", ".sqlite3")):
        con = sqlite3.connect(f"file:{os.path.abspath(p)}?mode=ro", uri=True)
        try:
            con.row_factory = sqlite3.Row
            if not tabela.replace("_", "").isalnum():
                raise ValueError(f"nome de tabela inválido: {tabela!r}")
            return [dict(r) for r in con.execute(f'SELECT * FROM "{tabela}"')]
        finally:
            con.close()
    if p.lower().endswith(".xlsx"):
        with open(p, "rb") as f:
            return cofre.ler_xlsx(io.BytesIO(f.read()))
    with open(p, "r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def conexao_ro(path):
    """Conexão sqlite somente-leitura (para quem quiser consultar a cópia direto). Qualquer escrita levanta erro."""
    return sqlite3.connect(f"file:{os.path.abspath(str(path))}?mode=ro", uri=True)


def _pct_para_fracao(v):
    """WebDisal: lance_percentual SEMPRE em percentual ('7,4328' = 7,4328%). Exato em Decimal: 7,4328 -> 0,074328."""
    v = str(v).strip().replace(".", "").replace(",", ".") if "," in str(v) else str(v).strip()
    return Decimal(v) / CEM


def normalizar(rows):
    """[(grupo, data, tipo, lance_fracao|None)]. Aceita o esquema real do WebDisal (tipo_contemplacao,
    lance_percentual em %) e o esquema suposto de scrap/cofre.py (tipo, lance_pct, fração ou %)."""
    out = []
    for r in rows:
        g = str(r["grupo"]).strip().zfill(6)
        d = cofre.parse_data(r["data_assembleia"])
        if "tipo_contemplacao" in r:
            t = str(r["tipo_contemplacao"]).strip().upper()
            tipo = {"LANCE LIVRE": "livre", "LANCE FIXO": "fixo", "SORTEIO": "sorteio"}.get(t, t.lower())
            bruto = str(r.get("lance_percentual") or "").strip()
            x = _pct_para_fracao(bruto) if (tipo == "livre" and bruto) else None
        else:
            tipo = str(r["tipo"]).strip().lower()
            bruto = str(r.get("lance_pct") or "").strip()
            x = cofre.parse_frac(bruto) if (tipo == "livre" and bruto) else None
        out.append((g, d, tipo, x))
    return out


def assembleias(norm):
    """{grupo: [(data, menor_livre|None, (livres...))]} em ordem cronológica."""
    ag = defaultdict(lambda: defaultdict(list))
    for g, d, tipo, x in norm:
        lst = ag[g][d]
        if tipo == "livre" and x is not None:
            lst.append(x)
    return {g: [(d, (min(ds[d]) if ds[d] else None), tuple(sorted(ds[d]))) for d in sorted(ds)]
            for g, ds in sorted(ag.items())}


# ---------------------------------------------------------------------------------------- filtro e definição única
def grupos_existentes(asm, D, ativos=None):
    """Grupos que existiam em D: têm assembleia anterior a D (grupo criado depois de D fica fora) e, se houver
    tabela de ativos, estão ativos em D."""
    return [g for g, a in asm.items() if a and a[0][0] < D and cofre.ativo_em(ativos, g, D)]


def cobre(lance, menor_contemplado):
    """Decisão Wagner 01/11: EMPATE = CONTEMPLAÇÃO (quem ofereceu primeiro ganha). Comparação inclusiva em Decimal
    exato (sem float), coerente com o '<=' do I2. None (assembleia sem lance livre contemplado) não é julgável."""
    if menor_contemplado is None:
        return None
    return Decimal(lance) >= Decimal(menor_contemplado)


def prever_sequencia(c):
    """DEFINIÇÃO ÚNICA (troque aqui). Usa o resolvedor (niveis_livres, modo sequencia_W_sobre_6):
    c = (c1..c6), c1 = assembleia mais recente antes de D. W = nº de assembleias SEGUIDAS, a partir da mais recente,
    com lance livre contemplado; M_W = max(c1..cW) é o lance que teria contemplado nas W; p = W/6.
    Previsão = o nível de MAIOR w do resolvedor, se w >= 2 (sequência de 2 a 6). None se não houver."""
    _, _, _, niveis = niveis_livres(c, PARAMS)
    cand = [n for n in niveis if W_MIN <= n.w <= W_MAX]
    if not cand:
        return None
    n = max(cand, key=lambda n: n.w)
    return {"w": n.w, "lance": n.lance_pct, "p": n.p}


# ------------------------------------------------------------------------------------------------------ backtest
def cortes_mensais(asm):
    datas = sorted({d for a in asm.values() for d, *_ in a})
    if not datas:
        return []
    out, y, m = [], datas[0].year, datas[0].month
    while (y, m) <= (datas[-1].year, datas[-1].month):
        out.append(date(y, m, 1))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out[1:]          # o 1º corte não tem passado


def _fmt(x):
    return None if x is None else format(Decimal(x).normalize(), "f")


def backtest(norm, ativos=None, datas=None):
    asm = assembleias(norm)
    datas = sorted(datas) if datas else cortes_mensais(asm)
    evid, cont = [], {"grupo_data_existentes": 0, "sem_previsao": 0, "sem_assembleia_na_janela": 0,
                      "sem_livre_contemplado": 0}
    for i, D in enumerate(datas):
        prox_corte = datas[i + 1] if i + 1 < len(datas) else date.max
        for g in grupos_existentes(asm, D, ativos):
            a = asm[g]
            passado = [x for x in a if x[0] < D]                       # SEM look-ahead: só < D
            cont["grupo_data_existentes"] += 1
            ult = passado[-6:][::-1]
            c = tuple(x[1] for x in ult)
            prev = prever_sequencia(c)
            if prev is None:
                cont["sem_previsao"] += 1
                continue
            futuro = [x for x in a if D <= x[0] < prox_corte]
            if not futuro:
                cont["sem_assembleia_na_janela"] += 1
                continue
            alvo = futuro[0]
            ok = cobre(prev["lance"], alvo[1])
            if ok is None:
                cont["sem_livre_contemplado"] += 1
                continue
            livres_jan = [y for x in passado[-6:] for y in x[2]]
            seq_futura = 0                                             # evidência extra: quantas seguidas M_W cobriu
            for x in [x for x in a if x[0] >= D][:6]:
                if cobre(prev["lance"], x[1]):
                    seq_futura += 1
                else:
                    break
            evid.append({
                "grupo": g, "data_referencia": D.isoformat(),
                "assembleias_entrada": ";".join(x[0].isoformat() for x in ult[:prev["w"]]),
                "menores_livres_entrada_pct": ";".join(_fmt(x[1] * CEM) for x in ult[:prev["w"]]),
                "w_previsto": prev["w"], "p_previsto": f"{prev['w']}/6",
                "lance_previsto_pct": _fmt(prev["lance"] * CEM),
                "assembleia_alvo": alvo[0].isoformat(), "menor_livre_real_pct": _fmt(alvo[1] * CEM),
                "empate": prev["lance"] == alvo[1], "acerto": bool(ok),
                "seq_futura_coberta": seq_futura, "manteve_w": seq_futura >= prev["w"],
                "mediana_livre_janela_pct": _fmt(median(livres_jan) * CEM) if livres_jan else None})
    return {"evidencias": evid, "contagens": cont, "datas_referencia": [d.isoformat() for d in datas],
            "por_grupo": por_grupo(evid), "por_w": por_w(evid), "geral": _taxa(evid)}


def _taxa(itens):
    n = len(itens)
    h = sum(1 for e in itens if e["acerto"])
    return {"n": n, "acertos": h, "taxa_acerto": round(h / n, 4) if n else None,
            "p_medio": round(sum(e["w_previsto"] for e in itens) / 6 / n, 4) if n else None,
            "empates": sum(1 for e in itens if e["empate"]),
            "taxa_manteve_w": round(sum(1 for e in itens if e["manteve_w"]) / n, 4) if n else None}


def por_grupo(evid):
    by = defaultdict(list)
    for e in evid:
        by[e["grupo"]].append(e)
    out = []
    for g, it in by.items():
        t = _taxa(it)
        meds = [Decimal(e["mediana_livre_janela_pct"]) for e in it if e["mediana_livre_janela_pct"] is not None]
        t.update({"grupo": g, "primeira_data_ref": it[0]["data_referencia"], "ultima_data_ref": it[-1]["data_referencia"],
                  "mediana_desempate_pct": _fmt(median(meds)) if meds else None})
        out.append(t)
    # ranking: taxa (desc), n (desc), mediana só como desempate (menor primeiro), grupo
    return sorted(out, key=lambda t: (-t["taxa_acerto"], -t["n"],
                                      Decimal(t["mediana_desempate_pct"]) if t["mediana_desempate_pct"] else Decimal("1e9"),
                                      t["grupo"]))


def por_w(evid):
    return {w: _taxa([e for e in evid if e["w_previsto"] == w]) for w in range(W_MIN, W_MAX + 1)}


# ------------------------------------------------------------------------------------------------------- saídas
def gravar(res, saida, meta):
    os.makedirs(saida, exist_ok=True)
    for nome, linhas in (("evidencias.csv", res["evidencias"]), ("por_grupo.csv", res["por_grupo"])):
        with open(os.path.join(saida, nome), "w", newline="", encoding="utf-8") as f:
            if linhas:
                w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
                w.writeheader()
                w.writerows(linhas)
    with open(os.path.join(saida, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, **res}, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(saida, "resumo.md"), "w", encoding="utf-8") as f:
        f.write(resumo_md(res, meta))


def resumo_md(res, meta):
    g, pg = res["geral"], res["por_grupo"]
    L = ["# Backtest rolante da sequência (resultado)", "",
         f"- Cofre: `{meta.get('cofre')}` · sha256 `{meta.get('sha256')}` · {meta.get('linhas')} linhas",
         f"- Datas de referência: {len(res['datas_referencia'])} cortes mensais "
         f"({res['datas_referencia'][0] if res['datas_referencia'] else '-'} a "
         f"{res['datas_referencia'][-1] if res['datas_referencia'] else '-'})",
         f"- Regra: acerto = lance previsto M_W >= menor lance livre contemplado na assembleia seguinte. "
         "Decisão Wagner 01/11: empate = contemplação.", "",
         f"**Geral:** {g['acertos']}/{g['n']} = {g['taxa_acerto']} (p médio previsto {g['p_medio']}; "
         f"empates {g['empates']}; manteve W seguidas {g['taxa_manteve_w']}). Grupos avaliados: {len(pg)}.", "",
         "| W previsto | p = W/6 | n | taxa de acerto | manteve W |", "|---|---|---|---|---|"]
    for w, t in res["por_w"].items():
        L.append(f"| {w} | {round(w / 6, 4)} | {t['n']} | {t['taxa_acerto']} | {t['taxa_manteve_w']} |")
    robustos = [t for t in pg if t["n"] >= N_MIN_RANKING]
    for titulo, lst in ((f"Top 5 (n >= {N_MIN_RANKING})", robustos[:5]), (f"Bottom 5 (n >= {N_MIN_RANKING})", robustos[-5:])):
        L += ["", f"**{titulo}:** " + "; ".join(f"{t['grupo']} {t['acertos']}/{t['n']} = {t['taxa_acerto']}" for t in lst)]
    L += ["", f"Contagens: {res['contagens']}", "", "| grupo | n | taxa | p médio | mediana (desempate, %) | 1ª ref | última ref |",
          "|---|---|---|---|---|---|---|"]
    for t in pg:
        L.append(f"| {t['grupo']} | {t['n']} | {t['taxa_acerto']} | {t['p_medio']} | {t['mediana_desempate_pct']} | "
                 f"{t['primeira_data_ref']} | {t['ultima_data_ref']} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cofre", default=os.environ.get("COFRE_PATH"), help="cópia somente-leitura (csv, xlsx, sqlite)")
    ap.add_argument("--tabela", default="cofre", help="tabela, se sqlite")
    ap.add_argument("--sha256", default=os.environ.get("COFRE_SHA256"), help="sha256 esperado da cópia (confere)")
    ap.add_argument("--ativos")
    ap.add_argument("--datas", help="datas de referência ISO separadas por vírgula (padrão: dia 1 de cada mês)")
    ap.add_argument("--saida", default="backtest_saida")
    a = ap.parse_args(argv)
    if not a.cofre:
        ap.error("informe --cofre ou COFRE_PATH")
    dig = sha256(a.cofre)
    if a.sha256 and dig != a.sha256.lower():
        sys.exit(f"sha256 da cópia não confere: {dig}")
    rows = abrir_cofre_ro(a.cofre, a.tabela)
    meta = {"cofre": os.path.basename(a.cofre), "sha256": dig, "linhas": len(rows),
            "copia_gravavel": os.access(a.cofre, os.W_OK), "definicao": prever_sequencia.__doc__.strip(),
            "regra_empate": cobre.__doc__.strip()}
    datas = [cofre.parse_data(x) for x in a.datas.split(",")] if a.datas else None
    res = backtest(normalizar(rows), cofre.ler_ativos(a.ativos) if a.ativos else None, datas)
    gravar(res, a.saida, meta)
    g = res["geral"]
    print(f"linhas={len(rows)} sha256={dig} grupos={len(res['por_grupo'])} n={g['n']} taxa={g['taxa_acerto']} "
          f"p_medio={g['p_medio']} empates={g['empates']} -> {a.saida}/")
    return res


if __name__ == "__main__":
    main()
