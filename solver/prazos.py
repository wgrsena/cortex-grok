"""Validade do dado e prazo de entrada de cliente novo (v1.1, itens 7, 8 e 9). Funções PURAS: nada lê o relógio
nem feriados codificados; `hoje` e `feriados` entram sempre como parâmetro.
Datas aceitas: date, datetime (usa só a data, sem conversão de fuso) ou string ISO (AAAA-MM-DD ou datetime ISO).
Revisão (N9): na saída por oportunidade (`campos_validade_prazo`/`extras_oportunidade`) data malformada NÃO derruba a
requisição: o campo sai None e o nome do campo entra em `datas_invalidas`. `como_data` continua estrita (erro) para
quem chama direto e quer falhar cedo; `como_data_ou_none` é a versão tolerante."""
from datetime import date, datetime, timedelta
from typing import Optional

from modelos import MAX_DIAS_COLETA

MAX_DIAS_PADRAO = MAX_DIAS_COLETA   # alias mantido por compatibilidade; fonte única em modelos.MAX_DIAS_COLETA (N7)
DIAS_ANTES_PADRAO = 2     # prazo de entrada = 2 dias corridos antes da assembleia (decisão do Wagner)


def como_data(v) -> Optional[date]:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if len(s) == 10:
        return date.fromisoformat(s)
    return datetime.fromisoformat(s).date()


def como_data_ou_none(v) -> tuple:
    """(data, ok). Valor ausente -> (None, True); malformado -> (None, False). Nunca levanta (N9)."""
    try:
        return como_data(v), True
    except (TypeError, ValueError):
        return None, False


def _lista_datas(v) -> tuple:
    """Aceita uma data ou uma lista/tupla de datas (N4). Retorna (datas válidas ordenadas, houve_invalida)."""
    itens = v if isinstance(v, (list, tuple)) else ([] if v is None or v == "" else [v])
    datas, invalida = [], False
    for x in itens:
        d, ok = como_data_ou_none(x)
        invalida |= not ok
        if d is not None:
            datas.append(d)
    return tuple(sorted(set(datas))), invalida


def _conjunto(feriados) -> frozenset:
    return frozenset(como_data(f) for f in (feriados or ()))


def oportunidade_desatualizada(data_coleta, hoje, max_dias: int = MAX_DIAS_PADRAO) -> Optional[bool]:
    """True se data_coleta tem MAIS de max_dias dias (exatamente max_dias = ainda vale). None se faltar data_coleta ou hoje."""
    dc, h = como_data(data_coleta), como_data(hoje)
    if dc is None or h is None:
        return None
    return (h - dc).days > max_dias


def prazo_entrada_cliente_novo(data_proxima_assembleia, feriados=frozenset(), dias_antes: int = DIAS_ANTES_PADRAO) -> date:
    """Último dia para o cliente novo entrar e concorrer: `dias_antes` dias corridos antes da assembleia.
    Se esse dia for sábado, domingo ou feriado, recua até o dia útil anterior (sexta, no fim de semana).
    Interpretação de feriado (recuar) é decisão pendente do Wagner: ver NOTAS_DUVIDAS."""
    nao_uteis = _conjunto(feriados)
    d = como_data(data_proxima_assembleia) - timedelta(days=dias_antes)
    while d.weekday() >= 5 or d in nao_uteis:
        d -= timedelta(days=1)
    return d


def assembleia_aplicavel(hoje, proximas_assembleias, feriados=frozenset()) -> Optional[date]:
    """Primeira assembleia (em ordem de data) cujo prazo de entrada ainda não venceu. Prazo INCLUSIVO: entrar
    exatamente no dia do prazo vale. None se nenhuma da lista servir."""
    h = como_data(hoje)
    for a in sorted(como_data(x) for x in proximas_assembleias):
        if prazo_entrada_cliente_novo(a, feriados) >= h:
            return a
    return None


