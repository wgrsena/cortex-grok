"""Persistência fina: recebe SÓ a lista ranqueada e grava na tabela `oportunidades` (migration 0004).

Sem driver de banco aqui (nenhuma dependência nova): quem integrar passa um `executar(sql, params)`
(ex.: psycopg/Supabase) para `GravadorSQL`. Nos testes usa-se `GravadorMemoria`.
"""
from __future__ import annotations

import json
from typing import Callable, Iterable, Protocol

from .modelos import Oportunidade

COLUNAS = ("rodada", "data_coleta", "faixa_alvo", "rank", "chave_cartas", "credito_total", "categoria_total",
           "cartas", "mediana_lance_livre", "prazo_meses", "embutido_pct", "parcela_pos_total", "parcelas_pos",
           "proxima_assembleia")


def linha(o: Oportunidade, rodada: str, data_coleta: str) -> dict:
    if o.rank < 1:
        raise ValueError("só oportunidades ranqueadas são persistidas")
    return {
        "rodada": rodada,
        "data_coleta": data_coleta,
        "faixa_alvo": str(o.faixa_alvo),
        "rank": o.rank,
        "chave_cartas": o.chave_cartas,
        "credito_total": str(o.credito_total),
        "categoria_total": str(o.categoria_total),
        "cartas": json.dumps([{"grupo": c.grupo, "qtd": c.qtd, "credito": str(c.credito)} for c in o.cartas]),
        "mediana_lance_livre": str(o.mediana_agregada),
        "prazo_meses": o.prazo,
        "embutido_pct": str(o.embutido),
        "parcela_pos_total": str(o.parcela_pos_total),
        "parcelas_pos": json.dumps([c.as_dict() for c in o.cartas]),
        "proxima_assembleia": o.proxima_assembleia.isoformat() if o.proxima_assembleia else None,
    }


class Gravador(Protocol):
    def gravar(self, rodada: str, data_coleta: str, ranqueadas: Iterable[Oportunidade]) -> int: ...


class GravadorMemoria:
    def __init__(self):
        self.linhas: list[dict] = []

    def gravar(self, rodada, data_coleta, ranqueadas) -> int:
        novas = [linha(o, rodada, data_coleta) for o in ranqueadas]
        self.linhas = [l for l in self.linhas if l["rodada"] != rodada] + novas   # regravar a rodada substitui
        return len(novas)


class GravadorSQL:
    """Apaga a rodada e insere as ranqueadas (o chamador cuida da transação)."""

    def __init__(self, executar: Callable[[str, dict], object]):
        self.executar = executar

    def gravar(self, rodada, data_coleta, ranqueadas) -> int:
        self.executar("delete from public.oportunidades where rodada = %(rodada)s", {"rodada": rodada})
        cols = ", ".join(COLUNAS)
        vals = ", ".join(f"%({c})s" for c in COLUNAS)
        n = 0
        for o in ranqueadas:
            self.executar(f"insert into public.oportunidades ({cols}) values ({vals})", linha(o, rodada, data_coleta))
            n += 1
        return n
