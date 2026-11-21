"""DADOS SINTÉTICOS — inventados só para testes. Não representam nenhum grupo/cota real Disal."""
from decimal import Decimal as Dc

from modelos import Cota, Pedido, Snapshot

PEDIDO_PADRAO = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("10000"))


def cota(cota_id, grupo="001000", credito="70000", taxa="0.16", parcela="1000", teto="0.10", plano=100,
         c=("0.20", "0.22", "0.18", "0.25", "0.21", "0.19"), qtd=2, fixo=None, ref=None, **kw):
    cc = tuple(None if x is None else Dc(x) for x in c)
    if kw.get("qtd_fixo_contemplado_mes") is not None:
        kw["qtd_fixo_contemplado_mes"] = Dc(kw["qtd_fixo_contemplado_mes"])
    return Cota(cota_id=cota_id, grupo=grupo, serie=grupo[:4], tipo_bem=kw.pop("tipo_bem", "veiculo"),
                plano_pct=plano, credito=Dc(credito), taxa_pct=Dc(taxa), parcela=Dc(parcela),
                pct_embutido_max=Dc(teto), tem_lance_fixo=fixo is not None,
                n_ofertantes_fixo_medio=None if fixo is None else Dc(fixo), qtd_min=qtd, c=cc,
                lance_ref_irmaos=None if ref is None else Dc(ref), **kw)


def snapshot_basico():
    """SINTÉTICO: 6 cotas veículo (+ 1 imóvel que nunca pode entrar)."""
    return Snapshot("sint-1", "2026-10-26T00:00:00Z", (
        cota("A", "001000", "70000", "0.16", "900", "0.10", c=("0.20", "0.20", "0.18", None, "0.25", "0.19")),
        cota("B", "003500", "35000", "0.16", "500", "0.25", c=("0.30", "0.28", "0.31", "0.27", "0.33", "0.29"),
             fixo="4"),
        cota("C", "004100", "40000", "0.15", "560", "0", c=("0.35", "0.30", None, None, None, None), qtd=3),
        cota("D", "002000", "30000", "0.14", "430", "0.10", c=("0.15", "0.12", "0.15", "0.10", "0.14", "0.16"), qtd=15),
        cota("E", "003600", "35000", "0.16", "500", "0.25", c=("0.29", "0.28", "0.30", "0.27", "0.32", "0.29")),
        cota("F", "002100", "30000", "0.14", "430", "0.10", c=("0.14", "0.13", "0.15", "0.11", "0.14", "0.15"), qtd=15),
        cota("IMV", "009000", "70000", "0.16", "700", "0.25", tipo_bem="imovel"),
    ))
