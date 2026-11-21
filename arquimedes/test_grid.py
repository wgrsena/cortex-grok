import itertools
import os
import random
import time
from datetime import date
from decimal import Decimal

import pytest

from .grid import gerar, main
from .modelos import GrupoArq, ParametrosGrid, carregar_json, grupo_de_dict
from .persist import GravadorMemoria, GravadorSQL
from .ranking import chave, fluxo_pos, simular_carta

AQUI = os.path.dirname(os.path.abspath(__file__))
EXEMPLO = os.path.join(AQUI, "exemplo_top5.json")


def G(grupo, credito, cartas=3, mediana="0.40", emb="0.25", prazo=40, parcela=1500, data="2026-11-26", taxa="0.18"):
    credito = Decimal(credito)
    return GrupoArq(grupo=grupo, categoria=(credito * (1 + Decimal(taxa))).quantize(Decimal("0.01")), cartas=cartas,
                    prazo_restante=prazo, parcela_antes=Decimal(parcela), mediana_lance_livre=Decimal(mediana),
                    pct_embutido=Decimal(emb), proxima_assembleia=date.fromisoformat(data), credito=credito)


def sinteticos(n=70, seed=7):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        out.append(G(f"{3300 + i:06d}", rnd.choice([30000, 40000, 50000, 60000, 70000, 80000, 100000, 120000, 150000]),
                     cartas=rnd.randint(1, 9), mediana=f"{rnd.uniform(0.15, 0.60):.4f}",
                     emb=rnd.choice(["0.10", "0.25"]), prazo=rnd.randint(10, 80), parcela=rnd.randint(500, 3000)))
    return out


# ---------- passo do grid na geração ----------

