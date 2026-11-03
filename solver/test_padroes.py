"""Decisões do Wagner (26/10/2026): sem teto de sobra de crédito e probabilidade = sequência/6 como padrão."""
import unittest
from decimal import Decimal as Dc
from fractions import Fraction

from dados_sinteticos import cota
from forca_bruta import resolver_forca_bruta
from modelos import Parametros, Pedido, Snapshot
from niveis import construir_universo


class TPadroesNovos(unittest.TestCase):
    def test_padroes(self):
        p = Parametros()
        self.assertIsNone(p.delta_credito)
        self.assertEqual(p.modo_probabilidade, "sequencia_W_sobre_6")
        self.assertEqual(p.teto_credito(Dc("65000")), Dc("Infinity"))
        self.assertEqual(Parametros(delta_credito=Dc("0.10")).teto_credito(Dc("65000")), Dc("71500"))

    def test_sem_teto_devolve_viavel_com_sobra_explicita(self):
        # alvo 65.000, carta de 100.000 (sobra 35.000 > 10%): antes era excluída, agora é viável com a sobra no gap
        c = cota("X", credito="100000", parcela="1000", teto="0", c=("0.10",) * 6)
        ped = Pedido("veiculo", Dc("65000"), Dc("1500"), Dc("50000"))
        uni = construir_universo(Snapshot("s", "t", (c,)), ped, Parametros())
        self.assertEqual(uni.excluidos.get("credito_acima_faixa", 0), 0)
        rk = resolver_forca_bruta(uni, ped, Parametros())["ranking"]
        self.assertEqual(len(rk), 1)
        self.assertEqual(rk[0].gap["sobra_credito"], Dc("35000"))
        self.assertEqual(rk[0].gap["credito"], Dc("0"))
        # com o teto reativado a mesma carta é excluída
        uni2 = construir_universo(Snapshot("s", "t", (c,)), ped, Parametros(delta_credito=Dc("0.10")))
        self.assertEqual(uni2.excluidos["credito_acima_faixa"], 1)

    def test_probabilidade_padrao_e_sequencia_sobre_6(self):
        c = cota("X", credito="70000", parcela="1000", teto="0", c=("0.10", "0.30", "0.30", "0.10", "0.30", "0.30"))
        ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("100000"))
        for modo, esperado in (("sequencia_W_sobre_6", lambda w: Fraction(w, 6)), ("fracao_h_sobre_N", None)):
            uni = construir_universo(Snapshot("s", "t", (c,)), ped, Parametros(modo_probabilidade=modo))
            for n in uni.tipos[0].niveis:
                if n.tipo == "livre" and esperado:
                    self.assertEqual(n.p, esperado(n.w))


if __name__ == "__main__":
    unittest.main()
