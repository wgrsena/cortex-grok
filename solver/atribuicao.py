"""Atribuição de cotas físicas (ids reais) às unidades, respeitando q_π compartilhado
entre planos (seção 4.1). Emparelhamento bipartido com capacidades (caminhos aumentantes)."""


def atribuir(demanda, tipos, caps):
    """demanda: {idx_tipo: n}. Retorna {idx_tipo: [cota_id, ...]} ou None se inviável."""
    ocup, onde = {}, {}

    def tentar(u, vis):
        for cid in tipos[u[0]].fontes:
            if cid in vis:
                continue
            vis.add(cid)
            lista = ocup.setdefault(cid, [])
            if len(lista) < caps[cid]:
                lista.append(u)
                onde[u] = cid
                return True
            for v in list(lista):
                if tentar(v, vis):
                    lista.remove(v)
                    lista.append(u)
                    onde[u] = cid
                    return True
        return False

    for idx in sorted(demanda):
        for k in range(demanda[idx]):
            if not tentar((idx, k), set()):
                return None
    return {idx: [onde[(idx, k)] for k in range(demanda[idx])] for idx in demanda}
