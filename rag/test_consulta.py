import unittest
from decimal import Decimal as Dc

from consulta import faixa_em_torno, montar_chamada


class TConsulta(unittest.TestCase):
    def test_faixa(self):
        self.assertEqual(faixa_em_torno("70000"), (Dc("56000.00"), Dc("84000.00")))

    def test_chamada_com_filtros(self):
        sql, p = montar_chamada([0.1, 0.2], tipo_bem="veiculo", cidade="Recife", credito="70000")
        self.assertIn("rag_buscar", sql)
        self.assertEqual(sql.count("%s"), len(p))
        self.assertEqual(p[0], "[0.1,0.2]")
        self.assertEqual(p[1:3], ("veiculo", "Recife"))

    def test_sem_filtros_vira_none(self):
        _, p = montar_chamada([0.5])
        self.assertEqual(p[1:5], (None, None, None, None))

    def test_entradas_invalidas(self):
        for kw in ({"embedding": []}, {"embedding": [1], "score_min": 2}, {"embedding": [1], "limite": 0}):
            with self.assertRaises(ValueError):
                montar_chamada(**kw)


if __name__ == "__main__":
    unittest.main()
