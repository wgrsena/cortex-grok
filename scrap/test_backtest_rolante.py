"""Testes do backtest rolante (scrap/backtest_rolante.py). Dados SINTÉTICOS, rotulados; nunca dado real."""
import csv
import os
import sqlite3
import stat
import tempfile
import unittest
from datetime import date
from decimal import Decimal as Dc
from fractions import Fraction

import backtest_rolante as br


def linha(g, d, tipo, pct=""):
    """SINTÉTICO no esquema real do WebDisal (lance_percentual em %, vírgula decimal)."""
    t = {"livre": "LANCE LIVRE", "fixo": "LANCE FIXO", "sorteio": "SORTEIO"}[tipo]
    return {"grupo": g, "data_assembleia": d, "tipo_contemplacao": t, "lance_percentual": pct}


def mes(i):
    return date(2024 + (i - 1) // 12, (i - 1) % 12 + 1, 15).isoformat()


def grupo_constante(g, pcts, inicio=1):
    rows = []
    for k, p in enumerate(pcts):
        rows += [linha(g, mes(inicio + k), "livre", p), linha(g, mes(inicio + k), "sorteio")]
    return rows


class TBacktestRolante(unittest.TestCase):
    def test_percentual_webdisal_vira_fracao_exata(self):
        n = br.normalizar([linha("3163", "2026-10-22", "livre", "7,4328"), linha("3163", "2026-10-22", "livre", "0,9375")])
        self.assertEqual([x[3] for x in n], [Dc("0.074328"), Dc("0.009375")])   # 0,9375% NÃO vira 93,75%
        self.assertEqual(n[0][0], "003163")

    def test_sequencia_sobre_6_vem_do_resolvedor(self):
        c = (Dc("0.30"), Dc("0.20"), Dc("0.25"), None, Dc("0.10"), Dc("0.10"))
        p = br.prever_sequencia(c)
        self.assertEqual((p["w"], p["lance"], p["p"]), (3, Dc("0.30"), Fraction(3, 6)))
        self.assertIsNone(br.prever_sequencia((Dc("0.3"), None, Dc("0.2"))))      # W = 1 < 2: sem previsão
        six = br.prever_sequencia((Dc("0.1"),) * 6)
        self.assertEqual(six["p"], 1)

    def test_empate_conta_como_contemplacao(self):
        """Decisão Wagner 01/11: empate = contemplação. Inclusivo e em Decimal exato."""
        self.assertTrue(br.cobre(Dc("0.074328"), Dc("0.074328")))
        self.assertFalse(br.cobre(Dc("0.074327"), Dc("0.074328")))
        self.assertIsNone(br.cobre(Dc("0.5"), None))
        # 7,4328% lido de texto: em float 7.4328/100 != 0.074328 em alguns casos; em Decimal o empate é exato
        a = br._pct_para_fracao("7,4328")
        b = br._pct_para_fracao("7.4328")
        self.assertTrue(br.cobre(a, b) and br.cobre(b, a))
        self.assertTrue(br.cobre(br._pct_para_fracao("33,3300"), br._pct_para_fracao("33,33")))

    def test_empate_exato_no_backtest_e_acerto(self):
        rows = grupo_constante("001000", ["20,0000"] * 6 + ["20,00"])            # alvo empata com o lance previsto
        res = br.backtest(br.normalizar(rows), datas=[date(2024, 7, 1)])
        e = res["evidencias"][0]
        self.assertEqual((e["w_previsto"], e["empate"], e["acerto"]), (6, True, True))
        self.assertEqual(res["geral"]["taxa_acerto"], 1.0)

    def test_sem_look_ahead(self):
        base = grupo_constante("001000", ["10", "12", "11", "13", "10", "12", "11", "40", "9"])
        D = date(2024, 7, 1)
        r1 = br.backtest(br.normalizar(base), datas=[D])["evidencias"][0]
        futuro_mexido = [dict(r, lance_percentual="99") if r["data_assembleia"] > mes(7) and r["lance_percentual"] else r
                         for r in base]
        r2 = br.backtest(br.normalizar(futuro_mexido), datas=[D])["evidencias"][0]
        for k in ("w_previsto", "lance_previsto_pct", "assembleias_entrada", "menores_livres_entrada_pct"):
            self.assertEqual(r1[k], r2[k])                                          # entrada idêntica
        self.assertTrue(all(x < D.isoformat() for x in r1["assembleias_entrada"].split(";")))
        self.assertEqual(r1["assembleia_alvo"], mes(7))                             # alvo é >= D

    def test_filtro_grupos_existentes_em_D(self):
        rows = grupo_constante("001000", ["10"] * 10) + grupo_constante("002000", ["10"] * 4, inicio=7)
        asm = br.assembleias(br.normalizar(rows))
        self.assertEqual(br.grupos_existentes(asm, date(2024, 7, 1)), ["001000"])   # 002000 criado em jul/24
        self.assertEqual(br.grupos_existentes(asm, date(2024, 8, 1)), ["001000", "002000"])
        ativos = {"001000": (None, date(2024, 6, 30))}
        self.assertEqual(br.grupos_existentes(asm, date(2024, 7, 1), ativos), [])   # inativo em D
        res = br.backtest(br.normalizar(rows), datas=[date(2024, 7, 1)])
        self.assertEqual({e["grupo"] for e in res["evidencias"]}, {"001000"})

    def test_taxa_por_grupo_e_mediana_so_desempata(self):
        rows = grupo_constante("001000", ["10"] * 6 + ["10", "50"]) + grupo_constante("002000", ["30"] * 6 + ["30", "50"])
        res = br.backtest(br.normalizar(rows), datas=[date(2024, 7, 1), date(2024, 8, 1)])
        pg = {t["grupo"]: t for t in res["por_grupo"]}
        self.assertEqual((pg["001000"]["acertos"], pg["001000"]["n"]), (1, 2))
        self.assertEqual(pg["001000"]["taxa_acerto"], pg["002000"]["taxa_acerto"])
        self.assertEqual([t["grupo"] for t in res["por_grupo"]], ["001000", "002000"])  # empate: menor mediana 1º

    def test_cofre_aberto_so_leitura(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "cofre.sqlite")
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE cofre (grupo, data_assembleia, tipo_contemplacao, lance_percentual)")
            con.execute("INSERT INTO cofre VALUES ('1000','2024-01-15','LANCE LIVRE','10')")
            con.commit()
            con.close()
            self.assertEqual(len(br.abrir_cofre_ro(db)), 1)
            ro = br.conexao_ro(db)
            with self.assertRaises(sqlite3.OperationalError):
                ro.execute("INSERT INTO cofre VALUES ('1','2024-01-01','SORTEIO','')")
            ro.close()
            csvp = os.path.join(d, "cofre.csv")
            with open(csvp, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["grupo", "data_assembleia", "tipo_contemplacao", "lance_percentual"])
                w.writeheader()
                w.writerow(linha("1000", "2024-01-15", "livre", "10"))
            os.chmod(csvp, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            antes = br.sha256(csvp)
            with tempfile.TemporaryDirectory() as out:
                br.main(["--cofre", csvp, "--saida", out, "--sha256", antes])
            self.assertEqual(br.sha256(csvp), antes)                                # cópia intacta
            if os.geteuid() != 0:
                with self.assertRaises(PermissionError):
                    open(csvp, "a")
            with self.assertRaises(SystemExit):
                br.main(["--cofre", csvp, "--sha256", "0" * 64, "--saida", d])

    def test_deterministico(self):
        rows = []
        for i, g in enumerate(("001000", "001001", "003500")):
            rows += grupo_constante(g, [str(10 + (k * 7 + i * 3) % 9) for k in range(20)])
        a = br.backtest(br.normalizar(rows))
        b = br.backtest(br.normalizar(list(reversed(rows))))
        self.assertEqual(a, b)
        self.assertGreater(a["geral"]["n"], 0)


if __name__ == "__main__":
    unittest.main()
