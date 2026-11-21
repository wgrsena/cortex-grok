"""Ranking A2, seleção lexicográfica de candidatos e refinamento exato em J (6.3), usados em PRODUÇÃO pelo MILP
(milp.py) e pela Função 2 (funcao2.py). Extraído de forca_bruta.py na revisão do Cortex Reviewer (I3): o serviço
não importa mais o oráculo de testes."""
from fractions import Fraction

from embutido import montar_combo
from modelos import D

# Chave A2 do ranking final (spec): taxa, parcela, recurso usado, embutido, nº de cartas.
ORDEM_A2 = ("taxa_total", "parcela_total", "recurso_usado", "embutido_total", "n_cartas")
# Seleção de candidatos S2..S5. D1 (decisão provisória): S4 = embutido mínimo necessário e depois recurso.
ORDEM_CANDIDATOS = ("taxa_total", "parcela_total", "embutido_total", "recurso_usado", "n_cartas")


def melhor(pool, tol_prob, tol_taxa, ordem=ORDEM_A2, w_desempate=True):
    """Escolhe o melhor por filtros sucessivos (equivale aos solves lexicográficos S1..S5 / chave A2).
    Candidatos sem probabilidade (None) só entram quando não há nenhum com probabilidade."""
    com_p = [x for x in pool if x.prob is not None]
    if com_p:
        pmax = max(x.prob for x in com_p)
        pool = [x for x in com_p if x.prob >= pmax * (1 - Fraction(tol_prob))]
    if w_desempate:            # ponto 4 do Wagner: sequência seguida desempata depois da probabilidade
        wmax = max(x.w_soma for x in pool)
        pool = [x for x in pool if x.w_soma == wmax]
    for attr in ordem:
        tol = tol_taxa if attr == "taxa_total" else 0
        m = min(getattr(x, attr) for x in pool)
        pool = [x for x in pool if getattr(x, attr) <= m + tol]
    return min(pool, key=_desempate)


def _desempate(combo):
    return tuple((c.celula.tipo.idx, str(c.celula.nivel.lance_pct), c.cota_id) for c in combo.cartas)


def ordenar_a2(combos, tol_prob, w_desempate=True):
    resto, saida = list(combos), []
    while resto:
        b = melhor(resto, tol_prob, D(0), w_desempate=w_desempate)
        saida.append(b)
        resto.remove(b)
    return saida


def refinar_e_ranquear(candidatos, pedido, params):
    """Refinamento exato em J (6.3) por candidato + ranking A2. Retorna (ranking, descartados)."""
    validos, descartados = [], []
    for cand in candidatos:
        r = montar_combo([(c.celula, c.cota_id) for c in cand.cartas], pedido, params, "dp")
        (validos if r.viavel else descartados).append(r)
    return ordenar_a2(validos, params.tol_prob, params.w_desempate), descartados
