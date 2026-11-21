"""Função 2 via MILP (HiGHS/highspy). Modelo das seções 3 a 7 da ESPECIFICACAO_V1_1.md.

Escala interna: milhares de R$. Variáveis: n[c] inteiro (unidades da célula c = tipo×nível), e[c] contínuo
(embutido da célula), x[k,π] inteiro (atribuição à cota física π: impõe 4.1 exatamente, mesmo com tipos
agregados de várias cotas), u[k] binário (tipo usado; só para o corte de exclusão), folgas sA/sP/sB.
Resolução lexicográfica S1..S5 em solves sequenciais; cada estágio congela o ótimo (com folga) do anterior.
D1 (decisão provisória): S4 = min embutido total (o necessário) e depois min recurso usado.
"""
import math
from dataclasses import replace
from decimal import Decimal

import highspy
import numpy as np

from embutido import fazer_celula, montar_combo
from enumeracao import unidades_com_ids
from ranking import refinar_e_ranquear
from modelos import D, cent
from niveis import construir_universo

K = 1000.0            # escala: R$ -> milhares de R$
EPS = 1e-6            # folga numérica dos congelamentos (R$ 0,001 na escala; abaixo de 1 centavo)
LN_NULA = -50.0       # níveis sem p (SEM_HISTORICO incluído): ln p artificial muito baixo -> ficam por último
INF = highspy.kHighsInf
P_INF = Decimal("1e9")
K_RESERVA = 5         # candidatos gerados por busca de reserva


class Modelo:
    def __init__(self):
        self.cols, self.linhas, self.expr = [], [], {}

    def col(self, lb, ub, inteiro=False):
        self.cols.append((lb, ub, inteiro))
        return len(self.cols) - 1

    def linha(self, coefs, lo=-INF, hi=INF):
        self.linhas.append((lo, hi, dict(coefs)))

    def copia(self):
        m = Modelo()
        m.cols, m.linhas, m.expr = list(self.cols), list(self.linhas), self.expr
        return m

    def resolver(self, coefs, maximizar, gap, tempo):
        h = highspy.Highs()
        for o, v in (("output_flag", False), ("mip_rel_gap", gap), ("mip_abs_gap", 1e-9 if gap == 0 else 1e-6),
                     ("time_limit", float(tempo)), ("threads", 1), ("random_seed", 1)):
            h.setOptionValue(o, v)
        for lb, ub, _ in self.cols:
            h.addVar(lb, ub)
        for j, (_, _, inteiro) in enumerate(self.cols):
            if inteiro:
                h.changeColIntegrality(j, highspy.HighsVarType.kInteger)
        for lo, hi, cf in self.linhas:
            h.addRow(lo, hi, len(cf), np.array(list(cf), dtype=np.int32), np.array(list(cf.values()), dtype=float))
        for j, c in coefs.items():
            h.changeColCost(j, c)
        h.changeObjectiveSense(highspy.ObjSense.kMaximize if maximizar else highspy.ObjSense.kMinimize)
        h.run()
        info = h.getInfo()
        if info.primal_solution_status != 2:                     # sem solução viável
            return None
        return list(h.getSolution().col_value), max(0.0, float(info.mip_gap))


