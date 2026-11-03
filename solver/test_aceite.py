"""Testes de aceite 1, 3, 4, 5, 7 e força bruta. DADOS SINTÉTICOS (ver dados_sinteticos.py).
Testes 2 (MILP vs força bruta) em test_milp.py; teste 6 (backtest) em test_novos.py."""
import itertools
import unittest
from dataclasses import replace
from decimal import Decimal as Dc
from fractions import Fraction

from contrato import combo_dict, para_json, saida_funcao1, saida_funcao2, parametros_de_dict
from dados_sinteticos import PEDIDO_PADRAO, cota, snapshot_basico
from embutido import J, fazer_celula, montar_combo, opcoes_embutido, refinar
from enumeracao import enumerar, percorrer, unidades_com_ids
from forca_bruta import resolver_forca_bruta
from modelos import Pedido, Snapshot, MAX_Q
from util_teste import PP
from niveis import alerta_sanidade, construir_universo, calcular_niveis
from revalidacao import marcar_saiu_da_venda, revalidar

P = PP()
PD5 = PP(refino_respeita_teto_credito=True)   # ver NOTAS_DUVIDAS D2


class T1Numerico(unittest.TestCase):
    def test_categoria_e_embutido(self):
        c = cota("X", credito="70000", taxa="0.16", teto="0.25")
        self.assertEqual(c.categoria, Dc("81200.00"))
        self.assertEqual(c.pct_embutido_max * c.categoria, Dc("20300.0000"))
        t = construir_universo(Snapshot("s", "t", (c,)), PEDIDO_PADRAO, P).tipos[0]
        self.assertEqual(t.teto_emb * t.categoria, Dc("20300.0000"))
        # com lance de 100% da categoria o embutido máximo por unidade é exatamente 20.300,00
        cel = fazer_celula(t, replace(t.niveis[0], lance_pct=Dc("1")), P)
        self.assertEqual(max(opcoes_embutido(cel)), Dc("20300.00"))

    def test_teto_vem_so_do_flag_nunca_do_numero_do_grupo(self):
        # v1.1: o número do grupo não decide nada. Flag 0,25 vale mesmo num grupo "exceção" (dado, não regra), sem alerta.
        c = cota("X", grupo="004100", teto="0.25")
        self.assertIsNone(alerta_sanidade(c))
        uni = construir_universo(Snapshot("s", "t", (c,)), PEDIDO_PADRAO, P)
        self.assertEqual(uni.tipos[0].teto_emb, Dc("0.25"))
        # flag fora de {0, 10%, 25%} gera alerta, mas vale
        self.assertIn("flag_invalido", alerta_sanidade(cota("W", teto="0.15")))
        self.assertIsNone(alerta_sanidade(cota("Y", grupo="004104", teto="0")))
        self.assertIsNone(alerta_sanidade(cota("Z", grupo="001000", teto="0.10")))


