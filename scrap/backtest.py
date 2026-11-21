"""Backtest da probabilidade (seção 8 da spec + ponto 9 do Wagner). Para cada grupo e assembleia t, monta os níveis
só com as 6 assembleias anteriores (niveis_livres) e confere se o lance M teria ganho em t (M >= menor lance livre
contemplado). Só usa dados de grupos ATIVOS na data (backtest rolante). Compara os dois modos de probabilidade.

uso: python backtest.py --cofre cofre.csv|xlsx [--ativos ativos.csv] [--json]
Dados reais ficam fora de qualquer repositório (/workspace/disal-solver/dados/)."""
import argparse
import json
import os
import sys
from dataclasses import replace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solver"))  # modelos, niveis
import cofre  # noqa: E402
from modelos import MODOS_PROB, Parametros
from niveis import niveis_livres  # noqa: E402

BINS = 10


def pares(rows, ativos, params):
    """[(p, y, w, grupo)] de todos os níveis de todas as assembleias com lance livre contemplado."""
    out = []
    for g, asm in cofre.assembleias(rows, ativos).items():
        for t, a in enumerate(asm):
            if a["menor_livre"] is None or t == 0:
                continue
            _, _, _, niveis = niveis_livres(cofre.c_recente(asm, t), params)
            for n in niveis:
                if n.p is not None:
                    out.append((float(n.p), 1 if n.lance_pct >= a["menor_livre"] else 0, n.w, g))
    return out


def metricas(ps):
    if not ps:
        return {"n": 0, "brier": None, "p_medio": None, "y_medio": None, "calibracao": []}
    n = len(ps)
    cal = []
    for b in range(BINS):
        itens = [x for x in ps if min(int(x[0] * BINS), BINS - 1) == b]
        if itens:
            cal.append({"faixa": f"{b / BINS:.1f}-{(b + 1) / BINS:.1f}", "n": len(itens),
                        "p_medio": round(sum(x[0] for x in itens) / len(itens), 4),
                        "freq_observada": round(sum(x[1] for x in itens) / len(itens), 4)})
    return {"n": n, "brier": round(sum((p - y) ** 2 for p, y, *_ in ps) / n, 4),
            "p_medio": round(sum(x[0] for x in ps) / n, 4), "y_medio": round(sum(x[1] for x in ps) / n, 4),
            "calibracao": cal}


def backtest(rows, ativos=None, params=None):
    params = params or Parametros()
    return {m: metricas(pares(rows, ativos, replace(params, modo_probabilidade=m))) for m in MODOS_PROB}


def imprimir(res):
    for m, r in res.items():
        print(f"\nmodo={m}  n={r['n']}  Brier={r['brier']}  p_medio={r['p_medio']}  y_medio={r['y_medio']}")
        for c in r["calibracao"]:
            print(f"  p {c['faixa']}  n={c['n']:>6}  p_medio={c['p_medio']:.3f}  observada={c['freq_observada']:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cofre", required=True)
    ap.add_argument("--ativos")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = backtest(cofre.ler_tabela(a.cofre), cofre.ler_ativos(a.ativos) if a.ativos else None)
    print(json.dumps(res, ensure_ascii=False, indent=1)) if a.json else imprimir(res)