def test_passo_do_grid_esta_na_geracao():
    p = ParametrosGrid()
    ops, est = gerar(sinteticos(), p, instrumentar=True)
    assert est.alvos_testados == list(p.faixas) == [50000, 80000, 100000, 180000, 200000, 250000]
    assert est.avaliadas == len(est.creditos_avaliados) > 0
    janelas = {p.janela(i) for i in range(len(p.faixas))}
    for alvo, teto, cred, _ in est.creditos_avaliados:
        assert (alvo, teto) in janelas
        assert alvo <= cred < teto                          # nenhum candidato fora da faixa
    # nenhum alvo adjacente (51k, 52k...): os únicos alvos avaliados são as faixas configuradas
    assert {a // 100 for a, _, _, _ in est.creditos_avaliados} <= set(p.faixas)
    # o gerador avalia uma fração pequena do espaço (poda), não todas as combinações
    assert est.nos < 200_000


def test_faixas_nao_se_sobrepoem_e_teto_respeita_proxima():
    p = ParametrosGrid()
    js = [p.janela(i) for i in range(len(p.faixas))]
    for (a1, t1), (a2, _) in zip(js, js[1:]):
        assert a1 < t1 <= a2
    assert p.janela(0) == (5_000_000, 6_250_000)        # 50k..62,5k (tol 25%)
    assert p.janela(4) == (20_000_000, 25_000_000)      # 200k..250k (corta na próxima faixa)


def _brute(grupos, p, faixa_idx):
    """Oráculo: enumera TODOS os multiconjuntos e aplica o mesmo critério (só para instância pequena)."""
    alvo, teto = p.janela(faixa_idx)
    melhor = None
    for qs in itertools.product(*[range(g.cartas + 1) for g in grupos]):
        esc = [(g, q) for g, q in zip(grupos, qs) if q]
        if not esc:
            continue
        cred = sum(int(g.credito * 100) * q for g, q in esc)
        kmin = min(int(g.credito * 100) for g, _ in esc)
        if not (alvo <= cred < teto and cred - kmin < alvo):
            continue
        cat = sum(int(g.categoria * 100) * q for g, q in esc)
        lan = sum(int(g.mediana_lance_livre * g.categoria * 100) * q for g, q in esc)
        emb = sum(int(g.pct_embutido * 10000) * int(g.categoria * 100) * q for g, q in esc)
        canon = tuple(sorted((g.grupo, int(g.credito * 100), q) for g, q in esc))
        ch = chave(lan, cat, emb, min(g.prazo_restante for g, _ in esc), cred - alvo, sum(q for _, q in esc), canon)
        melhor = ch if melhor is None or ch < melhor else melhor
    return melhor


@pytest.mark.parametrize("seed", range(12))
def test_branch_and_bound_igual_forca_bruta(seed):
    rnd = random.Random(seed)
    # sementes ímpares: medianas/prazos empatados de propósito (exercita a poda lexicográfica)
    med = (lambda: rnd.choice(["0.30", "0.40"])) if seed % 2 else (lambda: f"{rnd.uniform(0.2, 0.5):.2f}")
    prz = (lambda: rnd.choice([30, 40])) if seed % 2 else (lambda: rnd.randint(20, 60))
    grupos = [G(f"9{i:03d}", rnd.choice([30000, 40000, 60000, 80000]), cartas=rnd.randint(1, 3),
                mediana=med(), emb=rnd.choice(["0.10", "0.25"]), prazo=prz())
              for i in range(7)]
    p = ParametrosGrid()
    ops, _ = gerar(grupos, p)
    for i, f in enumerate(p.faixas):
        esperado = _brute(grupos, p, i)
        achou = [o for o in ops if o.faixa_alvo == f]
        if esperado is None:
            assert not achou
        else:
            assert len(achou) == 1
            canon = tuple(sorted((c.grupo, int(c.credito * 100), c.qtd) for c in achou[0].cartas))
            assert canon == esperado[-1]


# ---------- dedup ----------

def test_dedup_por_faixa_top1_e_topk():
    ops1, _ = gerar(sinteticos(), ParametrosGrid())
    assert all(sum(1 for o in ops1 if o.faixa_alvo == f) <= 1 for f in ParametrosGrid().faixas)
    p3 = ParametrosGrid(top_k=3)
    ops3, _ = gerar(sinteticos(), p3)
    for f in p3.faixas:
        rs = [o.rank for o in ops3 if o.faixa_alvo == f]
        assert rs == list(range(1, len(rs) + 1)) and len(rs) <= 3
    chaves = [o.chave_cartas for o in ops3]
    assert len(chaves) == len(set(chaves))


def test_multiconjunto_equivalente_nao_duplica():
    a = G("3301", 60000, cartas=2, mediana="0.30")
    a_dup = G("3301", 60000, cartas=2, mediana="0.30")   # mesma carta listada 2x -> 4 cartas, um item só
    b = G("3302", 60000, cartas=2, mediana="0.35")
    ops, est = gerar([a, a_dup, b], ParametrosGrid(faixas=(100000, 180000, 250000), top_k=5), instrumentar=True)
    chaves = [o.chave_cartas for o in ops]
    assert len(chaves) == len(set(chaves))
    canons = [tuple(sorted((c.grupo, c.qtd) for c in o.cartas)) for o in ops]
    assert len(canons) == len(set(canons))
    assert any(c.qtd == 4 for o in ops for c in o.cartas if c.grupo == "3301")   # cartas somadas
    with pytest.raises(ValueError):
        gerar([a, G("3301", 60000, mediana="0.31")], ParametrosGrid())


# ---------- ranking ----------

def test_ranking_desempate_25_antes_de_10_na_mesma_mediana():
    g10 = G("A10", 60000, mediana="0.45", emb="0.10", prazo=70)
    g25 = G("B25", 60000, mediana="0.45", emb="0.25", prazo=30)
    ops, _ = gerar([g10, g25], ParametrosGrid(faixas=(50000,), top_k=2))
    assert [o.cartas[0].grupo for o in ops] == ["B25", "A10"]


def test_ranking_menor_mediana_depois_maior_prazo():
    ops, _ = gerar([G("M50", 60000, mediana="0.50", prazo=80), G("M40", 60000, mediana="0.40", prazo=20),
                    G("M40L", 60000, mediana="0.40", prazo=60)], ParametrosGrid(faixas=(50000,), top_k=3))
    assert [o.cartas[0].grupo for o in ops] == ["M40L", "M40", "M50"]


# ---------- junção entre prazos ----------

def test_juncao_prazos_diferentes_gera_parcelas_pos_separadas():
    g1, _ = carregar_json(EXEMPLO)
    por = {g.grupo: g for g in g1}
    a = GrupoArq(**{**por["3301"].__dict__, "cartas": 1})
    b = GrupoArq(**{**por["3304"].__dict__, "cartas": 1})
    ops, _ = gerar([a, b], ParametrosGrid(faixas=(100000,)))
    (o,) = ops
    assert {c.grupo: c.meses for c in o.cartas} == {"3301": 38, "3304": 40}
    assert o.prazo == 38 and o.proxima_assembleia == date(2026, 11, 12)
    assert o.parcela_pos_total == sum(c.parcela_pos for c in o.cartas)
    fl = fluxo_pos(o.cartas)
    assert [(i, f) for i, f, _ in fl] == [(1, 38), (39, 40)]
    assert fl[0][2] == o.parcela_pos_total and fl[1][2] == o.cartas[[c.grupo for c in o.cartas].index("3304")].parcela_pos


def test_respeita_cartas_disponiveis():
    ops, est = gerar(sinteticos(), ParametrosGrid(top_k=3), instrumentar=True)
    disp = {(g.grupo, g.credito): g.cartas for g in sinteticos()}
    for o in ops:
        for c in o.cartas:
            assert c.qtd <= disp[(c.grupo, c.credito)]
    # uma carta só: 180k inalcançável com 1×60k
    ops, _ = gerar([G("X", 60000, cartas=1)], ParametrosGrid())
    assert [o.faixa_alvo for o in ops] == [50000]


# ---------- fórmula ----------

def test_formula_pos_contemplacao_3301():
    gs, _ = carregar_json(EXEMPLO)
    g = next(x for x in gs if x.grupo == "3301")
    assert g.credito == Decimal("60000.00") and g.mediana_lance_livre == Decimal("0.4556")
    s = simular_carta(g, 1, ParametrosGrid())
    assert s.lance_total == Decimal("32256.48")
    assert s.parcela_paga == Decimal("1921.00")
    assert s.embutido_usado == Decimal("17700.00") and s.recurso_proprio == Decimal("14556.48")
    assert s.parcela_pos == Decimal("963.75")            # (70800 − 32256,48 − 1921) / 38
    s2 = simular_carta(g, 1, ParametrosGrid(descontar_pagas_no_divisor=True))
    assert s2.meses == 37 and s2.parcela_pos == Decimal("989.80")


def test_mediana_percentual_vira_fracao():
    g = grupo_de_dict({"grupo": "1", "categoria": 70800, "taxa_adm": 18, "cartas": 1, "parcela_antes": 1,
                       "mediana_lance_livre": 45.56, "prazo_restante": 10, "pct_embutido": 10})
    assert g.mediana_lance_livre == Decimal("0.4556") and g.pct_embutido == Decimal("0.1")


# ---------- persistência ----------

def test_so_ranqueadas_sao_persistidas():
    ops, est = gerar(sinteticos(), ParametrosGrid(top_k=2))
    gm = GravadorMemoria()
    assert gm.gravar("2026-10-25#1", "2026-10-25", ops) == len(ops)
    assert len(gm.linhas) == len(ops) < est.avaliadas
    assert all(l["rank"] >= 1 for l in gm.linhas)
    assert len({(l["faixa_alvo"], l["rank"]) for l in gm.linhas}) == len(gm.linhas)
    gm.gravar("2026-10-25#1", "2026-10-25", ops[:1])        # regravar a rodada substitui
    assert len(gm.linhas) == 1
    feito = []
    n = GravadorSQL(lambda sql, prm: feito.append((sql, prm))).gravar("r", "2026-10-25", ops)
    assert n == len(ops) and feito[0][0].startswith("delete") and len(feito) == len(ops) + 1


# ---------- escala ----------

def test_escala_70_grupos_6_faixas_menos_de_2s():
    gs = sinteticos(70, seed=11)
    t = time.perf_counter()
    ops, est = gerar(gs, ParametrosGrid())
    dt = time.perf_counter() - t
    print(f"\nESCALA: 70 grupos x 6 faixas em {dt:.3f}s; {est.avaliadas} avaliadas; {est.nos} nós; {est.podas} podas")
    assert dt < 2.0
    assert len(ops) == 6


def test_cli_imprime_so_tabela_ranqueada(capsys):
    assert main(["--entrada", EXEMPLO]) == 0
    out = capsys.readouterr().out
    assert "| 50.000 | 1 | 1×3301" in out and "EXEMPLO SINTÉTICO" in out
    assert out.count("\n| ") == 1 + 6   # cabeçalho + 1 linha por faixa


def test_empate_macico_fica_limitado_e_sinaliza_truncagem():
    rnd = random.Random(5)
    grupos = [G(f"{i}", rnd.choice([30000, 40000, 50000, 60000, 80000]), cartas=rnd.randint(1, 9)) for i in range(70)]
    t = time.perf_counter()
    ops, est = gerar(grupos, ParametrosGrid(max_nos=20_000))
    assert time.perf_counter() - t < 2
    assert est.nos <= 6 * 20_000 and est.truncadas      # melhor achado devolvido, faixa marcada
    assert {o.faixa_alvo for o in ops} == set(ParametrosGrid().faixas)