class T3Restricoes(unittest.TestCase):
    def setUp(self):
        self.snap = snapshot_basico()
        self.ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("12000"))
        self.uni = construir_universo(self.snap, self.ped, P)

    def test_imovel_nunca_entra(self):
        self.assertNotIn("IMV", {f for t in self.uni.tipos for f in t.fontes})
        self.assertEqual(self.uni.excluidos["nao_veiculo"], 1)
        with self.assertRaises(ValueError):
            construir_universo(self.snap, Pedido("imovel", Dc(1), Dc(1), Dc(1)), P)

    def _checar(self, combo):
        usados = {}
        for c in combo.cartas:
            usados[c.cota_id] = usados.get(c.cota_id, 0) + 1
            self.assertLessEqual(c.embutido_rs, c.celula.teto_rs)  # por carta, nunca migra
            self.assertLessEqual(c.embutido_rs, c.celula.tipo.teto_emb * c.celula.tipo.categoria)
            self.assertLessEqual(c.embutido_rs, c.celula.lance_rs)
        for cid, n in usados.items():
            self.assertLessEqual(n, min(self.uni.caps[cid], MAX_Q))

    def test_forca_bruta_e_enumeracao_respeitam(self):
        r = resolver_forca_bruta(self.uni, self.ped, PD5)
        self.assertTrue(r["ranking"])
        for c in r["ranking"] + r["reservas"]:
            self._checar(c)
        for comb in enumerar(self.uni, self.ped, P)["combinacoes"]:
            self._checar(comb.sem)
            self._checar(comb.com)

    def test_q_limita_unidades(self):
        # cota com qtd 15 mas tipo precisa >q: q=2 em A -> nunca 3 unidades de A
        snap = Snapshot("s", "t", (cota("A", credito="25000", parcela="300", qtd=2),))
        ped = Pedido("veiculo", Dc("70000"), Dc("5000"), Dc("100000"))
        uni = construir_universo(snap, ped, P)
        for i in percorrer([fazer_celula(uni.tipos[0], uni.tipos[0].niveis[0], P)], uni, ped, P, None, {}):
            self.assertLessEqual(len(i), 2)
        snap2 = Snapshot("s", "t", (cota("A", credito="25000", parcela="300", qtd=40),))
        uni2 = construir_universo(snap2, ped, P)
        self.assertEqual(uni2.caps["A"], 15)

    def test_q_compartilhado_entre_planos(self):
        a100 = cota("A", credito="25000", parcela="400", plano=100, qtd=2)
        a75 = cota("A", credito="25000", parcela="300", plano=75, qtd=2)
        ped = Pedido("veiculo", Dc("70000"), Dc("5000"), Dc("100000"))
        uni = construir_universo(Snapshot("s", "t", (a100, a75)), ped, P)
        self.assertEqual(len(uni.tipos), 2)
        cels = [fazer_celula(t, t.niveis[0], P) for t in uni.tipos]
        for i in percorrer(cels, uni, ped, P, None, {}):
            self.assertLessEqual(len(i), 2)   # 100% + 75% da mesma cota física dividem q=2

    def test_embutido_nao_migra(self):
        # X sem embutido (teto 0) + Y com 25%; lance 20% de 46.000 = 9.200 por carta; B=10.000 -> G=8.400.
        # Só Y pode financiar: X fica em 0 e Y leva todo o embutido (nunca migra), nas duas versões.
        x = cota("X", grupo="004100", credito="40000", taxa="0.15", parcela="500", teto="0", c=("0.20",) * 6)
        y = cota("Y", grupo="003500", credito="40000", taxa="0.15", parcela="500", teto="0.25", c=("0.20",) * 6)
        ped = Pedido("veiculo", Dc("70000"), Dc("2000"), Dc("10000"))
        uni = construir_universo(Snapshot("s", "t", (x, y)), ped, P)
        achados = [c.com for c in enumerar(uni, ped, P)["combinacoes"]
                   if c.com.viavel and {k.cota_id for k in c.com.cartas} == {"X", "Y"}]
        self.assertTrue(achados)
        for v in achados:
            por_id = {c.cota_id: c.embutido_rs for c in v.cartas}
            self.assertEqual(por_id, {"X": Dc("0"), "Y": Dc("8400.00")})
        # com B=0 o G (18.400) excederia o teto de Y (9.200): nenhuma migração para X
        ped0 = Pedido("veiculo", Dc("70000"), Dc("2000"), Dc("0"))
        self.assertFalse([c for c in enumerar(construir_universo(Snapshot("s", "t", (x, y)), ped0, P), ped0, P)
                          ["combinacoes"] if c.com.viavel and c.com.n_cartas == 2])


