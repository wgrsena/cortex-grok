"""Orquestração das Funções 1 e 2 (orientações do Wagner): recurso 0 -> ramo fixo (sem MILP); senão, por categoria
de veículo (nunca mistura), plano 75% SEMPRE primeiro e 100% só depois (se 75 não resolver) ou como alternativa."""
from enumeracao import enumerar
from ranking import ordenar_a2
from milp import resolver_milp
from modelos import Parametros
from niveis import construir_universo
from ramo_fixo import resolver_ramo_fixo


def categorias(snapshot, pedido):
    if pedido.categoria_veiculo:
        return [pedido.categoria_veiculo]
    return sorted({c.categoria_veiculo for c in snapshot.cotas if c.tipo_bem == "veiculo"}) or ["carro"]


def _tenta(snapshot, pedido, params, plano, cat, solver):
    f = {"planos": (plano,), "categoria": cat}
    uni = construir_universo(snapshot, pedido, params, **f)
    r = solver(uni, pedido, params, snapshot=snapshot, filtros=f)
    r["universo"] = uni
    return r


def resolver_categoria(snapshot, pedido, params, cat, solver=resolver_milp):
    r75 = _tenta(snapshot, pedido, params, 75, cat, solver)
    if r75["ranking"]:
        alt = _tenta(snapshot, pedido, params, 100, cat, solver) if params.incluir_alternativa_100 else None
        return {**r75, "plano_testado": "75", "alternativa_100": alt, "categoria_veiculo": cat}
    r100 = _tenta(snapshot, pedido, params, 100, cat, solver)
    if r100["ranking"]:
        return {**r100, "plano_testado": "100 (75 não resolveu)", "alternativa_100": None, "categoria_veiculo": cat,
                "aproximacao_75": r75["aproximacao"]}
    return {**r75, "plano_testado": "75", "alternativa_100": r100, "categoria_veiculo": cat}


def resolver_funcao2(snapshot, pedido, params=None, solver=resolver_milp):
    params = params or Parametros()
    if pedido.recurso_proprio == 0:
        return resolver_ramo_fixo(snapshot, pedido, params)
    por_cat = {c: resolver_categoria(snapshot, pedido, params, c, solver) for c in categorias(snapshot, pedido)}
    if len(por_cat) == 1:
        return next(iter(por_cat.values()))
    todos = [x for r in por_cat.values() for x in r["ranking"]]
    ranking = ordenar_a2(todos, params.tol_prob, params.w_desempate) if todos else []
    melhor = por_cat[ranking[0].cartas[0].celula.tipo.categoria_veiculo] if ranking else next(iter(por_cat.values()))
    return {**melhor, "ranking": ranking, "por_categoria": por_cat}


def resolver_funcao1(snapshot, pedido, params=None, offset=0):
    """Função 1 por categoria; 75% primeiro, 100% só se o 75% não gerar combinações."""
    params = params or Parametros()
    saida, trunc, rotulos = [], False, {}
    for cat in categorias(snapshot, pedido):
        for plano, rot in ((75, "75"), (100, "100 (75 não resolveu)")):
            uni = construir_universo(snapshot, pedido, params, planos=(plano,), categoria=cat)
            r = enumerar(uni, pedido, params, offset)
            if r["combinacoes"]:
                break
        saida += [(c, cat, rot) for c in r["combinacoes"]]
        trunc = trunc or r["truncado"]
    return {"combinacoes": [c for c, _, _ in saida], "rotulos": [(cat, rot) for _, cat, rot in saida],
            "truncado": trunc, "universo": uni}
