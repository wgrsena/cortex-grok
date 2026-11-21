"""Modelos do grid do Arquimedes.

Unidades (explícitas de propósito):
- dinheiro: Decimal em reais, arredondado ao centavo; internamente o gerador usa inteiros em centavos;
- mediana_lance_livre, pct_embutido, taxa_adm: FRAÇÃO (0,4556 = 45,56%). A mediana é fração da CATEGORIA
  (crédito + taxa), como no solver. Valores > 1 na entrada são lidos como percentual (45,56 -> 0,4556);
- prazos em meses correntes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

CENT = Decimal("0.01")
FAIXAS_PADRAO = (50_000, 80_000, 100_000, 180_000, 200_000, 250_000)
EMBUTIDOS_VALIDOS = (Decimal("0"), Decimal("0.10"), Decimal("0.25"))


def D(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def cent(x) -> Decimal:
    return D(x).quantize(CENT, rounding=ROUND_HALF_UP)


def fracao(x) -> Decimal:
    """Percentual (> 1) vira fração; fração fica como está."""
    v = D(x)
    return v / 100 if v > 1 else v


@dataclass(frozen=True)
class GrupoArq:
    """Um grupo vivo da tabela fato (uma linha por grupo + valor de carta)."""
    grupo: str
    categoria: Decimal              # R$ por carta (crédito + taxa ADM)
    cartas: int                     # cartas disponíveis
    prazo_restante: int             # meses correntes restantes (não data de fundação)
    parcela_antes: Decimal          # R$ por carta, antes da contemplação
    mediana_lance_livre: Decimal    # fração da categoria, últimas 6 assembleias
    pct_embutido: Decimal           # 0, 0,10 ou 0,25
    proxima_assembleia: Optional[date] = None
    tem_lance_fixo: bool = False
    taxa_adm: Optional[Decimal] = None   # fração
    credito: Optional[Decimal] = None    # R$ por carta; se ausente = categoria / (1 + taxa_adm)

    def __post_init__(self):
        if self.credito is None:
            if self.taxa_adm is None:
                raise ValueError(f"grupo {self.grupo}: informe credito ou taxa_adm")
            object.__setattr__(self, "credito", cent(self.categoria / (1 + self.taxa_adm)))
        if self.pct_embutido not in EMBUTIDOS_VALIDOS:
            raise ValueError(f"grupo {self.grupo}: pct_embutido {self.pct_embutido} fora de {{0; 0,10; 0,25}}")
        if not (0 <= self.mediana_lance_livre <= 1):
            raise ValueError(f"grupo {self.grupo}: mediana fora de [0, 1] (fração da categoria)")


@dataclass(frozen=True)
class ParametrosGrid:
    faixas: tuple = FAIXAS_PADRAO               # crédito-alvo em R$ (o passo do grid)
    top_k: int = 1                              # oportunidades por faixa
    tolerancia_pct: Decimal = Decimal("0.25")   # teto da faixa = min(alvo*(1+tol), próxima faixa)
    parcelas_pagas: int = 1                     # contemplação na 1ª assembleia = 1 parcela antes paga
    descontar_pagas_no_divisor: bool = False    # False: divisor = prazo_restante (fórmula literal)
    max_nos: int = 300_000                    # trava de segurança por faixa (empates maciços); não é regra de negócio

    def __post_init__(self):
        fx = tuple(sorted({int(f) for f in self.faixas}))
        if not fx or fx[0] <= 0:
            raise ValueError("faixas devem ser positivas")
        object.__setattr__(self, "faixas", fx)
        if self.top_k < 1:
            raise ValueError("top_k >= 1")

    def janela(self, i: int) -> tuple[int, int]:
        """Janela [alvo, teto) da faixa i, em centavos. Faixas nunca se sobrepõem."""
        alvo = self.faixas[i]
        teto = D(alvo) * (1 + D(self.tolerancia_pct))
        if i + 1 < len(self.faixas):
            teto = min(teto, D(self.faixas[i + 1]))
        return alvo * 100, int(teto * 100)


@dataclass(frozen=True)
class CartaSim:
    """Simulação pós-contemplação de UMA carta (fórmula do Arquimedes)."""
    grupo: str
    qtd: int
    credito: Decimal
    categoria: Decimal
    lance_total: Decimal
    embutido_usado: Decimal
    recurso_proprio: Decimal
    parcela_paga: Decimal
    meses: int
    parcela_pos: Decimal
    proxima_assembleia: Optional[date]

    def as_dict(self) -> dict:
        d = {k: (str(v) if isinstance(v, Decimal) else v) for k, v in self.__dict__.items()}
        d["proxima_assembleia"] = self.proxima_assembleia.isoformat() if self.proxima_assembleia else None
        return d


@dataclass(frozen=True)
class Oportunidade:
    faixa_alvo: int
    rank: int
    cartas: tuple                   # (CartaSim, ...) por grupo, com qtd
    credito_total: Decimal
    categoria_total: Decimal
    mediana_agregada: Decimal       # fração da categoria, ponderada pela categoria
    prazo: int                      # menor prazo restante entre os grupos (pior caso)
    embutido: Decimal               # fração, ponderada pela categoria
    parcela_pos_total: Decimal      # mês 1 (todas as parcelas pós ativas)
    proxima_assembleia: Optional[date]   # a mais cedo = prazo real de venda
    chave_cartas: str = field(default="")

    @property
    def n_cartas(self) -> int:
        return sum(c.qtd for c in self.cartas)


def _data(v):
    return date.fromisoformat(v) if v else None


def grupo_de_dict(d: dict) -> GrupoArq:
    return GrupoArq(
        grupo=str(d["grupo"]),
        categoria=cent(d["categoria"]),
        cartas=int(d["cartas"]),
        prazo_restante=int(d["prazo_restante"]),
        parcela_antes=cent(d["parcela_antes"]),
        mediana_lance_livre=fracao(d["mediana_lance_livre"]),
        pct_embutido=fracao(d["pct_embutido"]),
        proxima_assembleia=_data(d.get("proxima_assembleia")),
        tem_lance_fixo=bool(d.get("tem_lance_fixo", False)),
        taxa_adm=fracao(d["taxa_adm"]) if d.get("taxa_adm") is not None else None,
        credito=cent(d["credito"]) if d.get("credito") is not None else None,
    )


def carregar_json(caminho: str) -> tuple[list[GrupoArq], dict]:
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    return [grupo_de_dict(g) for g in dados["grupos"]], {k: v for k, v in dados.items() if k != "grupos"}
