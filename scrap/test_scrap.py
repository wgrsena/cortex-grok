"""Testes do job semanal, do cofre e do backtest (scrap/). Dados SINTÉTICOS."""
import json
import os
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from decimal import Decimal as Dc

import backtest
import cofre
import resumo_semanal
from cofre_sintetico import cofre_sintetico
from contrato import snapshot_de_dict, snapshot_para_dict
from dados_sinteticos import cota
from modelos import Snapshot
from util_teste import PP


class TScrap(unittest.TestCase):
    def test_roundtrip_do_snapshot(self):
        s = Snapshot("s1", "t", (cota("A", "001000", fixo="4", qtd_fixo_contemplado_mes="2.50", prazo_total=60),))
        s2 = snapshot_de_dict(json.loads(json.dumps(snapshot_para_dict(s))))
        self.assertEqual(s2, s)

    def test_job_filtra_ativos_calcula_estatisticas_e_troca_ponteiro(self):
        rows = cofre_sintetico(3, ("001000", "001001", "009999"), 8)
        ativos = {"001000": (None, None), "001001": (None, None)}                 # 009999 não está ativo
        catalogo = [{"cota_id": "A", "grupo": "001000", "serie": "0010", "tipo_bem": "veiculo", "plano_pct": 100,
                     "credito": "70000", "taxa_pct": "0.16", "parcela": "1000", "pct_embutido_max": "0.10",
                     "tem_lance_fixo": True},
                    {"cota_id": "Z", "grupo": "009999", "serie": "0099", "tipo_bem": "veiculo", "plano_pct": 100,
                     "credito": "70000", "taxa_pct": "0.16", "parcela": "1000", "pct_embutido_max": "0.10"}]
        d = resumo_semanal.gerar_snapshot(rows, ativos, catalogo)
        self.assertEqual([c["cota_id"] for c in d["cotas"]], ["A"])
        a = d["cotas"][0]
        asm = cofre.assembleias([r for r in rows if r["grupo"] == "001000"])["001000"]
        self.assertEqual(a["c"][0], str(asm[-1]["menor_livre"]))                    # c1 = assembleia mais recente
        esperado = Dc(sum(x["n_fixo"] for x in asm[-6:])) / 6
        self.assertEqual(Dc(a["qtd_fixo_contemplado_mes"]), esperado.quantize(Dc("0.01")))
        self.assertEqual(len(a["M"]), 6)
        with tempfile.TemporaryDirectory() as t:
            resumo_semanal.gravar(d, t)
            with open(os.path.join(t, "ATUAL.json")) as f:
                self.assertEqual(json.load(f)["snapshot_id"], d["snapshot_id"])
            self.assertFalse([n for n in os.listdir(t) if n.endswith(".tmp")])
            self.assertTrue(os.path.exists(os.path.join(t, "snapshots", d["snapshot_id"] + ".json")))
        snapshot_de_dict(d)                                                         # o solver consegue ler

    def test_job_v1_1_mediana_data_coleta_e_proxima_assembleia(self):
        # SINTÉTICO: grupo com lances livres conhecidos nas 2 assembleias
        rows = [{"grupo": "001000", "data_assembleia": "2026-09-15", "tipo": "livre", "lance_pct": "0.10"},
                {"grupo": "001000", "data_assembleia": "2026-09-15", "tipo": "livre", "lance_pct": "0.20"},
                {"grupo": "001000", "data_assembleia": "2026-10-15", "tipo": "livre", "lance_pct": "0.30"}]
        base = {"serie": "0010", "tipo_bem": "veiculo", "plano_pct": 100, "credito": "70000", "taxa_pct": "0.16",
                "parcela": "1000", "pct_embutido_max": "0.10"}
        cat = [{**base, "cota_id": "A", "grupo": "001000", "proxima_assembleia": "2026-11-16"},
               {**base, "cota_id": "B", "grupo": "001000", "data_coleta": "2026-10-20"}]
        d = resumo_semanal.gerar_snapshot(rows, {"001000": (None, None)}, cat, agora=datetime(2026, 10, 27, 6, 0, tzinfo=timezone.utc))
        a, b = d["cotas"]
        self.assertEqual(a["mediana_lance_livre"], "0.2000")                 # mediana de {0,10; 0,20; 0,30}
        self.assertEqual(a["data_coleta"], "2026-10-27")                     # padrão: data da execução do job
        self.assertEqual(b["data_coleta"], "2026-10-20")                     # catálogo manda quando informa
        self.assertEqual(a["proxima_assembleia"], "2026-11-16")
        self.assertIsNone(b["proxima_assembleia"])
        s = snapshot_de_dict(d)                                              # o solver lê os campos novos
        self.assertEqual(s.cotas[0].mediana_lance_livre, Dc("0.2000"))
        # grupo sem nenhum lance livre: mediana desconhecida (None), nunca zero
        d2 = resumo_semanal.gerar_snapshot([], {"001000": (None, None)}, cat)
        self.assertIsNone(d2["cotas"][0]["mediana_lance_livre"])

    def test_backtest_deterministico_dois_modos(self):
        rows = [{"grupo": "001000", "data_assembleia": date(2024 + t // 12, t % 12 + 1, 1).isoformat(), "tipo": "livre",
                 "lance_pct": "0.15"} for t in range(12)]
        res = backtest.backtest(rows)
        self.assertEqual(res["fracao_h_sobre_N"]["brier"], 0.0)        # sempre ganha e p = h/N = 1
        self.assertGreater(res["sequencia_W_sobre_6"]["brier"], 0.0)   # W/6 < 1 enquanto o histórico é curto

    def test_backtest_sintetico_calibracao_razoavel(self):
        res = backtest.backtest(cofre_sintetico(5, n_assembleias=40))
        r = res["fracao_h_sobre_N"]
        self.assertGreater(r["n"], 100)
        self.assertLess(abs(r["p_medio"] - r["y_medio"]), 0.15)
        self.assertLess(r["brier"], 0.25)
        self.assertTrue(r["calibracao"])

    def test_backtest_rolante_so_usa_grupos_ativos_na_data(self):
        rows = cofre_sintetico(2, ("001000", "001001"), 20)
        todos = backtest.pares(rows, None, PP())
        so_um = backtest.pares(rows, {"001000": (None, None)}, PP())
        self.assertTrue(so_um and all(g == "001000" for *_, g in so_um))
        self.assertLess(len(so_um), len(todos))
        # grupo ativo só a partir de 2025-01: nenhuma assembleia anterior entra
        a = cofre.assembleias(rows, {"001000": (date(2025, 1, 1), None)})["001000"]
        self.assertTrue(all(x["data"] >= date(2025, 1, 1) for x in a))

    def test_leitor_xlsx_stdlib(self):
        with tempfile.TemporaryDirectory() as t:
            f = os.path.join(t, "c.xlsx")
            with zipfile.ZipFile(f, "w") as z:
                z.writestr("xl/sharedStrings.xml", '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                           '<si><t>grupo</t></si><si><t>tipo</t></si><si><t>livre</t></si></sst>')
                z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                           '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
                           '<row r="2"><c r="A2"><v>1000</v></c><c r="B2" t="s"><v>2</v></c></row></sheetData></worksheet>')
            self.assertEqual(cofre.ler_xlsx(f), [{"grupo": "1000", "tipo": "livre"}])
        self.assertEqual(cofre.parse_frac("15%"), Dc("0.15"))
        self.assertEqual(cofre.parse_frac("0,15"), Dc("0.15"))
        self.assertEqual(cofre.parse_data("45000"), date(2023, 3, 15))

    def test_n8_data_coleta_usa_fuso_da_bahia(self):
        """Revisão N8: 28/10 01:00 UTC ainda é 27/10 22:00 na Bahia -> data_coleta 27/10; o id segue em UTC."""
        cat = [{"cota_id": "A", "grupo": "001000", "serie": "0010", "tipo_bem": "veiculo", "plano_pct": 100,
                "credito": "70000", "taxa_pct": "0.16", "parcela": "1000", "pct_embutido_max": "0.10"}]
        d = resumo_semanal.gerar_snapshot([], {"001000": (None, None)}, cat,
                                          agora=datetime(2026, 10, 28, 1, 0, tzinfo=timezone.utc))
        self.assertEqual(d["cotas"][0]["data_coleta"], "2026-10-27")
        self.assertEqual(d["snapshot_id"], "snap-20261028T010000Z")
        d = resumo_semanal.gerar_snapshot([], {"001000": (None, None)}, cat, agora=datetime(2026, 10, 27, 23, 30))
        self.assertEqual(d["cotas"][0]["data_coleta"], "2026-10-27")     # ingênuo = hora local
        self.assertEqual(d["snapshot_id"], "snap-20261028T023000Z")
        self.assertEqual(datetime(2026, 1, 15, 12, tzinfo=resumo_semanal.TZ_LOCAL).utcoffset().total_seconds(), -3 * 3600)

    def test_n12_assembleias_guarda_livres_so_na_janela(self):
        """Revisão N12: listas de lances só nas últimas 6 assembleias; menor_livre e mediana idênticos."""
        rows = []
        for m in range(1, 11):                                         # 10 assembleias, 3 livres cada (SINTÉTICO)
            for x in ("0.%02d" % (10 + m), "0.%02d" % (20 + m), "0.%02d" % (30 + m)):
                rows.append({"grupo": "001000", "data_assembleia": "2026-%02d-15" % m, "tipo": "livre", "lance_pct": x})
        rows.append({"grupo": "001000", "data_assembleia": "2026-01-15", "tipo": "fixo", "lance_pct": "",
                     "n_ofertantes_fixo": "4"})
        novo = cofre.assembleias(iter(rows))["001000"]                 # aceita iterador
        antigo = cofre.assembleias(rows, janela_livres=None)["001000"]
        self.assertEqual([a["menor_livre"] for a in novo], [a["menor_livre"] for a in antigo])
        self.assertEqual([a["n_fixo"] for a in novo], [a["n_fixo"] for a in antigo])
        self.assertTrue(all(a["livres"] == () for a in novo[:4]))
        self.assertTrue(all(len(a["livres"]) == 3 for a in novo[4:]))
        self.assertEqual(cofre.stats_grupo(novo), cofre.stats_grupo(antigo))
        self.assertEqual(novo[0]["ofertantes"], Dc("4"))


class TI2UnidadeFracao(unittest.TestCase):
    """Revisão I2: tudo em fração 0..1 e `<=`. Os valores de regra continuam equivalentes aos da 0001 (0..100)."""

    def test_i2_equivalencia_percentual_x_fracao(self):
        from niveis import TETOS_VALIDOS
        from prazos import embutido_cobre_mediana
        # flags de embutido da 0001 (0, 10, 25 %) convertidos pela 0003 (x / 100) == flags do solver
        self.assertEqual(tuple(Dc(p) / 100 for p in ("0", "10", "25")), tuple(Dc(str(t)) for t in TETOS_VALIDOS))
        # embutido em R$ igual: 25 % e 10 % da categoria
        cat = Dc("81200")
        for p in ("10", "25"):
            self.assertEqual(cat * (Dc(p) / 100), cat * Dc(p) / 100)
        # regra da view da 0001 (% com `<=`) x regra nova (fração com `<=`): mesma decisão em toda a grade,
        # incluindo a fronteira mediana == teto (SINTÉTICO, centésimos de ponto de 0 a 60 %)
        for teto_pct in ("0", "10", "25"):
            for c in range(0, 6001):
                med_pct = Dc(c) / 100
                antigo = med_pct <= Dc(teto_pct)
                self.assertEqual(embutido_cobre_mediana(med_pct / 100, Dc(teto_pct) / 100), antigo, (teto_pct, med_pct))
        self.assertIsNone(embutido_cobre_mediana(None, Dc("0.25")))

    def test_i2_estatisticas_iguais_com_lance_em_percentual_ou_fracao(self):
        """Contagem de contemplações, média na janela de 6 assembleias, menor lance contemplado e mediana:
        idênticos se o cofre traz o lance como '23,5%', '23.5' (0..100) ou '0.235' (fração)."""
        def linhas(fmt):
            rows = []
            for m in range(1, 9):                                         # 8 assembleias (SINTÉTICO)
                for x in (Dc(15 + m) + Dc("0.5"), Dc(30 + m)):
                    rows.append({"grupo": "001000", "data_assembleia": "2026-%02d-10" % m, "tipo": "livre",
                                 "lance_pct": fmt(x)})
                rows += [{"grupo": "001000", "data_assembleia": "2026-%02d-10" % m, "tipo": "fixo", "lance_pct": "",
                          "n_ofertantes_fixo": str(3 + m % 2)}] * (1 + m % 3)
            return rows
        formatos = [lambda x: str(x).replace(".", ",") + "%", lambda x: str(x), lambda x: str(x / 100)]
        stats = [cofre.stats_grupo(cofre.assembleias(linhas(f))["001000"]) for f in formatos]
        self.assertEqual(stats[0], stats[1])
        self.assertEqual(stats[0], stats[2])
        self.assertEqual(stats[0]["c"][0], Dc("0.235"))                   # fração da categoria
        self.assertTrue(all(x is None or 0 <= x <= 1 for x in stats[0]["c"]))

    def test_i2_migration_converte_0001_para_fracao_e_usa_menor_ou_igual(self):
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sql = open(os.path.join(raiz, "supabase", "migrations", "0003_fracao_embutido_mediana.sql"), encoding="utf-8").read()
        for trecho in ("pct_embutido_max / 100", "mediana_lance_pct / 100", "lance_pct / 100",
                       "check (pct_embutido_max between 0 and 1)",
                       "g.mediana_lance_pct <= g.pct_embutido_max"):
            self.assertIn(trecho, sql)


if __name__ == "__main__":
    unittest.main()
