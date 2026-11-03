"""Monta a chamada de public.rag_buscar. Sem driver: devolve (sql, params) no estilo %s, pronto para psycopg/supabase."""
from decimal import Decimal

SCORE_MIN = 0.75   # TODO Wagner: calibrar com atendimentos reais
LIMITE = 8
MARGEM_CREDITO = Decimal("0.20")   # TODO Wagner: faixa de crédito ao redor do pedido (±20% é placeholder)


def faixa_em_torno(credito, margem=MARGEM_CREDITO):
    c = Decimal(str(credito))
    return c * (1 - margem), c * (1 + margem)


def montar_chamada(embedding, tipo_bem=None, cidade=None, credito=None, score_min=SCORE_MIN, limite=LIMITE):
    if not embedding:
        raise ValueError("embedding vazio")
    if not 0 <= score_min <= 1:
        raise ValueError("score_min deve estar entre 0 e 1")
    if limite < 1:
        raise ValueError("limite deve ser >= 1")
    cmin, cmax = faixa_em_torno(credito) if credito is not None else (None, None)
    vetor = "[" + ",".join(repr(float(x)) for x in embedding) + "]"
    sql = "select id, conteudo, score from public.rag_buscar(%s::vector, %s, %s, %s, %s, %s, %s)"
    return sql, (vetor, tipo_bem, cidade, cmin, cmax, score_min, limite)
