"""Ramo LANCE FIXO (orientação do Wagner, ponto 1): recurso_proprio == 0 -> NÃO roda MILP de lance livre.
Lê só `qtd_fixo_contemplado_mes` da tabela fato e ranqueia grupos por volume de fixo (+ crédito, taxa, parcela,
pesos em Parametros). v1.1: cada linha também traz `chance_fixo` = 1 / n_ofertantes_fixo_medio ("1 contra o número de
ofertantes", sem mediana), só INFORMATIVA: não entra no score nem na ordem (o ranking multi-critério não mudou)."""
from modelos import D, cent, cent_baixo
from niveis import chance_fixo   # fonte única do cálculo (N2)
from prazos import extras_oportunidade

MENSAGEM_COMPARATIVA = (
    "Sorteio: sua cota concorre contra todos os integrantes do grupo (1 contra todos). "
    "Lance fixo: você concorre só contra quem ofertou o lance fixo (1 contra os ofertantes). "
    "Por isso a chance real no lance fixo é maior que no sorteio.")


def _norm_alto(v, vs):                 # maior é melhor, normalizado pelo máximo
    m = max(vs)
    return D(1) if m == 0 else v / m


def _norm_baixo(v, vs):                # menor é melhor, min-max (1 se todos iguais)
    lo, hi = min(vs), max(vs)
    return D(1) if hi == lo else (hi - v) / (hi - lo)


def candidatos_fixo(snapshot, pedido, params, plano, categoria):
    A = pedido.credito_liquido_alvo
    lim = params.teto_credito(A)
    vistos, saida = set(), []
    for c in snapshot.cotas:
        chave = (c.grupo, c.plano_pct, c.credito, c.taxa_pct, c.parcela)
        if (c.tipo_bem != "veiculo" or c.status != "disponivel" or c.plano_pct != plano or chave in vistos
                or (categoria and c.categoria_veiculo != categoria) or not c.tem_lance_fixo
                or not c.qtd_fixo_contemplado_mes or c.qtd_fixo_contemplado_mes <= 0
                or c.parcela > pedido.parcela_max or c.credito > lim):
            continue
        vistos.add(chave)
        cat = c.categoria
        lance = cent(c.lance_fixo_pct * cat)                   # trava: 25% da CATEGORIA
        emb = min(lance, cent_baixo(c.pct_embutido_max * cat)) # embutido necessário, limitado ao teto
        cobre = emb >= lance
        if params.fixo_exigir_embutido_cobrir and not cobre:
            continue
        saida.append({"cota_id": c.cota_id, "grupo": c.grupo, "plano": c.plano_pct, "categoria_veiculo": c.categoria_veiculo,
                      "prazo_total": c.prazo_total, "credito": c.credito, "taxa_adm_serie": c.taxa_pct,
                      "parcela_pre_contemplacao": c.parcela, "lance_fixo_pct": c.lance_fixo_pct, "lance_fixo_rs": lance,
                      "embutido_necessario_rs": emb, "falta_recurso_rs": lance - emb, "embutido_cobre_lance": cobre,
                      "credito_liquido": c.credito - emb, "qtd_fixo_contemplado_mes": c.qtd_fixo_contemplado_mes,
                      "n_ofertantes_fixo_medio": c.n_ofertantes_fixo_medio, "chance_fixo": chance_fixo(c.n_ofertantes_fixo_medio),
                      **extras_oportunidade(c.mediana_lance_livre, c.pct_embutido_max, c.data_coleta, c.proxima_assembleia, params)})
    if not saida:
        return []
    w = (params.peso_credito, params.peso_taxa, params.peso_fixo, params.peso_parcela)
    desv = [abs(x["credito_liquido"] - A) for x in saida]
    for x, d in zip(saida, desv):
        s_cred = max(D(0), 1 - d / A) if A > 0 else D(1)
        s = (w[0] * s_cred + w[1] * _norm_baixo(x["taxa_adm_serie"], [y["taxa_adm_serie"] for y in saida])
             + w[2] * _norm_alto(x["qtd_fixo_contemplado_mes"], [y["qtd_fixo_contemplado_mes"] for y in saida])
             + w[3] * _norm_baixo(x["parcela_pre_contemplacao"], [y["parcela_pre_contemplacao"] for y in saida]))
        x["score"] = (s / sum(w)) if sum(w) > 0 else D(0)
    saida.sort(key=lambda x: (-x["score"], -x["qtd_fixo_contemplado_mes"], x["grupo"], x["cota_id"]))
    return saida[:params.top_fixo]


def resolver_ramo_fixo(snapshot, pedido, params):
    """75% primeiro; 100% só se o 75% não devolver nada ou como alternativa rotulada (ponto 2)."""
    cats = [pedido.categoria_veiculo] if pedido.categoria_veiculo else sorted(
        {c.categoria_veiculo for c in snapshot.cotas if c.tipo_bem == "veiculo"})
    por_cat = {}
    for cat in cats:
        r75 = candidatos_fixo(snapshot, pedido, params, 75, cat)
        r100 = candidatos_fixo(snapshot, pedido, params, 100, cat)
        por_cat[cat] = {"ranking": r75 or r100, "plano_testado": "75" if r75 else "100 (75 não resolveu)",
                        "alternativa_100": r100 if (r75 and params.incluir_alternativa_100) else []}
    return {"metodo": "lance_fixo", "mensagem_comparativa": MENSAGEM_COMPARATIVA, "por_categoria": por_cat,
            "ranking": sorted((x for v in por_cat.values() for x in v["ranking"]), key=lambda x: -x["score"])}