class T4EmbutidoMinimo(unittest.TestCase):
    def _unidades(self, B):
        t = construir_universo(Snapshot("s", "t", (cota("A", credito="40000", parcela="500", teto="0.25",
                                                        c=("0.20",) * 6, qtd=3),)),
                               Pedido("veiculo", Dc("70000"), Dc("2000"), Dc(B)), P)
        cel = fazer_celula(t.tipos[0], t.tipos[0].niveis[0], P)
        return [(cel, "A"), (cel, "A")], t

    def test_b_cobre_embutido_zero(self):
        und, _ = self._unidades("100000")
        ped = Pedido("veiculo", Dc("70000"), Dc("2000"), Dc("100000"))
        for modo in ("minimo", "dp"):
            self.assertEqual(montar_combo(und, ped, P, modo).embutido_total, 0, modo)

    def test_minimo_necessario(self):
        und, _ = self._unidades("0")
        lance = und[0][0].lance_rs           # 20% de 46.000 = 9.200
        ped = Pedido("veiculo", Dc("70000"), Dc("2000"), Dc("10000"))
        G = 2 * lance - Dc("10000")
        c = montar_combo(und, ped, P, "minimo")
        self.assertEqual(c.embutido_total, G)           # exatamente o necessário (contínuo)
        d = montar_combo(und, ped, P, "dp")
        self.assertGreaterEqual(d.embutido_total, G)
        # DP é ótimo: nenhuma combinação de J com soma >= G é menor
        ops = opcoes_embutido(und[0][0])
        melhor = min(a + b for a in ops for b in ops if a + b >= G)
        self.assertEqual(d.embutido_total, melhor)
        for x in d.cartas:
            self.assertIn(x.embutido_rs / x.celula.tipo.categoria, J)  # pct ∈ J (exato em centavos)

    def test_dp_unidades_identicas_e_inviavel(self):
        self.assertEqual(refinar([[Dc(0), Dc(5)], [Dc(0), Dc(5)]], Dc(11)), None)
        self.assertEqual(sum(refinar([[Dc(0), Dc(5)], [Dc(0), Dc(7)]], Dc(6))), 7)


class T5SemHistorico(unittest.TestCase):
    def setUp(self):
        self.sem = cota("S", grupo="005000", c=(None,) * 6, ref="0.30", fixo=None)
        self.snap = Snapshot("s", "t", (self.sem, cota("OK", c=("0.2",) * 6)))

    def test_fora_do_ranking_por_padrao(self):
        uni = construir_universo(self.snap, PEDIDO_PADRAO, P)
        self.assertNotIn("005000", {t.grupo for t in uni.tipos})
        self.assertEqual(uni.excluidos["sem_historico"], 1)

    def test_incluido_p_nulo_sem_numero_inventado(self):
        p = PP(incluir_sem_historico=True)
        uni = construir_universo(self.snap, PEDIDO_PADRAO, p)
        t = next(t for t in uni.tipos if t.grupo == "005000")
        self.assertEqual(t.hist_flag, "SEM_HISTORICO")
        self.assertEqual(t.N, 0)
        self.assertTrue(all(n.p is None and n.tipo == "referencia" for n in t.niveis))
        c = montar_combo([(fazer_celula(t, t.niveis[0], p), "S")], PEDIDO_PADRAO, p, "sem")
        self.assertIsNone(c.prob)
        d = combo_dict(c, Snapshot("s", "t", ()), p)
        self.assertIsNone(d["probabilidade_conjunta"])
        self.assertIsNone(d["cartas"][0]["p"])
        self.assertIn("SEM_HISTORICO", d["cartas"][0]["flags"])
        self.assertIn("sem_historico", d["avisos"])
        para_json(d)

    def test_parcial_mostra_n(self):
        flag, N, W, niv = calcular_niveis(cota("P", c=("0.2", "0.3", None, None, None, None)), P)
        self.assertEqual((flag, N, W), ("PARCIAL", 2, 2))
        self.assertEqual(niv[-1].p, Fraction(2, 2))


