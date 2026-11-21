"""Coleta real (CSV exportado do Drive) -> GrupoArq do Arquimedes. Nada é inventado aqui.

Mapeamento (decisões em docs/arquitetura-rota-oportunidades.md, seção "Fonte de dados"):
- credito          = coluna `credito` (portal)                              -> PÚBLICO
- taxa_adm         = `pct_taxa_adm` (portal); categoria = crédito × (1 + taxa) (regra Disal: lance sobre a categoria)
- parcela_antes    = `valor_1a_parcela_c_seguro` (portal, COM seguro)        -> PÚBLICO (rotulada assim)
- prazo_restante   = `prazo_cota` (portal)
- cartas           = `cotas_disponiveis` do mesmo grupo/plano/prazo (portal mostra no máx. 15); sem lista -> 1
- mediana_lance_livre = `lance_livre_mediana` (histórico, 6 últimas assembleias) -> SÓ RANKING, nunca publicada
- pct_embutido     = 25% se o grupo teve contemplação por lance fixo nas 6 últimas, senão 10% -> SÓ RANKING
- proxima_assembleia = 1ª data do calendário WebDisal >= data de geração      -> PÚBLICO
"""
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vendor"))
from arquimedes.modelos import GrupoArq, cent, fracao  # noqa: E402


def num(s: str):
    s = (s or "").replace("R$", "").strip()
    if not s:
        return None
    return Decimal(s.replace(".", "").replace(",", "."))


@dataclass
class Item:
    """Uma carta à venda (grupo + plano + prazo + valor), com o que é publicável separado do que não é."""
    rotulo: str                 # identidade no Arquimedes: grupo·plano·prazo
    grupo: str
    plano: str
    plano_codigo: str
    prazo_cota: int
    credito: Decimal
    parcela_1a_c_seguro: Decimal
    taxa_adm_pct: Decimal
    bens: list = field(default_factory=list)
    modo: str = ""
    proxima: date | None = None
    cotas: int = 1
    cotas_fonte: str = ""


def ler_csv(p: Path):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def calendario(dirp: Path, hoje: date) -> dict:
    prox = {}
    for r in ler_csv(dirp / "calendario.csv"):
        d = date.fromisoformat(r["data_assembleia"])
        if d >= hoje and (r["Grupo"] not in prox or d < prox[r["Grupo"]]):
            prox[r["Grupo"]] = d
    return prox


def carregar(dirp: Path, hoje: date):
    """Devolve (grupos para o Arquimedes, itens por rótulo, log de exclusões/decisões)."""
    prox = calendario(dirp, hoje)
    pools = {}
    for r in ler_csv(dirp / "cotas_disponiveis.csv"):
        k = (r["grupo"], r["plano"].split()[0], r["prazo_cota"])
        pools[k] = int(r["qtd_cotas (portal mostra no máx. 15: 15 = 15 ou mais)"])
    log = defaultdict(list)
    itens: dict = {}
    grupos = []
    for r in ler_csv(dirp / "grupos_a_venda.csv"):
        if r["tipo_bem"] != "AUTOMOVEL":
            log["fora: não é automóvel"].append(f"{r['grupo']}@{r['credito']}@{r['plano'][:6]}")
            continue
        med = num(r["lance_livre_mediana"])
        if med is None:
            log["fora: sem mediana de lance livre no histórico"].append(f"{r['grupo']}@{r['credito']}@{r['plano'][:6]}")
            continue
        cod = r["plano"].split()[0]
        rot = f"{r['grupo']}·{cod}·{r['prazo_cota']}"
        cred, parc, tx = num(r["credito"]), num(r["valor_1a_parcela_c_seguro"]), num(r["pct_taxa_adm"])
        if None in (cred, parc, tx):
            log["fora: crédito, parcela ou taxa vazios"].append(rot)
            continue
        chave = (rot, cred)
        if chave in itens:   # mesmo valor de carta para outro modelo: guarda o nome, não duplica a carta
            it = itens[chave]
            if it.parcela_1a_c_seguro != parc:
                log["divergência: mesma carta com parcela diferente (mantida a 1ª)"].append(f"{rot}@{cred}")
            it.bens.append(r["bem"])
            continue
        pk = (r["grupo"], cod, r["prazo_cota"])
        cotas = pools.get(pk)
        it = Item(rot, r["grupo"], r["plano"], cod, int(r["prazo_cota"]), cred, parc, tx, [r["bem"]], r["modo"],
                  prox.get(r["grupo"]), cotas or 1, "cotas_disponiveis" if cotas else "sem lista de cotas: 1 carta")
        if not cotas:
            log["sem lista de cotas (usada 1 carta)"].append(rot)
        if it.proxima is None:
            log["sem assembleia futura no calendário"].append(r["grupo"])
        itens[chave] = it
        fixo = int(r["contemp_6_ult_fixo"] or 0) > 0
        grupos.append(GrupoArq(
            grupo=rot, categoria=cent(cred * (1 + fracao(tx))), cartas=it.cotas, prazo_restante=it.prazo_cota,
            parcela_antes=cent(parc), mediana_lance_livre=fracao(med),
            pct_embutido=Decimal("0.25") if fixo else Decimal("0.10"),
            proxima_assembleia=it.proxima, tem_lance_fixo=fixo, taxa_adm=fracao(tx), credito=cent(cred)))
    return grupos, itens, {k: sorted(set(v)) for k, v in log.items()}
