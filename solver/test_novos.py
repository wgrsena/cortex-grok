"""Testes das orientações finais do Wagner (pontos 1-10) e da API. Dados SINTÉTICOS. Job e backtest: ver ../scrap/test_scrap.py."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
import urllib.error
from decimal import Decimal as Dc
from unittest import mock

import embutido
import funcao2
import milp
from contrato import para_json, saida_funcao2, snapshot_para_dict
from dados_sinteticos import cota, snapshot_basico
from forca_bruta import resolver_forca_bruta
from modelos import Pedido, Snapshot
from util_teste import PP
from niveis import construir_universo

AQUI = os.path.dirname(os.path.abspath(__file__))
P0 = PP(milp_gap_relativo=0.0)


def snap_fixo():
    return Snapshot("sf", "t", (
        cota("F1", "003500", "70000", "0.16", "900", "0.25", fixo="4", qtd_fixo_contemplado_mes="3.50"),
        cota("F2", "003600", "70000", "0.14", "800", "0.25", fixo="5", qtd_fixo_contemplado_mes="1.00"),
        cota("F3", "003700", "70000", "0.15", "850", "0.10", fixo="5", qtd_fixo_contemplado_mes="2.00"),
        cota("SEMFIXO", "003800", "70000", "0.10", "700", "0.25", qtd_fixo_contemplado_mes="0"),
    ))


class TJSem21(unittest.TestCase):
    def test_J_de_5_em_5_sem_21(self):
        self.assertEqual(embutido.J, tuple(Dc(x) / 100 for x in (0, 5, 10, 15, 20, 25)))
        self.assertNotIn(Dc("0.21"), embutido.J)

    def test_embutido_do_combo_so_usa_passos_de_5(self):
        snap = snapshot_basico()
        ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("12000"))
        r = resolver_forca_bruta(construir_universo(snap, ped, P0), ped, P0)
        for res in (r, milp.resolver_milp(construir_universo(snap, ped, P0), ped, P0)):
            for c in res["ranking"]:
                for x in c.cartas:
                    cat = x.celula.tipo.categoria
                    self.assertTrue(any(abs(x.embutido_rs - j * cat) <= Dc("0.01") for j in embutido.J),
                                    (x.embutido_rs, cat))


class TRamoFixo(unittest.TestCase):
    ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("0"))

    def test_sem_milp_e_sem_probabilidade(self):
        with mock.patch.object(milp, "resolver_milp", side_effect=AssertionError("MILP não pode rodar")), \
                mock.patch.object(funcao2, "resolver_milp", side_effect=AssertionError("MILP não pode rodar")):
            res = funcao2.resolver_funcao2(snap_fixo(), self.ped, PP())
        self.assertEqual(res["metodo"], "lance_fixo")
        js = para_json(saida_funcao2(res, snap_fixo(), PP()))
        self.assertNotIn("probabilidade", js)
        self.assertNotIn('"p"', js)
        self.assertIn("1 contra todos", res["mensagem_comparativa"])
        self.assertIn("só contra quem ofertou", res["mensagem_comparativa"])

    def test_maior_volume_de_fixo_primeiro_e_sem_fixo_fora(self):
        p = PP(peso_credito=Dc(0), peso_taxa=Dc(0), peso_parcela=Dc(0), peso_fixo=Dc(1))
        r = funcao2.resolver_funcao2(snap_fixo(), self.ped, p)["ranking"]
        self.assertEqual([x["grupo"] for x in r], ["003500", "003700", "003600"])   # SEMFIXO (qtd 0) fora
        self.assertEqual(r[0]["qtd_fixo_contemplado_mes"], Dc("3.50"))

    def test_pesos_ajustaveis_mudam_a_ordem(self):
        p = PP(peso_credito=Dc(0), peso_fixo=Dc(0), peso_parcela=Dc(0), peso_taxa=Dc(1))
        r = funcao2.resolver_funcao2(snap_fixo(), self.ped, p)["ranking"]
        self.assertEqual(r[0]["grupo"], "003600")                                    # menor taxa (14%)

    def test_embutido_cobre_o_lance_fixo_so_com_teto_25(self):
        r = {x["grupo"]: x for x in funcao2.resolver_funcao2(snap_fixo(), self.ped, PP())["ranking"]}
        self.assertTrue(r["003500"]["embutido_cobre_lance"])
        self.assertFalse(r["003700"]["embutido_cobre_lance"])                        # teto 10% < 25%
        self.assertGreater(r["003700"]["falta_recurso_rs"], 0)
        p = PP(fixo_exigir_embutido_cobrir=True)
        self.assertNotIn("003700", [x["grupo"] for x in funcao2.resolver_funcao2(snap_fixo(), self.ped, p)["ranking"]])

    def test_fixo_75_primeiro(self):
        s = Snapshot("s", "t", (cota("A100", "003500", parcela="900", teto="0.25", fixo="4", qtd_fixo_contemplado_mes="5"),
                                cota("A75", "003501", parcela="700", teto="0.25", plano=75, fixo="4",
                                     qtd_fixo_contemplado_mes="1")))
        r = funcao2.resolver_funcao2(s, self.ped, PP())
        c = r["por_categoria"]["carro"]
        self.assertEqual(c["plano_testado"], "75")
        self.assertEqual([x["plano"] for x in c["ranking"]], [75])
        self.assertEqual([x["plano"] for x in c["alternativa_100"]], [100])


class TPlano75Primeiro(unittest.TestCase):
    ped = Pedido("veiculo", Dc("65000"), Dc("1500"), Dc("10000"))

    def snap(self, com75=True):
        cs = [cota("C100", "001000", parcela="1000", teto="0.10", c=("0.15",) * 6)]
        if com75:
            cs.append(cota("C75", "001001", parcela="750", teto="0.10", plano=75, c=("0.15",) * 6))
        return Snapshot("s", "t", tuple(cs))

    def test_75_testado_primeiro_mesmo_com_100_viavel(self):
        r = funcao2.resolver_funcao2(self.snap(), self.ped, P0)
        self.assertEqual(r["plano_testado"], "75")
        self.assertTrue(all(x.celula.tipo.plano_pct == 75 for c in r["ranking"] for x in c.cartas))
        self.assertTrue(r["alternativa_100"]["ranking"])
        out = saida_funcao2(r, self.snap(), P0)
        self.assertEqual(out["alternativa_100"]["rotulo"], "alternativa plano 100%")
        self.assertTrue(all(x["plano"] == 75 for x in out["ranking"][0]["cartas"]))

    def test_100_so_quando_75_nao_resolve(self):
        r = funcao2.resolver_funcao2(self.snap(com75=False), self.ped, P0)
        self.assertEqual(r["plano_testado"], "100 (75 não resolveu)")
        self.assertTrue(r["ranking"])

    def test_sem_alternativa_100_por_parametro(self):
        r = funcao2.resolver_funcao2(self.snap(), self.ped, PP(incluir_alternativa_100=False, milp_gap_relativo=0.0))
        self.assertIsNone(r["alternativa_100"])

    def test_funcao1_75_primeiro(self):
        r = funcao2.resolver_funcao1(self.snap(), self.ped, PP())
        self.assertTrue(r["combinacoes"])
        self.assertEqual({rot for _, rot in r["rotulos"]}, {"75"})


class TSaidaPorCenario(unittest.TestCase):
    def test_campos_pedidos(self):
        ped = Pedido("veiculo", Dc("65000"), Dc("1500"), Dc("10000"))
        snap = Snapshot("s", "t", (cota("X", "001000", taxa="0.16", parcela="1000", teto="0.10",
                                        c=("0.15", "0.15", "0.15", "0.15", None, None)),))
        out = saida_funcao2(funcao2.resolver_funcao2(snap, ped, P0), snap, P0)
        cen = out["ranking"][0]
        carta = cen["cartas"][0]
        for k in ("grupo", "credito", "taxa_adm_serie", "plano", "parcela_pre_contemplacao", "lance_pct", "lance_rs",
                  "cobertura", "W", "p"):
            self.assertIn(k, carta)
        self.assertEqual(carta["taxa_adm_serie"], "0.16")
        self.assertEqual(carta["cobertura"], {"ganharia_em": 4, "de_assembleias": 4})
        for k in ("credito_total", "credito_liquido", "parcela"):
            self.assertIn(k, cen["totais"])
        self.assertIn("probabilidade_conjunta", cen)
        self.assertEqual(cen["cenario"]["plano"], "100")
        self.assertIn("não é contemplação", cen["cenario"]["observacao"])

    def test_juncao_soma_credito_e_probabilidade_conjunta(self):
        ped = Pedido("veiculo", Dc("75000"), Dc("2500"), Dc("20000"))
        snap = Snapshot("s", "t", (
            cota("A", "001000", "40000", "0.16", "1000", "0.10", c=("0.20", "0.20", "0.20", "0.20", "0.20", "0.20")),
            cota("B", "001001", "40000", "0.16", "1000", "0.10", c=("0.20", "0.10", "0.30", "0.20", "0.20", "0.20"))))
        out = saida_funcao2(funcao2.resolver_funcao2(snap, ped, P0), snap, P0)
        cen = out["ranking"][0]
        self.assertEqual(len(cen["cartas"]), 2)
        self.assertEqual(Dc(cen["totais"]["credito_total"]), Dc("80000"))
        conj = 1.0
        for c in cen["cartas"]:
            conj *= float(c["p"])
        self.assertAlmostEqual(float(cen["probabilidade_conjunta"]), conj, places=6)


class TWDesempate(unittest.TestCase):
    ped = Pedido("veiculo", Dc("65000"), Dc("1500"), Dc("10000"))
    snap = Snapshot("s", "t", (
        cota("SEQ6", "001000", taxa="0.16", parcela="1000", teto="0.10", c=("0.15",) * 6),
        cota("SEQ3", "001001", taxa="0.14", parcela="1000", teto="0.10", c=("0.15", "0.15", "0.15", None, "0.15", "0.15"))))

    def resolver(self, solver, w):
        p = PP(w_desempate=w, milp_gap_relativo=0.0)
        uni = construir_universo(self.snap, self.ped, p)
        return solver(uni, self.ped, p)["ranking"][0]

    def test_mesma_prob_w_maior_vence_a_taxa(self):
        for solver in (resolver_forca_bruta, milp.resolver_milp):
            com, sem = self.resolver(solver, True), self.resolver(solver, False)
            self.assertEqual(com.prob, sem.prob)
            self.assertEqual(com.cartas[0].celula.tipo.grupo, "001000")   # W=6 desempata
            self.assertEqual(sem.cartas[0].celula.tipo.grupo, "001001")   # sem W: taxa menor
            self.assertEqual(com.w_soma, 6)


class TUnificacao(unittest.TestCase):
    def test_nunca_mistura_categoria_e_aceita_prazos_diferentes(self):
        ped = Pedido("veiculo", Dc("75000"), Dc("2500"), Dc("20000"))
        c6 = ("0.20",) * 6
        snap = Snapshot("s", "t", (
            cota("C1", "001000", "40000", parcela="1000", teto="0.10", c=c6, qtd=1, prazo_total=60),
            cota("C2", "001001", "40000", parcela="1000", teto="0.10", c=c6, qtd=1, prazo_total=80),
            cota("M1", "001002", "40000", parcela="1000", teto="0.10", c=c6, qtd=1, categoria_veiculo="moto"),
            cota("IMV", "009000", "40000", parcela="1000", teto="0.10", c=c6, tipo_bem="imovel")))
        r = funcao2.resolver_funcao2(snap, ped, P0)
        self.assertEqual(set(r["por_categoria"]), {"carro", "moto"})
        for c in r["ranking"]:
            self.assertEqual(len({x.celula.tipo.categoria_veiculo for x in c.cartas}), 1)
            self.assertTrue(all(x.cota_id != "IMV" for x in c.cartas))
        carro = [c for c in r["ranking"] if c.cartas[0].celula.tipo.categoria_veiculo == "carro"]
        self.assertTrue(any({x.celula.tipo.prazo_total for x in c.cartas} == {60, 80} for c in carro))
        self.assertEqual(r["por_categoria"]["moto"]["ranking"], [])      # 1 moto só: não fecha 75 mil


class TApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        s = snapshot_basico()
        d = snapshot_para_dict(s)
        os.makedirs(os.path.join(cls.tmp.name, "snapshots"))             # mesmo layout que o job do scrap grava
        for caminho in (os.path.join("snapshots", d["snapshot_id"] + ".json"), "ATUAL.json"):
            with open(os.path.join(cls.tmp.name, caminho), "w", encoding="utf-8") as f:
                json.dump(d, f)
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0))
            cls.porta = sk.getsockname()[1]
        env = {**os.environ, "DISAL_SOLVER_TOKEN": "tok-teste", "DISAL_DADOS_DIR": cls.tmp.name}
        cls.srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--port", str(cls.porta),
                                    "--log-level", "warning"], cwd=AQUI, env=env)
        for _ in range(100):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{cls.porta}/saude", timeout=1)
                break
            except OSError:
                time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.srv.terminate()
        cls.srv.wait(10)
        cls.tmp.cleanup()

    def chamar(self, rota, corpo, token="tok-teste"):
        req = urllib.request.Request(f"http://127.0.0.1:{self.porta}{rota}", json.dumps(corpo).encode(),
                                     {"Content-Type": "application/json", **({"X-API-Token": token} if token else {})})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, None

    PED = {"tipo_bem": "veiculo", "credito_liquido_alvo": "70000", "parcela_max": "2500", "recurso_proprio": "12000"}

    def test_auth(self):
        self.assertEqual(self.chamar("/probabilidade", {"pedido": self.PED}, token=None)[0], 401)
        self.assertEqual(self.chamar("/probabilidade", {"pedido": self.PED}, token="errado")[0], 401)

    def test_fecha_por_padrao_sem_token_no_ambiente(self):
        from fastapi import HTTPException
        import app
        with mock.patch.dict(os.environ, {"DISAL_SOLVER_TOKEN": ""}):
            with self.assertRaises(HTTPException) as e:
                app.autenticar("qualquer")
        self.assertEqual(e.exception.status_code, 503)

    def test_snapshot_id_invalido_e_inexistente(self):
        self.assertEqual(self.chamar("/probabilidade", {"pedido": self.PED, "snapshot_id": "../etc/passwd"})[0], 422)
        self.assertEqual(self.chamar("/probabilidade", {"pedido": self.PED, "snapshot_id": "nao-existe"})[0], 404)

    def test_probabilidade_milp_e_combinacoes(self):
        st, out = self.chamar("/probabilidade", {"pedido": self.PED})
        self.assertEqual(st, 200)
        self.assertEqual(out["metodo"], "milp")
        self.assertTrue(out["ranking"])
        st, out = self.chamar("/combinacoes", {"pedido": self.PED})
        self.assertEqual(st, 200)
        self.assertIn("combinacoes", out)

    def test_probabilidade_recurso_zero_vai_para_ramo_fixo(self):
        st, out = self.chamar("/probabilidade", {"pedido": {**self.PED, "recurso_proprio": "0"}})
        self.assertEqual((st, out["metodo"]), (200, "lance_fixo"))
        self.assertNotIn("probabilidade_conjunta", json.dumps(out))

    def test_entrada_invalida(self):
        self.assertEqual(self.chamar("/probabilidade", {"pedido": {"tipo_bem": "veiculo"}})[0], 422)
        self.assertEqual(self.chamar("/probabilidade", {"pedido": self.PED, "parametros": {"inexistente": 1}})[0], 422)

    def test_revalidar_valida_e_reserva(self):
        _, out = self.chamar("/probabilidade", {"pedido": self.PED})
        ids = sorted({x["cota_id"] for x in out["ranking"][0]["cartas"]})
        st, r = self.chamar("/revalidar", {"pedido": self.PED, "principal": ids})
        self.assertEqual((st, r["status"]), (200, "valida"))
        st, r = self.chamar("/revalidar", {"pedido": self.PED, "principal": ids + ["INEXISTENTE"],
                                           "reservas": [ids]})
        self.assertEqual((st, r["status"], r["metodo"]), (200, "recalculada", "reserva"))
        st, r = self.chamar("/revalidar", {"pedido": self.PED, "principal": ["INEXISTENTE"]})
        self.assertEqual((st, r["status"], r["metodo"]), (200, "recalculada", "recalculo"))


if __name__ == "__main__":
    unittest.main()