class TNiveis(unittest.TestCase):
    def test_cobertura_temporal_nao_mediana(self):
        # c = 20, 25, 18 -> M1=.20 (h=2: .20,.18), M2=.25 (h=3), M3=.25 (domina w=2)
        flag, N, W, niv = calcular_niveis(cota("N", c=("0.20", "0.25", "0.18", None, None, None)), P)
        self.assertEqual([(n.w, n.lance_pct, n.p) for n in niv], [(1, Dc("0.20"), Fraction(2, 3)),
                                                                  (3, Dc("0.25"), Fraction(1))])

    def test_w_min_e_alternativa_w_sobre_6(self):
        _, _, _, niv = calcular_niveis(cota("N", c=("0.20", "0.25", "0.30", "0.30", "0.31", "0.32")),
                                       PP(w_min=3, modo_probabilidade="sequencia_W_sobre_6"))
        self.assertEqual([(n.w, n.p) for n in niv][0], (4, Fraction(4, 6)))  # M3=M4: mantém w=4
        self.assertTrue(all(n.w >= 3 for n in niv))

    def test_lance_fixo_trava_25_p_um_sobre_ofertantes(self):
        _, _, _, niv = calcular_niveis(cota("F", fixo="4", c=("0.5",) * 6), P)
        f = [n for n in niv if n.tipo == "fixo"][0]
        self.assertEqual((f.lance_pct, f.p), (Dc("0.25"), Fraction(1, 4)))
        _, _, _, niv = calcular_niveis(cota("F", fixo="0.5", c=("0.5",) * 6), P)
        self.assertEqual([n for n in niv if n.tipo == "fixo"][0].p, Fraction(1))  # limitado a [0,1]

    def test_lance_acima_de_100_descartado(self):
        _, _, _, niv = calcular_niveis(cota("X", c=("0.5", "1.2", None, None, None, None)), P)
        self.assertEqual([n.w for n in niv], [1])


class TEnumeracaoFuncao1(unittest.TestCase):
    def test_igual_a_enumeracao_ingenua(self):
        snap = snapshot_basico()
        ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("30000"))
        p = PP(max_cartas_enum=4, max_combos=100000)
        uni = construir_universo(snap, ped, p)
        res = enumerar(uni, ped, p)
        achados = set()
        for c in res["combinacoes"]:
            achados.add(tuple(sorted(x.celula.tipo.idx for x in c.sem.cartas)))
        from enumeracao import celulas_referencia
        cels = celulas_referencia(uni, p)
        ingenuo = set()
        for r in range(1, 5):
            for combo in itertools.combinations_with_replacement(range(len(cels)), r):
                try:
                    und = unidades_com_ids(combo, cels, uni)
                except TypeError:
                    continue
                if montar_combo(und, ped, p, "sem").viavel or montar_combo(und, ped, p, "minimo").viavel:
                    ingenuo.add(tuple(sorted(cels[j].tipo.idx for j in combo)))
        self.assertEqual(achados, ingenuo)
        self.assertTrue(achados)

    def test_truncado_por_max_combos_e_cartas(self):
        snap = snapshot_basico()
        ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("30000"))
        r = enumerar(construir_universo(snap, ped, PP(max_combos=1)), ped, PP(max_combos=1))
        self.assertEqual(len(r["combinacoes"]), 1)
        self.assertTrue(r["truncado"])
        r2 = enumerar(construir_universo(snap, ped, PP(max_cartas_enum=1)), ped, PP(max_cartas_enum=1))
        self.assertTrue(r2["truncado"])    # há combos com mais cartas que o limite
        pag2 = enumerar(construir_universo(snap, ped, PP(max_combos=1)), ped, PP(max_combos=1), offset=1)
        self.assertEqual(len(pag2["combinacoes"]), 1)
        self.assertNotEqual(r["combinacoes"][0], pag2["combinacoes"][0])

    def test_contrato_json(self):
        snap = snapshot_basico()
        ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("30000"))
        uni = construir_universo(snap, ped, P)
        s = para_json(saida_funcao1(enumerar(uni, ped, P), snap, P, uni))
        self.assertIn("versao_regras", s)
        s2 = para_json(saida_funcao2(resolver_forca_bruta(uni, ped, PD5), snap, PD5, uni))
        self.assertIn("probabilidade_conjunta", s2)
        self.assertEqual(parametros_de_dict({"w_min": 2, "delta_credito": "0.05"}).delta_credito, Dc("0.05"))


