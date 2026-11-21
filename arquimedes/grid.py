"""Grid do Arquimedes: gera, por faixa de crédito-alvo, só as combinações que miram aquela faixa.

O passo do grid está NA GERAÇÃO: para cada alvo T da lista (ex.: 50, 80, 100, 180, 200, 250 mil) o gerador
desce uma árvore de quantidades (branch-and-bound) e só fecha uma combinação quando a soma de crédito cai em
[T, teto) — teto = min(T·(1+tol), próxima faixa) — sendo cobertura mínima (tirar qualquer carta fica < T).
Nenhum alvo intermediário (51k, 52k...) existe, e nenhum ramo passa do teto. Detalhes em README.md.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from fractions import Fraction

from .modelos import GrupoArq, Oportunidade, ParametrosGrid, carregar_json
from .ranking import chave, chave_item, montar


@dataclass
class Estatisticas:
    alvos_testados: list = field(default_factory=list)   # exatamente as faixas configuradas
    nos: int = 0                                          # nós expandidos
    avaliadas: int = 0                                    # combinações completas avaliadas (folhas)
    podas: int = 0
    excluidos: dict = field(default_factory=dict)        # grupo -> motivo
    creditos_avaliados: list = field(default_factory=list)  # (alvo_c, teto_c, credito_c, n) se instrumentar
    truncadas: list = field(default_factory=list)        # faixas que bateram max_nos (melhor achado, sem prova de ótimo)


def _preparar(grupos, p: ParametrosGrid, est: Estatisticas) -> list[GrupoArq]:
    vistos: dict = {}
    for g in grupos:
        if g.cartas <= 0:
            est.excluidos[g.grupo] = "sem cartas"
            continue
        meses = g.prazo_restante - (p.parcelas_pagas if p.descontar_pagas_no_divisor else 0)
        if g.prazo_restante <= 0 or meses <= 0:
            est.excluidos[g.grupo] = "prazo restante insuficiente"
            continue
        k = (g.grupo, g.credito)
        if k in vistos:   # mesma carta listada 2x: soma as cartas se o resto é idêntico
            a = vistos[k]
            if (a.categoria, a.mediana_lance_livre, a.pct_embutido, a.prazo_restante, a.parcela_antes) != \
               (g.categoria, g.mediana_lance_livre, g.pct_embutido, g.prazo_restante, g.parcela_antes):
                raise ValueError(f"grupo {g.grupo}: carta {g.credito} repetida com dados divergentes")
            vistos[k] = GrupoArq(**{**a.__dict__, "cartas": a.cartas + g.cartas})
        else:
            vistos[k] = g
    return sorted(vistos.values(), key=chave_item)


def _busca_faixa(itens, alvo, teto, top_k, est, instrumentar, max_nos):
    """Branch-and-bound sobre a soma de crédito. Itens em ordem de ranking (mediana crescente).

    Poda lexicográfica (exata, em inteiros/frações): limite inferior da mediana; em empate exato de mediana,
    limite superior do embutido; em empate de embutido, limite superior do prazo. Todos monótonos em j,
    então a poda corta o resto do laço (break). Excedendo `max_nos`, a faixa sai marcada como truncada.
    """
    n = len(itens)
    # ordem exata pela mediana efetiva (a mesma da chave), depois embutido e prazo: base da poda monótona
    itens = sorted(itens, key=lambda g: (Fraction(int(g.mediana_lance_livre * g.categoria * 100), int(g.categoria * 100)),
                                         -g.pct_embutido, -g.prazo_restante, g.grupo, g.credito))
    k = [int(g.credito * 100) for g in itens]
    cat = [int(g.categoria * 100) for g in itens]
    lan = [int(g.mediana_lance_livre * g.categoria * 100) for g in itens]
    emb = [int(g.pct_embutido * 10000) for g in itens]
    prz = [g.prazo_restante for g in itens]
    m = [Fraction(lan[i], cat[i]) for i in range(n)]           # a mesma mediana que a chave usa
    mf = [float(x) for x in m]
    cap = [g.cartas for g in itens]
    suf = [0] * (n + 1)                        # crédito máximo ainda alcançável a partir de i
    for i in range(n - 1, -1, -1):
        suf[i] = suf[i + 1] + cap[i] * k[i]
    kmax = [0] * (n + 1)                       # maior carta a partir de i (limite do nº de cartas)
    for i in range(n - 1, -1, -1):
        kmax[i] = max(kmax[i + 1], k[i])
    r_max = max((Fraction(cat[i], k[i]) for i in range(n)), default=Fraction(1))
    r_min = min((Fraction(cat[i], k[i]) for i in range(n)), default=Fraction(1))
    rmaxf, rminf = float(r_max), float(r_min)
    melhores: list = []                        # [(chave, escolha)] ordenado, len <= top_k
    escolha: list = []

    def media_lim(s_num, s_cat, v, c_min, c_max, sobe):
        """Extremo da média ponderada ao juntar categoria em [c_min, c_max] com valor v (sobe = limite inferior)."""
        if s_cat == 0:
            return v
        media = Fraction(s_num, s_cat) if isinstance(v, Fraction) else s_num / s_cat
        if (media <= v) == sobe:               # juntar puxa para v: o extremo usa o mínimo de peso
            c = c_min
        else:
            c = c_max
        return (s_num + v * c) / (s_cat + c)

    def podar(j, cred, s_lan, s_cat, s_emb, prazo, ncart):
        wk = melhores[-1][0]
        lbf = media_lim(s_lan, s_cat, mf[j], (alvo - cred) * rminf, (teto - 1 - cred) * rmaxf, True)
        if lbf > float(wk[0]) + 1e-9:
            return True
        if lbf < float(wk[0]) - 1e-9:
            return False
        c_min, c_max = (alvo - cred) * r_min, (teto - 1 - cred) * r_max
        lb = media_lim(s_lan, s_cat, m[j], c_min, c_max, True) if s_cat else m[j]
        if lb != wk[0]:
            return lb > wk[0]
        # empate exato de mediana: só vale restringir ao bloco se P está na mesma mediana de j
        if s_cat and s_lan * cat[j] != lan[j] * s_cat:
            return False
        e_j = Fraction(emb[j])
        ub_e = media_lim(s_emb, s_cat, e_j, c_min, c_max, False) if s_cat else e_j
        if -ub_e != wk[1]:
            return -ub_e > wk[1]
        if s_cat and s_emb != emb[j] * s_cat:
            return False
        ub_p = -min(prazo, prz[j])
        if ub_p != wk[2]:
            return ub_p > wk[2]
        # empate total até o prazo: excedente >= 0; se o pior já tem excedente 0, limita pelo nº de cartas
        if wk[3] > 0:
            return False
        falta = alvo - cred
        return ncart + -(-falta // kmax[j]) > wk[4]

    def dfs(i, cred, s_lan, s_cat, s_emb, prazo, kmin, ncart):
        for j in range(i, n):
            if cred + suf[j] < alvo:           # nem tudo o que resta alcança o alvo
                return
            if nos[0] >= max_nos:
                truncou[0] = True
                return
            if len(melhores) == top_k and podar(j, cred, s_lan, s_cat, s_emb, prazo, ncart):
                est.podas += 1
                return                         # limites monótonos em j: o resto do laço também cai
            for q in range(1, cap[j] + 1):
                c = cred + q * k[j]
                if c >= teto:                  # nunca gera acima do teto da faixa
                    break
                nos[0] += 1
                escolha.append((j, q))
                lc, cc, ec = s_lan + q * lan[j], s_cat + q * cat[j], s_emb + q * emb[j] * cat[j]
                pz, km, nc = min(prazo, prz[j]), min(kmin, k[j]), ncart + q
                if c >= alvo:
                    if c - km < alvo:          # cobertura mínima
                        est.avaliadas += 1
                        if instrumentar:
                            est.creditos_avaliados.append((alvo, teto, c, nc))
                        canon = tuple(sorted((itens[a].grupo, k[a], b) for a, b in escolha))
                        ch = chave(lc, cc, ec, pz, c - alvo, nc, canon)
                        if len(melhores) < top_k or ch < melhores[-1][0]:
                            melhores.append((ch, list(escolha)))
                            melhores.sort(key=lambda e: e[0])
                            del melhores[top_k:]
                    escolha.pop()
                    break                      # mais cartas só aumentam o excedente
                dfs(j + 1, c, lc, cc, ec, pz, km, nc)
                escolha.pop()

    nos, truncou = [0], [False]
    dfs(0, 0, 0, 0, 0, 10**9, 10**18, 0)
    est.nos += nos[0]
    if truncou[0]:
        est.truncadas.append(alvo // 100)
    return [[(itens[a], b) for a, b in esc] for _, esc in melhores]


def gerar(grupos, p: ParametrosGrid = ParametrosGrid(), instrumentar: bool = False):
    """Devolve (oportunidades ranqueadas, estatísticas). Nada intermediário sai daqui."""
    est = Estatisticas()
    itens = _preparar(grupos, p, est)
    saida: list[Oportunidade] = []
    for i, faixa in enumerate(p.faixas):
        alvo, teto = p.janela(i)
        est.alvos_testados.append(faixa)
        for rank, esc in enumerate(_busca_faixa(itens, alvo, teto, p.top_k, est, instrumentar, p.max_nos), 1):
            saida.append(montar(faixa, rank, esc, p))
    return saida, est


def _br(v, casas=2) -> str:
    s = f"{float(v):,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def tabela(ops, p: ParametrosGrid) -> str:
    cab = "| Faixa (R$) | # | Cartas | Crédito (R$) | Mediana | Prazo | Embutido | Pós mês 1 (R$) | Pós por grupo | Próx. assembleia |"
    linhas = [cab, "|" + "---|" * 10]
    por_faixa = {f: [o for o in ops if o.faixa_alvo == f] for f in p.faixas}
    for f, lst in por_faixa.items():
        if not lst:
            linhas.append(f"| {_br(f, 0)} | – | sem oportunidade na faixa | | | | | | | |")
        for o in lst:
            cartas = " + ".join(f"{c.qtd}×{c.grupo}" for c in o.cartas)
            pos = "; ".join(f"{c.grupo}: {c.qtd}×{_br(c.parcela_pos)} ({c.meses}m)" for c in o.cartas)
            data = o.proxima_assembleia.strftime("%d/%m") if o.proxima_assembleia else "n/i"
            linhas.append(f"| {_br(f, 0)} | {o.rank} | {cartas} | {_br(o.credito_total)} | {_br(o.mediana_agregada * 100)}% "
                          f"| {o.prazo}m | {_br(o.embutido * 100, 0)}% | {_br(o.parcela_pos_total)} | {pos} | {data} |")
    return "\n".join(linhas)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Grid do Arquimedes: imprime só a tabela ranqueada.")
    ap.add_argument("--entrada", required=True, help="JSON com {'grupos': [...]}")
    ap.add_argument("--faixas", help="crédito-alvo em R$, separado por vírgula (padrão 50000,80000,100000,180000,200000,250000)")
    ap.add_argument("--top-k", type=int, default=1)
    a = ap.parse_args(argv)
    grupos, meta = carregar_json(a.entrada)
    kw = {"top_k": a.top_k}
    if a.faixas:
        kw["faixas"] = tuple(int(x) for x in a.faixas.split(","))
    p = ParametrosGrid(**kw)
    ops, est = gerar(grupos, p)
    if meta.get("_aviso"):
        print(f"AVISO: {meta['_aviso']}\n")
    print(tabela(ops, p))
    print(f"\n{len(ops)} oportunidades ranqueadas; {est.avaliadas} combinações avaliadas; {est.nos} nós; "
          f"excluídos: {est.excluidos or 'nenhum'}. Seguro de vida à parte.")
    if est.truncadas:
        print(f"ATENÇÃO: faixas {est.truncadas} bateram o limite de nós; resultado sem prova de ótimo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
