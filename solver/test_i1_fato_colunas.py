"""I1 (01/11/2026): extra (jsonb) -> 8 colunas tipadas da fato_cotas (migration 0005). Dados SINTÉTICOS.
A função Python `fato_colunas.colunas_de_extra` é o espelho da regra SQL da 0005; estes testes fixam a regra
(válido / inválido / ausente) e conferem que o SQL cita as mesmas colunas, chaves, domínios e literais."""
import os
import re
import unittest
from decimal import Decimal as Dc

from contrato import snapshot_de_dict
from fato_colunas import (CATEGORIAS_VALIDAS, COLUNAS_I1, INT_MAX, NUMERO_RE, STATUS_VALIDOS,
                          colunas_de_extra)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_0005 = os.path.join(RAIZ, "supabase", "migrations", "0005_fato_cotas_colunas_i1.sql")

EXTRA_OK = {"status": "disponivel", "categoria_veiculo": "carro", "qtd_min": 2, "qtd_truncada": False,
            "lance_fixo_pct": "0.25", "n_ofertantes_fixo_medio": "3.5", "lance_ref_irmaos": "0.18", "prazo_total": 80,
            "M": ["0.2"], "p": ["1/6"]}


class TMapeamento(unittest.TestCase):
    def test_validos(self):
        self.assertEqual(colunas_de_extra(EXTRA_OK), {
            "status": "disponivel", "categoria_veiculo": "carro", "qtd_min": 2, "qtd_truncada": False,
            "lance_fixo_pct": Dc("0.25"), "n_ofertantes_fixo_medio": Dc("3.5"), "lance_ref_irmaos": Dc("0.18"),
            "prazo_total": 80})

    def test_normalizacoes_validas(self):
        r = colunas_de_extra({"status": " Saiu_Da_Venda ", "categoria_veiculo": "MOTO", "qtd_min": "3",
                              "qtd_truncada": "TRUE", "lance_fixo_pct": 25, "n_ofertantes_fixo_medio": 0,
                              "lance_ref_irmaos": "23.5", "prazo_total": 48.0})
        self.assertEqual(r, {"status": "saiu_da_venda", "categoria_veiculo": "moto", "qtd_min": 3, "qtd_truncada": True,
                             "lance_fixo_pct": Dc("0.25"), "n_ofertantes_fixo_medio": Dc("0"),
                             "lance_ref_irmaos": Dc("0.235"), "prazo_total": 48})

    def test_fracao_limites(self):
        for v, esperado in ((0, Dc(0)), (1, Dc(1)), ("1.0", Dc("1.0")), (100, Dc(1)), ("45.56", Dc("0.4556")),
                            (-0.1, None), (100.01, None), ("1e3", None), ("25%", None), ("0,25", None)):
            self.assertEqual(colunas_de_extra({"lance_fixo_pct": v})["lance_fixo_pct"], esperado, v)

    def test_invalidos_viram_none_sem_erro(self):
        r = colunas_de_extra({"status": "vendida", "categoria_veiculo": "barco", "qtd_min": 0, "qtd_truncada": "sim",
                              "lance_fixo_pct": True, "n_ofertantes_fixo_medio": -1, "lance_ref_irmaos": "abc",
                              "prazo_total": 2.5})
        self.assertEqual(r, dict.fromkeys(COLUNAS_I1))
        r = colunas_de_extra({"status": 1, "categoria_veiculo": None, "qtd_min": True, "qtd_truncada": 1,
                              "lance_fixo_pct": [0.25], "n_ofertantes_fixo_medio": {"x": 1}, "lance_ref_irmaos": float("nan"),
                              "prazo_total": INT_MAX + 1})
        self.assertEqual(r, dict.fromkeys(COLUNAS_I1))

    def test_ausentes_e_extra_invalido(self):
        for extra in ({}, None, [], "texto", {"outra": 1}):
            self.assertEqual(colunas_de_extra(extra), dict.fromkeys(COLUNAS_I1))


class TSqlEspelho(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = open(SQL_0005, encoding="utf-8").read()
        cls.codigo = re.sub(r"--[^\n]*", "", cls.sql)

    def test_cita_as_8_colunas_e_chaves_do_extra(self):
        for col in COLUNAS_I1:
            self.assertRegex(self.codigo, rf"add column if not exists {col}\s", col)
            self.assertIn(f"extra -> '{col}'", self.codigo, col)
            self.assertRegex(self.codigo, rf"\b{col}\s+= coalesce\({col},", col)

    def test_mesmos_literais_e_dominios(self):
        self.assertIn(NUMERO_RE, self.codigo)
        self.assertIn(str(INT_MAX), self.codigo)
        for v in STATUS_VALIDOS + CATEGORIAS_VALIDAS:
            self.assertIn(f"'{v}'", self.codigo)
        self.assertIn("x / 100", self.codigo)
        self.assertIn("x > 100", self.codigo)

    def test_idempotente_e_sem_extra_removido(self):
        self.assertEqual(self.codigo.count("add column if not exists"), 8)
        self.assertNotRegex(self.codigo, r"drop column")
        self.assertEqual(len(re.findall(r"create or replace function public\._i1_", self.codigo)),
                         len(re.findall(r"drop function public\._i1_", self.codigo)))


class TJobEContrato(unittest.TestCase):
    def test_linhas_fato_e_leitura_pelo_extra(self):
        import sys
        sys.path.insert(0, os.path.join(RAIZ, "scrap"))
        from resumo_semanal import linhas_fato_cotas
        import json
        d = json.load(open(os.path.join(RAIZ, "schema", "snapshot.exemplo.json"), encoding="utf-8"))
        original = snapshot_de_dict(d).cotas
        linhas = linhas_fato_cotas(d)
        self.assertEqual(len(linhas), len(d["cotas"]))
        for ln, r in zip(linhas, d["cotas"]):
            for k in COLUNAS_I1:
                self.assertIn(k, ln)
                self.assertEqual(ln["extra"].get(k), r.get(k))          # extra mantido (compatibilidade)
        # leitura do banco: coluna tipada presente
        self.assertEqual(snapshot_de_dict({**d, "cotas": linhas}).cotas, original)
        # leitura do banco antes do backfill: colunas tipadas NULL -> cai no extra
        sem_tipadas = [{**ln, **dict.fromkeys(COLUNAS_I1)} for ln in linhas]
        self.assertEqual(snapshot_de_dict({**d, "cotas": sem_tipadas}).cotas, original)


if __name__ == "__main__":
    unittest.main()