def construir(universo, pedido, params, relax=(False, False, False), cortes=()):
    """Monta o modelo base. relax = (sA, sP, sB) livres? Retorna (Modelo, células, índices de colunas)."""
    A, B, Pmax = (float(pedido.credito_liquido_alvo) / K, float(pedido.recurso_proprio) / K,
                  float(pedido.parcela_max) / K)
    M = Modelo()
    cels = [fazer_celula(t, n, params) for t in universo.tipos for n in t.niveis
            if n.tipo != "referencia" or params.incluir_sem_historico]
    ub_tipo = {t.idx: sum(universo.caps[f] for f in t.fontes) for t in universo.tipos}
    nc = [M.col(0, ub_tipo[c.tipo.idx], True) for c in cels]
    ec = [M.col(0, float(c.teto_rs) / K * ub_tipo[c.tipo.idx]) for c in cels]
    sA, sP, sB = (M.col(0, INF if r else 0) for r in relax)
    x = {(t.idx, f): M.col(0, universo.caps[f], True) for t in universo.tipos for f in t.fontes}
    u = {t.idx: M.col(0, 1, True) for t in universo.tipos}
    for t in universo.tipos:                                       # 4.1 + ligação n_k = Σ_π x
        ns = {nc[j]: 1.0 for j, c in enumerate(cels) if c.tipo.idx == t.idx}
        M.linha({**ns, **{x[t.idx, f]: -1.0 for f in t.fontes}}, 0, 0)
        M.linha({**{c: 1.0 for c in ns}, u[t.idx]: -float(ub_tipo[t.idx])}, hi=0)   # n_k <= q u_k
        M.linha({**{c: 1.0 for c in ns}, u[t.idx]: -1.0}, lo=0)                     # n_k >= u_k
    for f, q in universo.caps.items():
        M.linha({x[t.idx, f]: 1.0 for t in universo.tipos if f in t.fontes}, hi=q)
    for j, c in enumerate(cels):                                   # 4.2 e 4.3 (teto = min(ē·Cat, R) por unidade)
        M.linha({ec[j]: 1.0, nc[j]: -float(c.teto_rs) / K}, hi=0)
    liq = {**{nc[j]: float(c.tipo.credito) / K for j, c in enumerate(cels)}, **{e: -1.0 for e in ec}}
    rec = {**{nc[j]: float(c.lance_rs) / K for j, c in enumerate(cels)}, **{e: -1.0 for e in ec}}
    par = {nc[j]: float(c.tipo.parcela) / K for j, c in enumerate(cels)}
    M.linha({**rec, sB: -1.0}, hi=B)                               # 4.4
    M.linha({**liq, sA: 1.0}, lo=A)                                # 4.5
    if params.delta_credito is not None:                           # sem teto de sobra por padrão
        M.linha(liq, hi=A * (1 + float(params.delta_credito)))
    M.linha({**par, sP: -1.0}, hi=Pmax)                            # 4.6
    M.linha({c: 1.0 for c in nc}, lo=1)                            # combo não vazio
    for usados in cortes:                                          # corte de exclusão por conjunto de tipos
        M.linha({u[i]: (-1.0 if i in usados else 1.0) for i in u}, lo=1 - len(usados))
    M.expr = {
        "L": {nc[j]: (math.log(c.nivel.p) if c.nivel.p is not None else LN_NULA) for j, c in enumerate(cels)},
        "taxa": {nc[j]: float(c.tipo.taxa_rs) / K for j, c in enumerate(cels)},
        "W": {nc[j]: float(c.nivel.w or 0) for j, c in enumerate(cels)},
        "parcela": par, "e": {e: 1.0 for e in ec}, "recurso": rec, "n": {c: 1.0 for c in nc},
        "sA": {sA: K / max(float(pedido.credito_liquido_alvo), 1.0)}, "sP": {sP: K / max(float(pedido.parcela_max), 1.0)},
        "sB": {sB: 1.0},
    }
    return M, cels, nc, ec


def _val(coefs, sol):
    return sum(c * sol[j] for j, c in coefs.items())


def lexicografico(M, estagios, params, gap, tempo):
    """estagios: [(expr, maximizar, folga)]. Retorna (solução, pior gap) ou None se o 1º estágio é inviável."""
    M, sol, gmax = M.copia(), None, 0.0
    for nome, maximizar, folga in estagios:
        cf = M.expr[nome] if isinstance(nome, str) else nome
        r = M.resolver(cf, maximizar, gap, tempo)
        if r is None:
            break                                                   # por tolerância numérica: fica o anterior
        sol, g = r
        gmax = max(gmax, g)
        v = _val(cf, sol)
        M.linha(cf, lo=v - folga - EPS) if maximizar else M.linha(cf, hi=v + folga + EPS)
    return (sol, gmax) if sol is not None else None


def estagios_exatos(params):
    tol_l = math.log(1 / (1 - float(params.tol_prob))) if params.tol_prob < 1 else INF
    w = [("W", True, 0.0)] if params.w_desempate else []      # ponto 4 do Wagner: W desempata após p
    return [("L", True, tol_l), *w, ("taxa", False, float(params.tol_taxa_rs) / K), ("parcela", False, 0.0),
            ("e", False, 0.0), ("recurso", False, 0.0), ("n", False, 0.0)]


def _unidades(sol, nc, cels, universo):
    indices = [j for j, c in enumerate(nc) for _ in range(int(round(sol[c])))]
    return unidades_com_ids(indices, cels, universo)


def candidatos(universo, pedido, params, k, gap, tempo):
    """K candidatos exatos (S1..S5 + corte de exclusão por tipos usados). Retorna (combos 'continuo', pior gap)."""
    if not universo.tipos:
        return [], 0.0
    cortes, saida, gmax = [], [], 0.0
    while len(saida) < k:
        M, cels, nc, _ = construir(universo, pedido, params, cortes=cortes)
        r = lexicografico(M, estagios_exatos(params), params, gap, tempo)
        if r is None:
            break
        sol, g = r
        gmax = max(gmax, g)
        combo = montar_combo(_unidades(sol, nc, cels, universo), pedido, params, "continuo")
        cortes.append(combo.tipos_usados)
        if combo.viavel:
            saida.append(combo)
    return saida, gmax


