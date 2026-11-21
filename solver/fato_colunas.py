"""I1 (01/11/2026): mapeamento `fato_cotas.extra` (jsonb) -> 8 colunas tipadas da migration 0005.

Fonte única da regra em Python; a 0005 aplica a MESMA regra em SQL (teste `test_i1_fato_colunas.py` confere).
Nunca levanta erro: valor ausente, de tipo errado ou fora do domínio vira None (NULL no banco).

Regras por coluna:
- status            texto em STATUS_VALIDOS (trim + minúsculas)
- categoria_veiculo texto em CATEGORIAS_VALIDAS (trim + minúsculas)
- qtd_min           inteiro >= 1 (aceita 2, 2.0 ou "2")
- qtd_truncada      booleano JSON ou texto "true"/"false"
- lance_fixo_pct    FRAÇÃO da categoria 0..1 (I2); valor em (1, 100] é percentual e vira /100; fora disso None
- n_ofertantes_fixo_medio  número >= 0
- lance_ref_irmaos  FRAÇÃO da categoria 0..1, mesma conversão do lance_fixo_pct (é lance de referência, nível do solver)
- prazo_total       inteiro >= 1 (meses)
Número: JSON number (não booleano) ou texto que casa NUMERO_RE (ponto decimal). Inteiros limitados a INT_MAX (int4).
"""
import math
import re
from decimal import Decimal, InvalidOperation

COLUNAS_I1 = ("status", "categoria_veiculo", "qtd_min", "qtd_truncada", "lance_fixo_pct",
              "n_ofertantes_fixo_medio", "lance_ref_irmaos", "prazo_total")
STATUS_VALIDOS = ("disponivel", "saiu_da_venda")
CATEGORIAS_VALIDAS = ("carro", "moto", "caminhao")
NUMERO_RE = r"^\s*-?[0-9]+(\.[0-9]+)?\s*$"          # o mesmo literal está na 0005
INT_MAX = 2147483647
_NUM = re.compile(NUMERO_RE)


def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, Decimal)):
        return Decimal(v)
    if isinstance(v, float):
        return None if (math.isnan(v) or math.isinf(v)) else Decimal(str(v))
    if isinstance(v, str) and _NUM.match(v):
        try:
            return Decimal(v.strip())
        except InvalidOperation:  # pragma: no cover (regex já garante)
            return None
    return None


def _fracao(v):
    x = _num(v)
    if x is None or x < 0 or x > 100:
        return None
    return x if x <= 1 else x / 100


def _inteiro(v, minimo=1):
    x = _num(v)
    if x is None or x != x.to_integral_value() or x < minimo or x > INT_MAX:
        return None
    return int(x)


def _bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.strip().lower() in ("true", "false"):
        return v.strip().lower() == "true"
    return None


def _texto(v, validos):
    if isinstance(v, str) and v.strip().lower() in validos:
        return v.strip().lower()
    return None


def colunas_de_extra(extra):
    """dict `extra` -> dict com as 8 colunas tipadas (None quando inválido/ausente). Espelha o UPDATE da 0005."""
    e = extra if isinstance(extra, dict) else {}
    nn = _num(e.get("n_ofertantes_fixo_medio"))
    return {
        "status": _texto(e.get("status"), STATUS_VALIDOS),
        "categoria_veiculo": _texto(e.get("categoria_veiculo"), CATEGORIAS_VALIDAS),
        "qtd_min": _inteiro(e.get("qtd_min")),
        "qtd_truncada": _bool(e.get("qtd_truncada")),
        "lance_fixo_pct": _fracao(e.get("lance_fixo_pct")),
        "n_ofertantes_fixo_medio": nn if nn is not None and nn >= 0 else None,
        "lance_ref_irmaos": _fracao(e.get("lance_ref_irmaos")),
        "prazo_total": _inteiro(e.get("prazo_total")),
    }