def embutido_cobre_mediana(mediana, teto_embutido) -> Optional[bool]:
    """Revisão I2 (decisão de engenharia autorizada pelo Wagner, sem mudar regra): ambos em FRAÇÃO da categoria
    (0..1) e comparação `<=`: o embutido que IGUALA a mediana cobre o lance. Mesma regra da view
    `grupos_disal_faixa` (0001/0003). Grupo sem embutido (teto 0) não cobre mediana positiva. None se a mediana
    é desconhecida (nunca zero)."""
    if mediana is None or teto_embutido is None:
        return None
    return bool(mediana <= teto_embutido)


MOTIVO_SEM_PROXIMA = "sem_proxima_assembleia"
MOTIVO_SEM_HOJE = "sem_data_de_referencia_hoje"
MOTIVO_SEM_SEGUINTE = "prazo_vencido_sem_assembleia_seguinte_cadastrada"
MOTIVO_TODAS_VENCIDAS = "prazo_vencido_em_todas_as_assembleias_cadastradas"


def campos_validade_prazo(mediana, teto_embutido, data_coleta, proxima_assembleia, hoje, feriados=(),
                          max_dias: int = MAX_DIAS_COLETA) -> dict:
    """Campos extras da saída por oportunidade (item 9). Dado ausente ou malformado -> None, nunca erro (N9).
    embutido_cobre_mediana: mediana do lance livre do grupo <= teto de embutido (só dado comercial; a mediana
    não entra em probabilidade nem em ranking).
    `proxima_assembleia` aceita uma data ou uma lista de datas (N4): se o prazo da primeira já venceu, usa a próxima
    da lista cujo prazo ainda vale. Com uma única data e prazo vencido, `assembleia_aplicavel` = None e
    `motivo_assembleia_aplicavel` explica (não inventamos a assembleia seguinte)."""
    invalidas = []
    h, ok = como_data_ou_none(hoje)
    if not ok:
        invalidas.append("hoje")
    dc, ok = como_data_ou_none(data_coleta)
    if not ok:
        invalidas.append("data_coleta")
    datas, inval = _lista_datas(proxima_assembleia)
    if inval:
        invalidas.append("proxima_assembleia")
    fer, inval = _lista_datas(tuple(feriados or ()))
    if inval:
        invalidas.append("feriados")
    prox = datas[0] if datas else None
    aplicavel, motivo = None, None
    if prox is None:
        motivo = MOTIVO_SEM_PROXIMA
    elif h is None:
        motivo = MOTIVO_SEM_HOJE
    else:
        aplicavel = assembleia_aplicavel(h, datas, fer)
        if aplicavel is None:
            motivo = MOTIVO_SEM_SEGUINTE if len(datas) == 1 else MOTIVO_TODAS_VENCIDAS
    base_prazo = aplicavel or prox
    prazo = None if base_prazo is None else prazo_entrada_cliente_novo(base_prazo, fer)
    return {
        "mediana_lance_livre": None if mediana is None else str(mediana),
        "embutido_cobre_mediana": embutido_cobre_mediana(mediana, teto_embutido),
        "data_coleta": None if dc is None else dc.isoformat(),
        "desatualizada": oportunidade_desatualizada(dc, h, max_dias),
        "proxima_assembleia": None if prox is None else prox.isoformat(),
        "prazo_entrada": None if prazo is None else prazo.isoformat(),
        "assembleia_aplicavel": None if aplicavel is None else aplicavel.isoformat(),
        "prazo_vencido": None if (prox is None or h is None) else aplicavel is None,
        "motivo_assembleia_aplicavel": motivo,
        "datas_invalidas": invalidas,
    }


def extras_oportunidade(mediana, teto, data_coleta, proxima, params):
    """v1.1 (itens 6, 7, 9): flags de validade e prazo por oportunidade; sem dado/`hoje`, saem None.
    Movida de contrato.py para cá na revisão (N3): é regra de prazo, não formato de saída."""
    return campos_validade_prazo(mediana, teto, data_coleta, proxima, params.hoje if params else None,
                                 params.feriados if params else (),
                                 params.max_dias_coleta if params else MAX_DIAS_COLETA)
