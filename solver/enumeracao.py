"""Função 1 (seção 8): todas as combinações válidas, sem ranquear. DFS com poda em Python.
`percorrer` é compartilhado com o resolvedor de força bruta (forca_bruta.py)."""
from dataclasses import dataclass

from atribuicao import atribuir
from embutido import fazer_celula, montar_combo
from modelos import D
from niveis import nivel_referencia


def percorrer(celulas, universo, pedido, params, max_cartas, estado):
    """Gera tuplas de índices de células (multiconjuntos, ordem não decrescente).
    Poda (todas monótonas ao adicionar unidades): parcela > Pmax; crédito líquido mínimo possível
    (ΣC − Σteto) > A(1+δ); recurso mínimo possível (Σ(R − teto)) > B; disponibilidade física.
    Premissa da poda: teto_rs < crédito (verdadeiro com ē <= 0,25 e taxa < 3)."""
    A, B, Pmax = pedido.credito_liquido_alvo, pedido.recurso_proprio, pedido.parcela_max
    lim = params.teto_credito(A)
    n = len(celulas)
    demanda = {}

    def passa(j, sP, sNet, sNeed):
        c = celulas[j]
        return (sP + c.tipo.parcela <= Pmax and sNet + c.tipo.credito - c.teto_rs <= lim
                and sNeed + c.lance_rs - c.teto_rs <= B)

    def rec(inicio, escolha, sP, sNet, sNeed):
        if escolha:
            yield tuple(escolha)
        cheio = max_cartas is not None and len(escolha) >= max_cartas
        for j in range(inicio, n):
            if not passa(j, sP, sNet, sNeed):
                continue
            c = celulas[j]
            idx = c.tipo.idx
            demanda[idx] = demanda.get(idx, 0) + 1
            ok = atribuir(demanda, universo.tipos, universo.caps) is not None
            if ok and cheio:
                estado["truncado"] = True         # havia como estender além de max_cartas_enum
            elif ok:
                escolha.append(j)
                yield from rec(j, escolha, sP + c.tipo.parcela, sNet + c.tipo.credito - c.teto_rs,
                               sNeed + c.lance_rs - c.teto_rs)
                escolha.pop()
            demanda[idx] -= 1
            if not demanda[idx]:
                del demanda[idx]
            if cheio and estado.get("truncado"):
                return

    yield from rec(0, [], D(0), D(0), D(0))


def unidades_com_ids(indices, celulas, universo):
    demanda = {}
    for j in indices:
        demanda[celulas[j].tipo.idx] = demanda.get(celulas[j].tipo.idx, 0) + 1
    ids = atribuir(demanda, universo.tipos, universo.caps)
    usados = {}
    saida = []
    for j in indices:
        idx = celulas[j].tipo.idx
        k = usados.get(idx, 0)
        usados[idx] = k + 1
        saida.append((celulas[j], ids[idx][k]))
    return saida


@dataclass(frozen=True)
class Combinacao:
    sem: object      # Combo (versão SEM embutido)
    com: object      # Combo (versão COM embutido mínimo)

    @property
    def viavel(self):
        return self.sem.viavel or self.com.viavel


def celulas_referencia(universo, params):
    cels = []
    for t in universo.tipos:
        n = nivel_referencia(t, params.w_ref_efetivo)
        if n is None:   # SEM_HISTORICO incluído: usa a referência dos irmãos (informativa)
            n = next((x for x in t.niveis if x.tipo == "referencia"), None)
        if n is not None:
            cels.append(fazer_celula(t, n, params))
    return cels


def enumerar(universo, pedido, params, offset=0):
    """Retorna {"combinacoes": [Combinacao], "truncado": bool}. Paginação: `offset` e `max_combos`.
    Cada combinação traz as duas versões; entra se pelo menos uma é viável."""
    cels = celulas_referencia(universo, params)
    estado = {"truncado": False}
    saida, vistos, mais = [], 0, False
    for indices in percorrer(cels, universo, pedido, params, params.max_cartas_enum, estado):
        und = unidades_com_ids(indices, cels, universo)
        comb = Combinacao(montar_combo(und, pedido, params, "sem"), montar_combo(und, pedido, params, "minimo"))
        if not comb.viavel:
            continue
        vistos += 1
        if vistos <= offset:
            continue
        if len(saida) >= params.max_combos:
            mais = True
            break
        saida.append(comb)
    return {"combinacoes": saida, "truncado": mais or estado["truncado"]}
