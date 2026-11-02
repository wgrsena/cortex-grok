"""Ranking e agregação do Arquimedes (decisões revisáveis em README.md desta pasta).

Ordem (lexicográfica):
  1. menor mediana de lance livre agregada (Σ lance / Σ categoria = média ponderada pela categoria);
  2. na mesma mediana, maior embutido agregado (25% antes de 10%; ponderado pela categoria);
  3. maior prazo (prazo da combinação = MENOR prazo restante entre os grupos, pior caso);
  4. menor excedente de crédito sobre o alvo; 5. menos cartas; 6. chave canônica (determinismo).
"""
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from .modelos import CartaSim, GrupoArq, Oportunidade, ParametrosGrid, cent

Q6 = Decimal("0.000001")


def chave_item(g: GrupoArq) -> tuple:
    """Ordem dos grupos no gerador (a mesma do ranking, por carta isolada)."""
    return (g.mediana_lance_livre, -g.pct_embutido, -g.prazo_restante, g.grupo, g.credito)


def chave(lance_c: int, cat_c: int, emb_w: int, prazo: int, excedente_c: int, n: int, canon: tuple) -> tuple:
    """lance_c/cat_c em centavos; emb_w = Σ pct_embutido(em centésimos de %) × cat_c."""
    return (Fraction(lance_c, cat_c), -Fraction(emb_w, cat_c), -prazo, excedente_c, n, canon)


def simular_carta(g: GrupoArq, qtd: int, p: ParametrosGrid) -> CartaSim:
    """Pós-contemplação por carta: (categoria − lance total − parcela paga) / meses restantes. Seguro à parte."""
    lance = cent(g.mediana_lance_livre * g.categoria)
    emb = cent(min(g.pct_embutido, g.mediana_lance_livre) * g.categoria)
    paga = cent(g.parcela_antes * p.parcelas_pagas)
    meses = g.prazo_restante - (p.parcelas_pagas if p.descontar_pagas_no_divisor else 0)
    pos = cent((g.categoria - lance - paga) / meses)
    return CartaSim(g.grupo, qtd, g.credito, g.categoria, lance, emb, lance - emb, paga, meses, pos,
                    g.proxima_assembleia)


def montar(faixa: int, rank: int, escolha: list, p: ParametrosGrid) -> Oportunidade:
    """escolha = [(GrupoArq, qtd), ...]. Só é chamado para as oportunidades ranqueadas."""
    sims = tuple(simular_carta(g, q, p) for g, q in escolha)
    cat = sum(g.categoria * q for g, q in escolha)
    lance = sum(s.lance_total * s.qtd for s in sims)
    emb = sum(g.pct_embutido * g.categoria * q for g, q in escolha)
    datas = [g.proxima_assembleia for g, _ in escolha if g.proxima_assembleia]
    return Oportunidade(
        faixa_alvo=faixa,
        rank=rank,
        cartas=sims,
        credito_total=sum(g.credito * q for g, q in escolha),
        categoria_total=cat,
        mediana_agregada=(lance / cat).quantize(Q6),
        prazo=min(g.prazo_restante for g, _ in escolha),
        embutido=(emb / cat).quantize(Q6),
        parcela_pos_total=sum(s.parcela_pos * s.qtd for s in sims),
        proxima_assembleia=min(datas) if datas else None,
        chave_cartas=chave_cartas(escolha),
    )


def chave_cartas(escolha) -> str:
    """Identidade do multiconjunto (grupo, valor da carta, qtd), independente da ordem."""
    return "|".join(f"{g.grupo}@{g.credito}x{q}" for g, q in sorted(escolha, key=lambda e: (e[0].grupo, e[0].credito)))


def fluxo_pos(cartas) -> list[tuple[int, int, Decimal]]:
    """Fluxo mensal das parcelas pós separadas: [(mes_ini, mes_fim, valor/mês)]; cada carta paga até zerar."""
    fins = sorted({c.meses for c in cartas})
    out, ini = [], 1
    for fim in fins:
        valor = sum(c.parcela_pos * c.qtd for c in cartas if c.meses >= fim)
        out.append((ini, fim, valor))
        ini = fim + 1
    return out
