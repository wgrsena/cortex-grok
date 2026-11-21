"""Serviço FastAPI do solver (ponto 10 do Wagner: highspy num serviço próprio, não numa Edge Function).
Env: DISAL_SOLVER_TOKEN (obrigatório; sem ele o serviço recusa tudo = fecha por padrão),
     DISAL_DADOS_DIR (pasta do job semanal com ATUAL.json e snapshots/; padrão ./fato).
Header de autenticação: X-API-Token. Só lê a tabela fato; nunca consulta o cofre."""
import hmac
import json
import os
import re
from types import SimpleNamespace

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

from contrato import (para_json, parametros_de_dict, pedido_de_dict, saida_funcao1, saida_funcao2,
                      snapshot_de_dict, combo_dict)
from funcao2 import resolver_funcao1, resolver_funcao2
from revalidacao import revalidar

ID_OK = re.compile(r"^[A-Za-z0-9._-]{1,64}$")     # barra path traversal no snapshot_id
_cache = {}                                       # snapshots são imutáveis: cache por id

app = FastAPI(title="Disal solver")


def autenticar(x_api_token: str = Header(default="")):
    esperado = os.environ.get("DISAL_SOLVER_TOKEN", "")
    if not esperado:
        raise HTTPException(503, "serviço sem token configurado")
    if not hmac.compare_digest(x_api_token.encode(), esperado.encode()):
        raise HTTPException(401, "token inválido")


def carregar_snapshot(snapshot_id):
    pasta = os.environ.get("DISAL_DADOS_DIR", "fato")
    if snapshot_id == "atual":
        try:
            with open(os.path.join(pasta, "ATUAL.json"), encoding="utf-8") as f:
                snapshot_id = json.load(f)["snapshot_id"]
        except OSError:
            raise HTTPException(404, "snapshot atual indisponível")
    if not ID_OK.match(snapshot_id):
        raise HTTPException(422, "snapshot_id inválido")
    if snapshot_id not in _cache:
        try:
            with open(os.path.join(pasta, "snapshots", snapshot_id + ".json"), encoding="utf-8") as f:
                _cache[snapshot_id] = snapshot_de_dict(json.load(f))
        except OSError:
            raise HTTPException(404, "snapshot não encontrado")
    return _cache[snapshot_id]


class Req(BaseModel):
    pedido: dict
    snapshot_id: str = "atual"
    parametros: dict = {}
    offset: int = 0


class ReqRevalidar(BaseModel):
    pedido: dict
    principal: list[str]                 # cota_ids do combo escolhido
    reservas: list[list[str]] = []
    snapshot_id: str = "atual"
    parametros: dict = {}


def _json(obj):
    return Response(content=para_json(obj), media_type="application/json")


def _entrada(r):
    try:
        return pedido_de_dict(r.pedido), parametros_de_dict(r.parametros)
    except (KeyError, AttributeError, ValueError, ArithmeticError) as e:
        raise HTTPException(422, f"entrada inválida: {e!r}")


@app.get("/saude")
def saude():
    return {"ok": True}


@app.post("/combinacoes", dependencies=[Depends(autenticar)])      # Função 1
def combinacoes(r: Req):
    pedido, params = _entrada(r)
    snap = carregar_snapshot(r.snapshot_id)
    return _json(saida_funcao1(resolver_funcao1(snap, pedido, params, r.offset), snap, params))


@app.post("/probabilidade", dependencies=[Depends(autenticar)])    # Função 2 (B = 0 -> ramo lance fixo)
def probabilidade(r: Req):
    pedido, params = _entrada(r)
    snap = carregar_snapshot(r.snapshot_id)
    return _json(saida_funcao2(resolver_funcao2(snap, pedido, params), snap, params))


@app.post("/revalidar", dependencies=[Depends(autenticar)])
def revalidar_ep(r: ReqRevalidar):
    pedido, params = _entrada(r)
    snap = carregar_snapshot(r.snapshot_id)
    ref = lambda ids: SimpleNamespace(cota_ids=set(ids))            # noqa: E731  adaptador de ComboRef
    res = revalidar(ref(r.principal), [ref(x) for x in r.reservas], snap, pedido, params)
    c = res["combo"]
    if c is None:
        combo = None
    elif isinstance(c, SimpleNamespace):
        combo = {"cota_ids": sorted(c.cota_ids)}
    elif isinstance(c, dict):
        combo = c
    else:
        combo = combo_dict(c, snap, params)
    return _json({"status": res["status"], "metodo": res["metodo"], "cotas_removidas": res["cotas_removidas"],
                  "combo": combo, "snapshot_id": snap.snapshot_id})
