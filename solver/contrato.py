"""Formato de saída da seção 10 como dicts/JSON. Dinheiro como string com 2 casas; p como float de exibição."""
import json
from decimal import Decimal
from fractions import Fraction

from dataclasses import fields

from fato_colunas import COLUNAS_I1, colunas_de_extra
from prazos import extras_oportunidade
from modelos import VERSAO_REGRAS, Cota, Pedido, Parametros, Snapshot, D

OBSERVACAO = "Proposta de unificação de cartas de veículo; não é contemplação."
_DEC = {"credito", "taxa_pct", "parcela", "pct_embutido_max", "lance_fixo_pct", "n_ofertantes_fixo_medio",
        "lance_ref_irmaos", "qtd_fixo_contemplado_mes", "mediana_lance_livre"}


def pedido_de_dict(d) -> Pedido:
    return Pedido(d["tipo_bem"], D(d["credito_liquido_alvo"]), D(d["parcela_max"]), D(d["recurso_proprio"]),
                  d.get("categoria_veiculo"))


def snapshot_de_dict(d) -> Snapshot:
    """Lê o JSON da tabela fato (jobs/resumo_semanal.py). Dinheiro/frações como string."""
    nomes = {f.name for f in fields(Cota)}
    cotas = []
    for r in d["cotas"]:
        if isinstance(r.get("extra"), dict):                    # I1: linha do banco (0005); coluna tipada ausente/NULL
            de_extra = colunas_de_extra(r["extra"])             # cai no `extra` (mesma regra da migration)
            r = {**r, **{k: de_extra[k] for k in COLUNAS_I1 if r.get(k) is None and de_extra[k] is not None}}
        kw = {k: v for k, v in r.items() if k in nomes}          # ignora colunas derivadas (M, p, ...)
        for k in _DEC & kw.keys():
            kw[k] = None if kw[k] is None else D(kw[k])
        kw["c"] = tuple(None if x is None else D(x) for x in kw.get("c", ()))
        if isinstance(kw.get("proxima_assembleia"), list):     # N4: lista de assembleias -> tupla (imutável)
            kw["proxima_assembleia"] = tuple(kw["proxima_assembleia"])
        cotas.append(Cota(**kw))
    return Snapshot(d["snapshot_id"], d["atualizado_em"], tuple(cotas))


def snapshot_para_dict(snap) -> dict:
    def cv(v):
        return str(v) if isinstance(v, Decimal) else v
    cotas = []
    for c in snap.cotas:
        r = {f.name: cv(getattr(c, f.name)) for f in fields(Cota)}
        r["c"] = [cv(x) for x in c.c]
        cotas.append(r)
    return {"snapshot_id": snap.snapshot_id, "atualizado_em": snap.atualizado_em, "cotas": cotas}


def parametros_de_dict(d) -> Parametros:
    base = Parametros()
    kw = {}
    for k, v in (d or {}).items():
        atual = getattr(base, k)       # AttributeError se parâmetro desconhecido
        # delta_credito é Optional[Decimal] (None = sem teto): converte quando vier um valor
        kw[k] = D(v) if (isinstance(atual, Decimal) or (k == "delta_credito" and v is not None)) else v
        if k == "feriados":
            kw[k] = tuple(v or ())                      # JSON manda lista; Parametros é imutável
    return Parametros(**kw)


def _rs(x):
    return str(D(x).quantize(Decimal("0.01")))


def _p(f):
    return None if f is None else float(f)


def carta_dict(c, params=None):
    t, n, cel = c.celula.tipo, c.celula.nivel, c.celula
    flags = [t.hist_flag] if t.hist_flag != "OK" else []
    if n.tipo == "referencia":
        flags.append("lance_referencia_irmaos")
    return {
        "cota_id": c.cota_id, "grupo": t.grupo, "plano": t.plano_pct, "credito": _rs(t.credito),
        "taxa_pct": str(t.taxa_pct), "categoria": _rs(t.categoria), "parcela": _rs(t.parcela),
        "nivel_lance": {"tipo": n.tipo, "w": n.w}, "lance_pct": str(n.lance_pct), "lance_rs": _rs(cel.lance_rs),
        "embutido_pct": str((c.embutido_rs / t.categoria).quantize(Decimal("0.0001"))),
        "embutido_rs": _rs(c.embutido_rs), "recurso_alocado_rs": _rs(c.recurso_alocado_rs),
        "p": _p(n.p), "W": t.W, "W_nivel": n.w, "N": t.N, "flags": flags,
        # saída por cenário (ponto 3): crédito, taxa da série, plano, parcela sobre crédito cheio,
        # lance mínimo que maximiza a cobertura e em quantas das últimas assembleias ele teria ganhado
        "taxa_adm_serie": str(t.taxa_pct), "parcela_pre_contemplacao": _rs(t.parcela),
        "cobertura": None if n.tipo != "livre" else {"ganharia_em": n.h, "de_assembleias": n.N},
        "categoria_veiculo": t.categoria_veiculo, "prazo_total": t.prazo_total,
        **extras_oportunidade(t.mediana_lance_livre, t.teto_emb, t.data_coleta, t.proxima_assembleia, params),
    }


