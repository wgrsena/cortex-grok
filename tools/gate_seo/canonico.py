"""Parser do arquivo canônico SEO (Markdown exportado do Google Docs).

Formato esperado de cada requisito (o mesmo do DIARIO_SEO_PITAGORAS, com ID e severidade):

    ### SEO-001 — Título do requisito
    - **Requisito:** ...
    - **Fonte:** ...
    - **Data:** 2026-11-02            (aceita também "Data de descoberta")
    - **Severidade:** bloqueante      (bloqueante | alta | média | baixa | informativa ...)
    - **Status:** ativo               (ativo | envelhecido | substituído)

Aceita as duas grafias de campo que o Google Docs exporta: "- **Campo:** valor" e "- [ ] Campo: valor".
O ID pode vir no título (### SEO-001 ...) ou num campo "ID".
"""
import re
from dataclasses import dataclass, field

RE_ID = re.compile(r"\bSEO-\d{3,}\b")
RE_VERSAO = re.compile(r"Vers[ãa]o:?\**\s*:?\s*(v\d+(?:\.\d+)*)", re.I)
RE_CAMPO = re.compile(r"^\s*[-*]\s*(?:\[[ xX]\]\s*)?(?:\*\*)?([^:*\n]{2,40}?)(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.*)$")

CAMPOS = {
    "id": "id", "requisito": "requisito", "fonte": "fonte", "data": "data", "data de descoberta": "data",
    "severidade": "severidade", "status": "status", "verificação": "verificacao", "verificacao": "verificacao",
}
BLOQUEANTE = {"bloqueante", "blocking", "bloqueia"}


def limpar(s: str) -> str:
    """Remove escapes do export do Google Docs (\\_ \\< \\( ...) e negrito solto."""
    return re.sub(r"\\(.)", r"\1", s).replace("**", "").strip()


@dataclass
class Requisito:
    titulo: str
    id: str = ""
    requisito: str = ""
    fonte: str = ""
    data: str = ""
    severidade: str = ""
    status: str = ""
    verificacao: str = ""
    linha: int = 0

    @property
    def ativo(self) -> bool:
        return self.status.lower().startswith("ativo")

    @property
    def bloqueante(self) -> bool:
        return self.severidade.lower().split(" ")[0].strip(".;,") in BLOQUEANTE

    def faltando(self):
        return [c for c in ("id", "data", "fonte", "severidade", "status") if not getattr(self, c)]


@dataclass
class Canonico:
    versao: str = ""
    requisitos: list = field(default_factory=list)


def parse(texto: str) -> Canonico:
    c = Canonico()
    m = RE_VERSAO.search(limpar(texto[:3000]))
    c.versao = m.group(1) if m else ""
    atual = None
    for i, bruta in enumerate(texto.splitlines(), 1):
        linha = limpar(bruta)
        if bruta.startswith("#"):
            nivel = len(bruta) - len(bruta.lstrip("#"))
            atual = None
            if nivel >= 3:
                atual = Requisito(titulo=linha.lstrip("# ").strip(), linha=i)
                mid = RE_ID.search(atual.titulo)
                atual.id = mid.group(0) if mid else ""
                c.requisitos.append(atual)
            continue
        if atual is None:
            continue
        mc = RE_CAMPO.match(bruta.replace("\\", ""))
        if not mc:
            continue
        chave = CAMPOS.get(limpar(mc.group(1)).lower())
        if chave and not getattr(atual, chave):
            valor = limpar(mc.group(2))
            if chave == "id":
                mid = RE_ID.search(valor)
                valor = mid.group(0) if mid else ""
            setattr(atual, chave, valor)
    # requisito = bloco ### que tem o campo Requisito (exclui blocos de teste/checklist sem requisito)
    c.requisitos = [r for r in c.requisitos if r.requisito or r.id]
    return c
