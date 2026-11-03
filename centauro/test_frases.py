import unittest

from frases import frase_sequencia


class TFrases(unittest.TestCase):
    def test_singular_e_plural(self):
        self.assertIn("na última assembleia", frase_sequencia(1))
        self.assertIn("últimas 4 assembleias", frase_sequencia(4))

    def test_nunca_numero_frio(self):
        for w in range(7):
            t = frase_sequencia(w)
            self.assertNotIn("%", t)
            self.assertNotIn("probabilidade", t.lower())

    def test_invalidos(self):
        for w in (-1, 7, 2.5, True, None):
            with self.assertRaises(ValueError):
                frase_sequencia(w)


if __name__ == "__main__":
    unittest.main()