def avisos_de(combo, params, truncado=False):
    cartas = combo.cartas
    av = []
    grupos = [c.celula.tipo.grupo for c in cartas]
    if params.a4_avisar_mesmo_grupo and len(set(grupos)) < len(grupos):
        av.append("mesmo_grupo")
    if any(c.celula.tipo.hist_flag == "SEM_HISTORICO" for c in cartas):
        av.append("sem_historico")
    if any(c.celula.tipo.hist_flag == "PARCIAL" for c in cartas):
        av.append("parcial")
    if any(c.celula.tipo.qtd_truncada for c in cartas):
        av.append("qtd_piso")
    if truncado:
        av.append("truncado")
    return av


def _plano(combo):
    ps = {c.celula.tipo.plano_pct for c in combo.cartas}
    return str(ps.pop()) if len(ps) == 1 else "misto"


def _categoria(combo):
    return combo.cartas[0].celula.tipo.categoria_veiculo if combo.cartas else None


def combo_dict(combo, snapshot, params, truncado=False):
    return {
        "cartas": [carta_dict(c, params) for c in combo.cartas],
        "cenario": {"plano": _plano(combo), "categoria_veiculo": _categoria(combo), "observacao": OBSERVACAO},
        "totais": {"credito_total": _rs(combo.credito_bruto), "credito_liquido": _rs(combo.credito_liquido), "parcela": _rs(combo.parcela_total),
                   "taxa_total": _rs(combo.taxa_total), "recurso_usado": _rs(combo.recurso_usado),
                   "embutido_total": _rs(combo.embutido_total), "W_soma": combo.w_soma},
        "probabilidade_conjunta": _p(combo.prob),
        "gap": {k: _rs(v) for k, v in combo.gap.items()},
        "viavel": combo.viavel, "motivo": combo.motivo,
        "avisos": avisos_de(combo, params, truncado),
        "snapshot_id": snapshot.snapshot_id, "atualizado_em": snapshot.atualizado_em,
        "versao_regras": VERSAO_REGRAS,
    }


def saida_funcao1(res, snapshot, params, universo=None):
    universo = universo or res["universo"]
    comb = [{"sem_embutido": combo_dict(c.sem, snapshot, params, res["truncado"]),
             "com_embutido": combo_dict(c.com, snapshot, params, res["truncado"])} for c in res["combinacoes"]]
    for item, (cat, rot) in zip(comb, res.get("rotulos", [])):
        item["categoria_veiculo"], item["plano_testado"] = cat, rot
    return {"combinacoes": comb, "truncado": res["truncado"], "alertas": list(universo.alertas),
            "excluidos": universo.excluidos, "snapshot_id": snapshot.snapshot_id, "versao_regras": VERSAO_REGRAS}


def _aprox(ap, snapshot, params):
    if not isinstance(ap, dict):
        return ap
    return {"nivel": ap["nivel"], "opcoes": [{"foco": o["foco"], **combo_dict(o["combo"], snapshot, params)}
                                             for o in ap["opcoes"]]}


def saida_fixo(res, snapshot):
    def lin(x):
        return {k: (float(v) if k == "score" else (None if v is None else (str(v) if hasattr(v, "quantize") else v)))
                for k, v in x.items()}
    return {"metodo": "lance_fixo", "mensagem_comparativa": res["mensagem_comparativa"],
            "ranking": [lin(x) for x in res["ranking"]],
            "por_categoria": {c: {"plano_testado": v["plano_testado"], "ranking": [lin(x) for x in v["ranking"]],
                                  "alternativa_100": [lin(x) for x in v["alternativa_100"]]}
                              for c, v in res["por_categoria"].items()},
            "snapshot_id": snapshot.snapshot_id, "atualizado_em": snapshot.atualizado_em, "versao_regras": VERSAO_REGRAS}


def saida_funcao2(res, snapshot, params, universo=None):
    if res["metodo"] == "lance_fixo":
        return saida_fixo(res, snapshot)
    universo = universo or res["universo"]
    alt = res.get("alternativa_100")
    out = {"metodo": res["metodo"], "plano_testado": res.get("plano_testado"),
           "categoria_veiculo": res.get("categoria_veiculo"),
           "ranking": [combo_dict(c, snapshot, params) for c in res["ranking"]],
           "reservas": [combo_dict(c, snapshot, params) for c in res["reservas"]],
           "alternativa_100": None if not alt else {
               "rotulo": "alternativa plano 100%", "ranking": [combo_dict(c, snapshot, params) for c in alt["ranking"]]},
           "descartado_discreto": len(res["descartado_discreto"]),
           "aproximacao": _aprox(res["aproximacao"], snapshot, params),
           "alertas": list(universo.alertas), "excluidos": universo.excluidos,
           "snapshot_id": snapshot.snapshot_id, "atualizado_em": snapshot.atualizado_em, "versao_regras": VERSAO_REGRAS}
    if "por_categoria" in res:
        out["por_categoria"] = {c: saida_funcao2(r, snapshot, params) for c, r in res["por_categoria"].items()}
    return out


def para_json(obj):
    def padrao(o):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, Fraction):
            return float(o)
        raise TypeError(type(o))
    return json.dumps(obj, default=padrao, ensure_ascii=False, indent=2)