class TForcaBruta(unittest.TestCase):
    def setUp(self):
        self.snap = snapshot_basico()
        self.ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("12000"))
        self.uni = construir_universo(self.snap, self.ped, P)

    def test_ranking_a2_e_p_produto(self):
        r = resolver_forca_bruta(self.uni, self.ped, PD5)
        rk = r["ranking"]
        self.assertTrue(rk)
        for c in rk:
            esperado = Fraction(1)
            for x in c.cartas:
                esperado *= x.celula.nivel.p
            self.assertEqual(c.prob, esperado)
            self.assertTrue(c.viavel)
        chaves = [(-c.prob, c.taxa_total, c.parcela_total, c.recurso_usado, c.embutido_total, c.n_cartas) for c in rk]
        self.assertEqual(chaves, sorted(chaves))
        tipos = [c.tipos_usados for c in rk]
        self.assertEqual(len(tipos), len(set(tipos)))            # corte de exclusão por conjunto de tipos

    def test_reservas_disjuntas(self):
        r = resolver_forca_bruta(self.uni, self.ped, PD5)
        self.assertTrue(r["reservas"])
        for res in r["reservas"]:
            self.assertFalse(res.cota_ids & r["ranking"][0].cota_ids)

    def test_oraculo_independente_caso_pequeno(self):
        # 1 tipo, 1 nível: A=70000, cota 40000 qtd 3 -> só 2 unidades (liq 80000 sem emb. > 77000 exige embutido)
        c = cota("A", credito="40000", taxa="0.15", parcela="500", teto="0.25", c=("0.20",) * 6, qtd=3)
        ped = Pedido("veiculo", Dc("70000"), Dc("2000"), Dc("100000"))
        uni = construir_universo(Snapshot("s", "t", (c,)), ped, P)
        r = resolver_forca_bruta(uni, ped, P)
        # com B grande, embutido = 0 e líquido = 80000 > 77000 -> inviável por A5; 'descartado_discreto' literal
        # (ver NOTAS_DUVIDAS D2): o contínuo exige embutido >= 3000, o DP (6.3) usa G=0
        self.assertEqual(r["ranking"], [])
        self.assertEqual(len(r["descartado_discreto"]), 1)
        # com a variante D5 ligada: Σe >= 3000 -> DP escolhe 10% (4.600) por unidade? não: soma mínima >= 3000
        rd = resolver_forca_bruta(uni, ped, PD5)
        self.assertEqual(len(rd["ranking"]), 1)
        self.assertEqual(rd["ranking"][0].embutido_total, Dc("4600.00"))     # menor soma em J que cobre 3.000
        self.assertEqual(rd["ranking"][0].credito_liquido, Dc("75400.00"))
        # B = 0: G=18400 = 2·9200; líquido 80000 − 18400 = 61600 < alvo
        ped2 = Pedido("veiculo", Dc("70000"), Dc("2000"), Dc("0"))
        r2 = resolver_forca_bruta(construir_universo(Snapshot("s", "t", (c,)), ped2, P), ped2, P)
        self.assertEqual(r2["ranking"], [])      # líquido 80000 − 18400 = 61600 < 70000 -> inviável

    def test_ranking_calculado_a_mao(self):
        # SINTÉTICO, resultado calculado à mão. A=65.000 (faixa até 71.500), B=10.000, crédito 70.000, Cat 81.200.
        # X: c=(10%,30%) -> nível w=1: lance 10% (8.120), p=1/2; cabe em B -> embutido 0, líquido 70.000.
        #    (nível w=2: lance 30%, p=1, mas o teto de X é 0: 24.360 > B -> inviável)
        # Y: c=15% x6 -> w=6: lance 15% (12.180), p=1; G=2.180 -> DP em J: 5% = 4.060; líquido 65.940; recurso 8.120.
        # Duas cartas estouram a faixa (140.000). Ranking esperado: Y (p=1) depois X (p=1/2).
        x = cota("X", credito="70000", parcela="1000", teto="0", c=("0.10", "0.30"))
        y = cota("Y", grupo="001001", credito="70000", parcela="1000", teto="0.25", c=("0.15",) * 6)
        ped = Pedido("veiculo", Dc("65000"), Dc("1500"), Dc("10000"))
        for params in (P, PD5):
            r = resolver_forca_bruta(construir_universo(Snapshot("s", "t", (x, y)), ped, params), ped, params)
            rk = r["ranking"]
            self.assertEqual([c.cartas[0].celula.tipo.grupo for c in rk], ["001001", "001000"])
            self.assertEqual([c.prob for c in rk], [Fraction(1), Fraction(1, 2)])
            self.assertEqual((rk[0].embutido_total, rk[0].credito_liquido, rk[0].recurso_usado),
                             (Dc("4060.00"), Dc("65940.00"), Dc("8120.00")))
            self.assertEqual((rk[1].embutido_total, rk[1].credito_liquido, rk[1].recurso_usado),
                             (Dc("0"), Dc("70000"), Dc("8120.00")))

    def test_limite_8_tipos(self):
        cotas = tuple(cota(f"C{i}", grupo=f"00{1000 + i}", credito=str(30000 + i), parcela="300", c=("0.2",) * 6)
                      for i in range(9))
        ped = Pedido("veiculo", Dc("70000"), Dc("5000"), Dc("50000"))
        with self.assertRaises(ValueError):
            resolver_forca_bruta(construir_universo(Snapshot("s", "t", cotas), ped, P), ped, P)


