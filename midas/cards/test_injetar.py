"""python3 midas/cards/test_injetar.py — mesmos números da rota, lacunas honestas, nada interno vaza."""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import injetar  # noqa: E402
from injetar import gerar  # noqa: E402

HOJE = date(2026, 11, 1)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = injetar.injetar(HOJE, [50000, 100000, 200000])
        cls.res, cls.por = gerar.rodar(HOJE)

    def test_igual_ao_card_da_rota(self):
        for c in self.d["cards"]:
            o = self.res["faixas"][c["faixa"]]["ops"][0]
            h = gerar.card(o, 1, c["faixa"], self.por, None, gerar.imagens_faixa(c["faixa"]), self.res)
            for k in ("credito", "parcela", "assembleia"):
                self.assertIn(f">{c[k]['texto']}</dd>", h, (c["faixa"], k))
                self.assertTrue(c[k]["fonte"], (c["faixa"], k))

    def test_valores_da_coleta_25_10(self):
        esperado = {50000: ("R$ 55.000,00", "R$ 2.408,79"), 100000: ("R$ 110.000,00", "R$ 5.472,36"),
                    200000: ("R$ 236.973,00", "R$ 8.958,06")}
        self.assertEqual(self.d["data_coleta"], "2026-10-25")
        for c in self.d["cards"]:
            self.assertEqual((c["credito"]["texto"], c["parcela"]["texto"]), esperado[c["faixa"]])
            self.assertEqual(c["assembleia"]["texto"], "26/11/2026")

    def test_lacunas(self):
        for c in self.d["cards"]:
            for k in ("entrada", "lance"):
                self.assertEqual(c[k]["texto"], "dado não disponível")
                self.assertIsNone(c[k]["fonte"])

    def test_nada_interno(self):
        s = json.dumps(self.d, ensure_ascii=False).lower()
        for proibido in ("mediana", "embutido", "lance_livre", "pct_"):
            self.assertNotIn(proibido, s)

    def test_coleta_vencida_nao_gera(self):
        with self.assertRaises(SystemExit):
            injetar.injetar(date(2026, 11, 3), [50000])


if __name__ == "__main__":
    unittest.main(verbosity=1)
