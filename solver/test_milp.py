"""Teste de aceite 2 (MILP vs força bruta) + propriedades do MILP e da aproximação (seção 7). Dados SINTÉTICOS."""
import random
import unittest
from decimal import Decimal as Dc
from fractions import Fraction

from dados_sinteticos import cota, snapshot_basico
from forca_bruta import resolver_forca_bruta
from milp import resolver_milp
from modelos import Pedido, Snapshot, MAX_Q
from util_teste import PP
from niveis import construir_universo

EXATO = dict(milp_gap_relativo=0.0, milp_tempo_limite_s=30.0)
P0 = PP(refino_respeita_teto_credito=True, **EXATO)


def instancia(rng):
    n = rng.randint(3, 8)
    cotas = []
    for i in range(n):
        cr = rng.choice([20000, 25000, 30000, 35000, 40000, 50000, 70000])
        c = tuple(None if rng.random() < 0.12 else Dc(str(round(rng.uniform(0.10, 0.45), 2))) for _ in range(6))
        cotas.append(cota(f"S{i}", grupo=f"00{rng.randint(1000, 4999)}", credito=str(cr),
                          taxa=str(round(rng.uniform(0.14, 0.18), 2)), parcela=str(round(cr * rng.uniform(0.011, 0.016))),
                          teto=rng.choice(["0", "0.10", "0.25"]), c=c, qtd=rng.randint(1, 3),
                          fixo=rng.choice([None, "3", "5"]), plano=rng.choice([100, 75])))
    ped = Pedido("veiculo", Dc(rng.choice([60000, 70000, 90000])), Dc(rng.choice([1500, 2500, 3500, 5000])),
                 Dc(rng.choice([5000, 12000, 20000, 30000])))
    return Snapshot("rnd", "t", tuple(cotas)), ped


def assinatura(r):
    return [(c.prob, c.taxa_total) for c in r["ranking"]]


class T2MilpVsForcaBruta(unittest.TestCase):
    def test_instancias_aleatorias_semente_fixa(self):
        rng, comparadas = random.Random(20261026), 0
        for _ in range(24):
            snap, ped = instancia(rng)
            uni = construir_universo(snap, ped, P0)
            if len(uni.tipos) > 8 or not uni.tipos:
                continue
            fb, mi = resolver_forca_bruta(uni, ped, P0), resolver_milp(uni, ped, P0)
            self.assertEqual(bool(fb["ranking"]), bool(mi["ranking"]))
            if fb["ranking"]:
                comparadas += 1
                self.assertEqual(assinatura(fb)[0], assinatura(mi)[0])          # melhor: probabilidade e taxa iguais
                self.assertEqual(assinatura(fb), assinatura(mi))                # e o ranking inteiro
                self.assertEqual(len(fb["descartado_discreto"]), len(mi["descartado_discreto"]))
        self.assertGreaterEqual(comparadas, 6)

    def test_propriedades_na_saida_do_milp(self):
        rng = random.Random(7)
        n = 0
        for _ in range(10):
            snap, ped = instancia(rng)
            uni = construir_universo(snap, ped, P0)
            r = resolver_milp(uni, ped, P0)
            for c in r["ranking"] + r["reservas"]:
                n += 1
                usados = {}
                for x in c.cartas:
                    usados[x.cota_id] = usados.get(x.cota_id, 0) + 1
                    self.assertLessEqual(x.embutido_rs, x.celula.teto_rs)
                    self.assertEqual(x.celula.tipo.grupo[:0], "")
                self.assertTrue(all(q <= min(MAX_Q, uni.caps[k]) for k, q in usados.items()))
                self.assertTrue(c.viavel)
            for res in r["reservas"]:
                self.assertFalse(res.cota_ids & r["ranking"][0].cota_ids)
            for a in range(len(r["reservas"])):
                for b in range(a):
                    self.assertFalse(r["reservas"][a].cota_ids & r["reservas"][b].cota_ids)
        self.assertGreater(n, 5)