class T7Revalidacao(unittest.TestCase):
    def setUp(self):
        self.snap = snapshot_basico()
        self.ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("12000"))
        self.p = PP(K_top=20, n_reservas=2, refino_respeita_teto_credito=True)
        uni = construir_universo(self.snap, self.ped, self.p)
        self.res = resolver_forca_bruta(uni, self.ped, self.p)
        self.princ = self.res["ranking"][0]

    def test_valida(self):
        r = revalidar(self.princ, self.res["reservas"], self.snap, self.ped, self.p)
        self.assertEqual(r["status"], "valida")

    def test_troca_por_reserva_disjunta(self):
        self.assertTrue(self.res["reservas"], "dados sintéticos devem gerar reserva")
        snap2 = marcar_saiu_da_venda(self.snap, {sorted(self.princ.cota_ids)[0]})
        r = revalidar(self.princ, self.res["reservas"], snap2, self.ped, self.p)
        self.assertEqual((r["status"], r["metodo"]), ("recalculada", "reserva"))
        self.assertFalse(r["combo"].cota_ids & set(r["cotas_removidas"]))

    def test_recalculo_sem_reserva(self):
        snap2 = marcar_saiu_da_venda(self.snap, {sorted(self.princ.cota_ids)[0]})
        r = revalidar(self.princ, [], snap2, self.ped, self.p)
        if r["status"] == "recalculada":
            self.assertEqual(r["metodo"], "recalculo")
            self.assertFalse(r["combo"].cota_ids & set(r["cotas_removidas"]))
        else:
            self.assertEqual(r["status"], "invalidada")

    def test_invalidada_quando_nada_sobra(self):
        todas = {c.cota_id for c in self.snap.cotas}
        r = revalidar(self.princ, self.res["reservas"], marcar_saiu_da_venda(self.snap, todas), self.ped, self.p)
        self.assertEqual(r["status"], "invalidada")
        self.assertIsNone(r["combo"])


if __name__ == "__main__":
    unittest.main()