def _reservas(principal, universo, pedido, params, gap, tempo):
    """Combos com cotas físicas disjuntas do principal (e entre si), re-resolvendo com essas cotas zeradas."""
    usados, reservas = set(principal.cota_ids), []
    for _ in range(params.n_reservas):
        uni = replace(universo, caps={k: (0 if k in usados else q) for k, q in universo.caps.items()})
        cands, _ = candidatos(uni, pedido, params, K_RESERVA, gap, tempo)
        rank, _ = refinar_e_ranquear(cands, pedido, params)
        if not rank:
            break
        reservas.append(rank[0])
        usados |= rank[0].cota_ids
    return reservas


def _combo_aprox(sol, nc, ec, cels, universo, pedido, params):
    und = _unidades(sol, nc, cels, universo)
    por_celula = {}
    for (cel, _) in und:
        por_celula[id(cel)] = por_celula.get(id(cel), 0) + 1
    j_de = {id(c): j for j, c in enumerate(cels)}
    es = [min(cel.teto_rs, cent(D(repr(max(0.0, sol[ec[j_de[id(cel)]]]) * K)) / por_celula[id(cel)]))
          for (cel, _) in und]
    return montar_combo(und, pedido, params, "dado", es)


def aproximar(universo, pedido, params, gap, tempo):
    """Seção 7. R1: cobertura e B rígidos, relaxa crédito (sA) e parcela (sP). Opções 'credito' e 'parcela'.
    Opção 'recurso' (sA=sP=0, relaxa só B) sempre tentada. R2 (relaxa tudo) só se R1 for inviável."""
    cauda = [("L", True, 0.0), *([("W", True, 0.0)] if params.w_desempate else []), ("taxa", False, 0.0), ("e", False, 0.0), ("n", False, 0.0)]
    planos = [("credito", (True, True, False), [("sA", False, 0.0), ("sP", False, 0.0)]),
              ("parcela", (True, True, False), [("sP", False, 0.0), ("sA", False, 0.0)]),
              ("recurso", (False, False, True), [("sB", False, 0.0)])]
    opcoes, vistos, r1 = [], set(), False
    r2 = ("recurso_r2", (True, True, True), [("sB", False, 0.0), ("sA", False, 0.0), ("sP", False, 0.0)])
    for foco, relax, prim in planos + [r2]:
        if foco == "recurso_r2" and r1:
            break
        M, cels, nc, ec = construir(universo, pedido, params, relax)
        r = lexicografico(M, prim + cauda, params, gap, tempo)
        if r is None:
            continue
        r1 = r1 or foco in ("credito", "parcela")
        combo = _combo_aprox(r[0], nc, ec, cels, universo, pedido, params)
        chave = tuple(sorted((c.celula.tipo.idx, str(c.celula.nivel.lance_pct)) for c in combo.cartas))
        if chave in vistos:
            continue
        vistos.add(chave)
        opcoes.append({"foco": foco.replace("_r2", ""), "combo": combo})
    if not opcoes:
        return None
    return {"nivel": "R1" if r1 else "R2", "opcoes": opcoes[:3]}


def resolver_milp(universo, pedido, params, tempo_limite_s=None, gap_relativo=None, snapshot=None, filtros=None):
    """Função 2: candidatos exatos -> refinamento em J -> ranking A2 -> reservas disjuntas.
    Sem solução exata: aproximação da seção 7 (se `snapshot` for passado, o universo da aproximação não
    aplica o pré-filtro de parcela, que é o que a relaxação de parcela precisa; `filtros` = planos/categoria)."""
    gap = params.milp_gap_relativo if gap_relativo is None else gap_relativo
    tempo = params.milp_tempo_limite_s if tempo_limite_s is None else tempo_limite_s
    cands, gmax = candidatos(universo, pedido, params, params.K_top, gap, tempo)
    ranking, descartados = refinar_e_ranquear(cands, pedido, params)
    reservas = _reservas(ranking[0], universo, pedido, params, gap, tempo) if ranking else []
    aprox = None
    if not ranking:
        uni = construir_universo(snapshot, replace(pedido, parcela_max=P_INF), params, **(filtros or {})) if snapshot else universo
        aprox = aproximar(uni, pedido, params, gap, tempo) or "sem_opcoes"
    return {"metodo": "milp", "ranking": ranking, "descartado_discreto": descartados, "reservas": reservas,
            "aproximacao": aprox, "gap_milp": gmax}
