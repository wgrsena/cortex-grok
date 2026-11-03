"""Níveis de lance por tipo (seção 2), conferência do valor do flag de teto e pré-filtros (4.10)."""
from collections import Counter
from fractions import Fraction

from modelos import (D, cent, MAX_Q, Nivel, Tipo, Universo)

TETOS_VALIDOS = (D("0"), D("0.10"), D("0.25"))   # fração da CATEGORIA (crédito + taxa); passo de 5 pontos em embutido.J


def alerta_sanidade(cota):
    """Só confere o VALOR do flag. Nada por número de grupo: o teto (0, 10% ou 25%) e as exceções sem fixo/embutido
    (grupos sem fixo e sem embutido) vêm como DADO do catálogo (pct_embutido_max, tem_lance_fixo), verificado por série."""
    if cota.pct_embutido_max not in TETOS_VALIDOS:
        return f"flag_invalido grupo={cota.grupo} pct_embutido_max={cota.pct_embutido_max} (vale o flag)"
    return None


def niveis_livres(c, params):
    """Níveis livres a partir do histórico c1..c6 (fração da categoria; None = sem lance livre).
    Retorna (hist_flag, N, W, niveis). Seção 2. Usado também pelo backtest."""
    c = (tuple(c) + (None,) * 6)[:6]
    validos = [x for x in c if x is not None]
    N = len(validos)
    W = 0
    for x in c:
        if x is None:
            break
        W += 1
    flag = "SEM_HISTORICO" if N == 0 else ("PARCIAL" if N < 6 else "OK")
    niveis = []
    brutos = []
    for w in range(1, W + 1):
        M = max(c[:w])
        if M > 1:                       # acima de 100% da categoria: descartado (M é não decrescente)
            break
        h = sum(1 for x in validos if x <= M)
        p = Fraction(h, N) if params.modo_probabilidade == "fracao_h_sobre_N" else Fraction(w, 6)
        brutos.append((w, M, h, p))
    for i, (w, M, h, p) in enumerate(brutos):
        if i + 1 < len(brutos) and brutos[i + 1][1] == M:
            continue                    # M_w = M_{w+1}: mantém só o w maior
        if w >= params.w_min:
            niveis.append(Nivel("livre", w, M, p, h, N))
    return flag, N, W, tuple(niveis)


def chance_fixo(n_ofertantes):
    """1 / nº de ofertantes (limitada a 1). None se o número de ofertantes faltar ou for <= 0.
    Fonte única (N2): usada no nível fixo do MILP/Função 2 e na coluna informativa do ramo fixo."""
    if n_ofertantes is None or n_ofertantes <= 0:
        return None
    return min(Fraction(1), 1 / Fraction(n_ofertantes))


def calcular_niveis(cota, params):
    """Retorna (hist_flag, N, W, niveis): níveis livres + fixo + referência. Seção 2."""
    flag, N, W, livres = niveis_livres(cota.c, params)
    niveis = list(livres)
    p_fixo = chance_fixo(cota.n_ofertantes_fixo_medio)
    if cota.tem_lance_fixo and p_fixo is not None and cota.lance_fixo_pct <= 1:
        niveis.append(Nivel("fixo", None, cota.lance_fixo_pct, p_fixo, 0, 0))
    if N == 0 and params.incluir_sem_historico and cota.lance_ref_irmaos is not None:
        niveis.append(Nivel("referencia", None, cota.lance_ref_irmaos, None, 0, 0))
    return flag, N, W, tuple(niveis)


def construir_universo(snapshot, pedido, params, planos=None, categoria=None) -> Universo:
    """Pré-filtros 4.10 + imóvel (4.8) + agregação de cotas idênticas.
    `planos`: restringe aos planos dados (ex.: (75,)); `categoria`: carro|moto|caminhao (padrão: do pedido)."""
    categoria = categoria or pedido.categoria_veiculo
    if pedido.tipo_bem != "veiculo":
        raise ValueError("v1 só atende veículo; imóvel nunca entra")
    A, Pmax = pedido.credito_liquido_alvo, pedido.parcela_max
    lim = params.teto_credito(A)
    alertas, excl = [], Counter()
    caps, vistos = {}, {}
    for c in snapshot.cotas:
        a = alerta_sanidade(c)
        if a and a not in alertas:
            alertas.append(a)
        q = min(c.qtd_min, MAX_Q)
        caps[c.cota_id] = min(caps.get(c.cota_id, q), q)
        ref = vistos.setdefault(c.cota_id, c)
        if params.a7_validar_categoria_entre_planos and ref is not c and ref.plano_pct != c.plano_pct:
            if ref.categoria != c.categoria or ref.pct_embutido_max != c.pct_embutido_max:
                alertas.append(f"A7_divergencia cota={c.cota_id} categoria/embutido diferem entre planos")
    grupos, ordem = {}, []
    for c in snapshot.cotas:
        if c.tipo_bem != "veiculo":
            excl["nao_veiculo"] += 1
        elif categoria and c.categoria_veiculo != categoria:
            excl["outra_categoria"] += 1
        elif planos and c.plano_pct not in planos:
            excl["outro_plano"] += 1
        elif c.status != "disponivel":
            excl["saiu_da_venda"] += 1
        elif caps[c.cota_id] <= 0:
            excl["q_zero"] += 1
        elif c.parcela > Pmax:
            excl["parcela_acima_pmax"] += 1
        elif c.credito > lim:
            excl["credito_acima_faixa"] += 1
        else:
            chave = (c.grupo, c.plano_pct, c.credito, c.taxa_pct, c.parcela)
            if chave not in grupos:
                grupos[chave] = []
                ordem.append(chave)
            grupos[chave].append(c)
    tipos = []
    for chave in ordem:
        linhas = grupos[chave]
        c0 = linhas[0]
        flag, N, W, niveis = calcular_niveis(c0, params)
        if flag == "SEM_HISTORICO" and not params.incluir_sem_historico:
            excl["sem_historico"] += 1
            continue
        if not niveis:
            excl["sem_nivel"] += 1
            continue
        tipos.append(Tipo(
            idx=len(tipos), grupo=c0.grupo, serie=c0.serie, plano_pct=c0.plano_pct,
            credito=c0.credito, taxa_pct=c0.taxa_pct, categoria=c0.categoria, parcela=c0.parcela,
            taxa_rs=cent(c0.credito * c0.taxa_pct), teto_emb=c0.pct_embutido_max,
            fontes=tuple(sorted({l.cota_id for l in linhas})), niveis=niveis,
            hist_flag=flag, N=N, W=W, qtd_truncada=any(l.qtd_truncada for l in linhas),
            categoria_veiculo=c0.categoria_veiculo, prazo_total=c0.prazo_total,
            mediana_lance_livre=c0.mediana_lance_livre, data_coleta=c0.data_coleta,
            proxima_assembleia=c0.proxima_assembleia))
    return Universo(tuple(tipos), caps, tuple(alertas), dict(excl))


def nivel_referencia(tipo, w_ref):
    """Função 1: nível livre cujo lance = M_{w_ref} (menor nível mantido com w >= w_ref)."""
    for n in tipo.niveis:
        if n.tipo == "livre" and n.w >= w_ref:
            return n
    return None