class TMilpCasos(unittest.TestCase):
    def test_ranking_calculado_a_mao(self):
        # mesmo caso do teste da força bruta: Y (p=1) depois X (p=1/2)
        x = cota("X", credito="70000", parcela="1000", teto="0", c=("0.10", "0.30"))
        y = cota("Y", grupo="001001", credito="70000", parcela="1000", teto="0.25", c=("0.15",) * 6)
        ped = Pedido("veiculo", Dc("65000"), Dc("1500"), Dc("10000"))
        r = resolver_milp(construir_universo(Snapshot("s", "t", (x, y)), ped, P0), ped, P0)
        self.assertEqual([c.prob for c in r["ranking"]], [Fraction(1), Fraction(1, 2)])
        self.assertEqual(r["ranking"][0].embutido_total, Dc("4060.00"))

    def test_gap_padrao_e_tempo_limite_sao_parametros(self):
        p = PP()
        self.assertEqual((p.milp_gap_relativo, p.milp_tempo_limite_s), (0.005, 10.0))
        snap = snapshot_basico()
        ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("12000"))
        r = resolver_milp(construir_universo(snap, ped, p), ped, p)
        self.assertEqual(r["metodo"], "milp")
        self.assertLessEqual(r["gap_milp"], 0.005 + 1e-9)

    def test_d1_embutido_zero_quando_b_cobre(self):
        c = cota("A", credito="70000", parcela="1000", teto="0.25", c=("0.10",) * 6)
        ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("50000"))
        r = resolver_milp(construir_universo(Snapshot("s", "t", (c,)), ped, P0), ped, P0)
        self.assertEqual(r["ranking"][0].embutido_total, Dc("0"))

    def test_modo_probabilidade_troca_so_p(self):
        c = cota("A", credito="70000", parcela="1000", teto="0.25", c=("0.30", "0.10", None, None, None, None))
        ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("50000"))
        ps = {}
        for modo in ("fracao_h_sobre_N", "sequencia_W_sobre_6"):
            pr = PP(modo_probabilidade=modo, **EXATO)
            r = resolver_milp(construir_universo(Snapshot("s", "t", (c,)), ped, pr), ped, pr)
            ps[modo] = (r["ranking"][0].prob, r["ranking"][0].cartas[0].celula.nivel.lance_pct)
        self.assertEqual(ps["fracao_h_sobre_N"], (Fraction(1), Dc("0.30")))       # w=2, M=0,30 cobre 2 de 2
        self.assertEqual(ps["sequencia_W_sobre_6"], (Fraction(2, 6), Dc("0.30")))  # mesmo lance, só p muda

    def test_sem_solucao_exata_devolve_opcoes_com_gap(self):
        # alvo 70.000: cotas de 30.000 e parcela máxima 1.000: duas cartas = 60.000 (gap de crédito),
        # três cartas = 90.000 > faixa; parcela de cada uma 900.
        cs = tuple(cota(f"Q{i}", grupo=f"00200{i}", credito="30000", parcela="900", teto="0.10",
                        c=("0.10",) * 6, qtd=1) for i in range(3))
        snap = Snapshot("s", "t", cs)
        ped = Pedido("veiculo", Dc("70000"), Dc("1900"), Dc("20000"))
        uni = construir_universo(snap, ped, P0)
        r = resolver_milp(uni, ped, P0, snapshot=snap)
        self.assertEqual(r["ranking"], [])
        ap = r["aproximacao"]
        self.assertEqual(ap["nivel"], "R1")
        foco = {o["foco"]: o["combo"] for o in ap["opcoes"]}
        self.assertLessEqual(len(ap["opcoes"]), 3)
        c = foco["credito"]
        self.assertFalse(c.viavel)
        self.assertEqual(c.gap["parcela"], Dc("0"))
        self.assertGreater(c.gap["credito"], Dc("0"))
        self.assertLess(c.gap["credito"], Dc("70000"))
        # a opção de parcela relaxa parcela (ΣP > Pmax) e fecha crédito: 3 cartas = 90.000 exigiria 90.000>77.000
        for o in ap["opcoes"]:
            self.assertGreaterEqual(o["combo"].gap["credito"], 0)

    def test_r1_relaxa_parcela_quando_pmax_exclui_tudo(self):
        # Pmax abaixo da parcela de qualquer carta: o pré-filtro 4.10 zera o universo; com snapshot, R1 relaxa sP
        c = cota("A", credito="70000", parcela="1000", teto="0.10", c=("0.10",) * 6)
        snap = Snapshot("s", "t", (c,))
        ped = Pedido("veiculo", Dc("70000"), Dc("800"), Dc("20000"))
        uni = construir_universo(snap, ped, P0)
        self.assertEqual(uni.tipos, ())
        r = resolver_milp(uni, ped, P0, snapshot=snap)
        self.assertEqual(r["aproximacao"]["nivel"], "R1")
        o = r["aproximacao"]["opcoes"][0]["combo"]
        self.assertEqual(o.gap["parcela"], Dc("200"))
        self.assertEqual(o.gap["credito"], Dc("0"))

    def test_r2_relaxa_recurso_quando_b_nao_cobre(self):
        # B = 0 e teto de embutido 0: lance 10% de 81.200 = 8.120 sem embutido -> recurso insuficiente
        c = cota("A", credito="70000", parcela="1000", teto="0", c=("0.10",) * 6)
        snap = Snapshot("s", "t", (c,))
        ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("0"))
        r = resolver_milp(construir_universo(snap, ped, P0), ped, P0, snapshot=snap)
        ap = r["aproximacao"]
        self.assertEqual(ap["nivel"], "R2")
        self.assertEqual(ap["opcoes"][0]["foco"], "recurso")
        self.assertEqual(ap["opcoes"][0]["combo"].gap["recurso"], Dc("8120.00"))
        self.assertEqual(ap["opcoes"][0]["combo"].gap["credito"], Dc("0"))


if __name__ == "__main__":
    unittest.main()
