"""Revalidação antes do handoff (seção 10, /revalidar): checa saiu_da_venda.
Cota sumiu -> troca pela reserva disjunta; sem reserva -> recalcula excluindo a cota.
Status: valida | recalculada | invalidada (troca por reserva conta como `recalculada`, metodo="reserva")."""
from dataclasses import replace

from funcao2 import resolver_funcao2


def marcar_saiu_da_venda(snapshot, cota_ids):
    cotas = tuple(replace(c, status="saiu_da_venda") if c.cota_id in cota_ids else c for c in snapshot.cotas)
    return replace(snapshot, cotas=cotas)


def cotas_indisponiveis(combo, snapshot):
    disponiveis = {c.cota_id for c in snapshot.cotas if c.status == "disponivel"}
    return {cid for cid in combo.cota_ids if cid not in disponiveis}


def revalidar(principal, reservas, snapshot_atual, pedido, params, recalcular=None):
    """`recalcular(snapshot, pedido, params)` -> dict com `ranking`/`reservas`; padrão = resolver_funcao2
    (ramo fixo se B = 0; senão MILP com 75% primeiro). Para testes, injetar outro resolvedor."""
    fora = cotas_indisponiveis(principal, snapshot_atual)
    if not fora:
        return {"status": "valida", "combo": principal, "metodo": None, "cotas_removidas": []}
    for r in reservas:
        if not cotas_indisponiveis(r, snapshot_atual) and not (r.cota_ids & fora):
            return {"status": "recalculada", "combo": r, "metodo": "reserva", "cotas_removidas": sorted(fora)}
    res = (recalcular or resolver_funcao2)(snapshot_atual, pedido, params)
    if res["ranking"]:
        return {"status": "recalculada", "combo": res["ranking"][0], "metodo": "recalculo",
                "reservas": res.get("reservas", []), "cotas_removidas": sorted(fora)}
    return {"status": "invalidada", "combo": None, "metodo": "recalculo", "cotas_removidas": sorted(fora)}
