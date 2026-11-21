"""Parâmetros 'legados' dos testes calculados à mão (h/N e teto de 10%). Os padrões novos têm testes próprios."""
from decimal import Decimal

from modelos import Parametros

LEGADO = dict(modo_probabilidade="fracao_h_sobre_N", delta_credito=Decimal("0.10"))


def PP(**kw):
    return Parametros(**{**LEGADO, **kw})
