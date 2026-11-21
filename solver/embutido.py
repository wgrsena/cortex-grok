"""Embutido: conjunto J, DP de refinamento exato (seção 6.3) e montagem/avaliação de combos."""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Optional

from modelos import D, cent, cent_baixo

J = tuple(D(x) / 100 for x in (0, 5, 10, 15, 20, 25))  # percentuais permitidos: de 5 em 5 (orientação do Wagner: sem 21%)


@dataclass(frozen=True)
class Celula:
    """(tipo, nível) com lance em reais e teto de embutido por unidade já calculados."""
    tipo: object
    nivel: object
    lance_rs: Decimal
    teto_rs: Decimal       # min(ē·Cat, R); 0 se fixo e A3 desligada


def fazer_celula(tipo, nivel, params) -> Celula:
    R = cent(nivel.lance_pct * tipo.categoria)       # lance sobre a CATEGORIA (crédito + taxa)
    if nivel.tipo == "fixo" and not params.a3_fixo_financiavel_por_embutido:
        teto = D(0)
    else:
        teto = min(cent_baixo(tipo.teto_emb * tipo.categoria), R)
    return Celula(tipo, nivel, R, teto)


def opcoes_embutido(cel: Celula):
    """e = pct·Cat com pct ∈ J ∩ [0, ē], e <= R. Sempre inclui 0."""
    ops = {D(0)}
    for pct in J:
        if pct <= cel.tipo.teto_emb:
            e = cent_baixo(pct * cel.tipo.categoria)
            if e <= cel.teto_rs:
                ops.add(e)
    return sorted(ops)


def refinar(opcoes_por_unidade, G: Decimal) -> Optional[list]:
    """DP exata: escolhe e_i minimizando Σe com Σe >= G. None se inviável.
    Estados = somas parciais distintas < G (poucas unidades; unidades idênticas colapsam)."""
    n = len(opcoes_por_unidade)
    if G <= 0:
        return [D(0)] * n
    resto = [D(0)] * (n + 1)
    for i in range(n - 1, -1, -1):
        resto[i] = resto[i + 1] + max(opcoes_por_unidade[i])
    estados = {D(0): ()}
    melhor = None  # (soma, escolhas)
    for i, ops in enumerate(opcoes_por_unidade):
        novo = {}
        for s, esc in estados.items():
            for e in ops:
                t = s + e
                if t + resto[i + 1] < G:
                    continue
                if t >= G:
                    if melhor is None or t < melhor[0]:
                        melhor = (t, esc + (e,) + (D(0),) * (n - i - 1))
                    continue
                if melhor is not None and t >= melhor[0]:
                    continue
                novo.setdefault(t, esc + (e,))
        estados = novo
    return list(melhor[1]) if melhor else None


@dataclass(frozen=True)
class Carta:
    celula: Celula
    cota_id: str
    embutido_rs: Decimal

    @property
    def recurso_alocado_rs(self):
        return self.celula.lance_rs - self.embutido_rs


@dataclass(frozen=True)
class Combo:
    cartas: tuple
    modo: str                  # sem | minimo | continuo | dp
    viavel: bool
    motivo: Optional[str]
    gap: dict                  # {credito, parcela, recurso}

    @property
    def n_cartas(self): return len(self.cartas)
    @property
    def w_soma(self):
        """Soma da sequência seguida W coberta pelo lance de cada carta (fixo conta 0). Desempate (ponto 4)."""
        return sum((c.celula.nivel.w or 0 for c in self.cartas), 0)
    @property
    def credito_bruto(self): return sum((c.celula.tipo.credito for c in self.cartas), D(0))
    @property
    def embutido_total(self): return sum((c.embutido_rs for c in self.cartas), D(0))
    @property
    def credito_liquido(self): return self.credito_bruto - self.embutido_total
    @property
    def parcela_total(self): return sum((c.celula.tipo.parcela for c in self.cartas), D(0))
    @property
    def taxa_total(self): return sum((c.celula.tipo.taxa_rs for c in self.cartas), D(0))
    @property
    def lance_total(self): return sum((c.celula.lance_rs for c in self.cartas), D(0))
    @property
    def recurso_usado(self): return self.lance_total - self.embutido_total
    @property
    def cota_ids(self): return frozenset(c.cota_id for c in self.cartas)
    @property
    def tipos_usados(self): return frozenset(c.celula.tipo.idx for c in self.cartas)

    @property
    def prob(self) -> Optional[Fraction]:
        """Probabilidade conjunta = Π p_i (A4). None se alguma carta não tem p."""
        r = Fraction(1)
        for c in self.cartas:
            if c.celula.nivel.p is None:
                return None
            r *= c.celula.nivel.p
        return r


def montar_combo(unidades, pedido, params, modo, es_dados=None) -> Combo:
    """unidades: [(Celula, cota_id)]. Modos:
    sem      – sem embutido (Função 1, versão SEM);
    minimo   – G = max(0, ΣR−B) distribuído guloso pelo teto de cada carta (Função 1, COM);
    continuo – como minimo, mas também força Σe >= ΣC − A(1+δ) (relaxação contínua do MILP);
    dp       – refinamento discreto em J (seção 6.3);
    dado     – embutido por unidade informado em `es_dados` (usado nas aproximações da seção 7)."""
    A, B, Pmax = pedido.credito_liquido_alvo, pedido.recurso_proprio, pedido.parcela_max
    lim = params.teto_credito(A)
    SC = sum((c.tipo.credito for c, _ in unidades), D(0))
    SR = sum((c.lance_rs for c, _ in unidades), D(0))
    SP = sum((c.tipo.parcela for c, _ in unidades), D(0))
    G = max(D(0), SR - B)
    tetos = [c.teto_rs for c, _ in unidades]
    es, motivo = [D(0)] * len(unidades), None
    if modo in ("minimo", "continuo"):
        alvo = G if modo == "minimo" else max(G, SC - lim, D(0))
        if alvo > sum(tetos, D(0)):
            motivo = "embutido_insuficiente"
        else:
            rem = alvo
            for i, t in enumerate(tetos):
                es[i] = min(t, rem)
                rem -= es[i]
    elif modo == "dp":
        alvo = max(G, SC - lim) if params.refino_respeita_teto_credito else G
        r = refinar([opcoes_embutido(c) for c, _ in unidades], alvo)
        if r is None:
            motivo = "embutido_insuficiente"
        else:
            es = r
    elif modo == "dado":
        es = [D(x) for x in es_dados]
    elif modo != "sem":
        raise ValueError(modo)
    cartas = tuple(Carta(c, cid, e) for (c, cid), e in zip(unidades, es))
    liq = SC - sum(es, D(0))
    recurso = SR - sum(es, D(0))
    if motivo is None:
        if SP > Pmax:
            motivo = "parcela_acima"
        elif recurso > B:
            motivo = "recurso_insuficiente"
        elif liq < A or liq > lim:
            motivo = "descartado_discreto" if modo == "dp" else ("credito_abaixo" if liq < A else "credito_acima")
    gap = {"credito": max(D(0), A - liq), "parcela": max(D(0), SP - Pmax), "recurso": max(D(0), recurso - B),
           "sobra_credito": max(D(0), liq - A)}        # sem teto de sobra: o excesso fica explícito aqui
    return Combo(cartas, modo, motivo is None, motivo, gap)
