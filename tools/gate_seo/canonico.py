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
RE_VERSAO = re.compile(r"Vers[ãa]o:?\**\s*:?\s*(v\d+(?:\.\d+)*|\d+(?:\.\d+)+)", re.I)  # "v1.3" ou "1.0.0"
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


# --- Formato "seções numeradas" (docs/CANONICO_SEO.md, v1.0.0) -----------------------------------------
# Cabeçalho:  "Versão 1.0.0 | Data 2026-11-02 | Autor Pitágoras | Aprovação Wagner Sena | Status FONTE DA VERDADE"
# Requisito:  "## 1. REGRA DE EMBALAGEM" + parágrafo(s) até a próxima seção.
# O arquivo não traz ID nem severidade. O ID é derivado mecanicamente do número da seção (CANON-SEO-01…);
# a severidade vem do .meta.json ("severidade_padrao"), nunca do texto. Sem ela, o gate bloqueia (SEM-SEVERIDADE).
RE_SECAO = re.compile(r"^##\s+(\d{1,2})\.\s+(.+?)\s*$")
RE_CAB = re.compile(r"^\s*([A-Za-zÀ-ÿ]+)\s+(.+?)\s*$")


def cabecalho(texto: str) -> dict:
    """Campos do cabeçalho "Chave valor | Chave valor" (primeira linha com "|" antes da 1ª seção)."""
    for linha in texto.splitlines():
        if linha.startswith("## "):
            break
        if "|" in linha:
            out = {}
            for parte in linha.split("|"):
                m = RE_CAB.match(parte)
                if m:
                    out[m.group(1).lower()] = m.group(2)
            return out
    return {}


def parse_secoes(texto: str, prefixo: str = "CANON-SEO", severidade_padrao: str = "", arquivo: str = "") -> Canonico:
    c = Canonico()
    cab = cabecalho(texto)
    m = RE_VERSAO.search(texto[:3000])
    c.versao = m.group(1) if m else ""
    data = cab.get("data", "")
    status_doc = cab.get("status", "")
    fonte = " · ".join(x for x in (arquivo, f"autor {cab['autor']}" if cab.get("autor") else "",
                                    f"aprovação {cab['aprovação']}" if cab.get("aprovação") else "") if x)
    atual = None
    for i, linha in enumerate(texto.splitlines(), 1):
        ms = RE_SECAO.match(linha)
        if ms:
            n = int(ms.group(1))
            atual = Requisito(titulo=f"{n}. {ms.group(2)}", id=f"{prefixo}-{n:02d}", fonte=f"{fonte} · §{n}" if fonte else "",
                              data=data, severidade=severidade_padrao,
                              status="ativo" if "FONTE DA VERDADE" in status_doc.upper() else status_doc.lower(), linha=i)
            c.requisitos.append(atual)
            continue
        if linha.startswith("#"):
            atual = None
            continue
        if atual is not None and linha.strip():
            atual.requisito = (atual.requisito + " " + linha.strip()).strip()
    return c
