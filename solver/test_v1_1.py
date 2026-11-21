"""Testes da v1.1 (decisões do Wagner de 27/10/2026, repassadas pelo MiroFish Cortex). Todos os dados são SINTÉTICOS.
Itens: 1 prob = W/6 | 2 sem teto de sobra | 3 teto de embutido pela flag, nunca pelo número do grupo |
4 chance_fixo | 6 mediana como dado comercial | 7 validade | 8 prazo de entrada | 9 campos de saída."""
import unittest
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal as Dc
from fractions import Fraction

import funcao2
from contrato import carta_dict, para_json, parametros_de_dict, saida_funcao2
from dados_sinteticos import cota
from embutido import fazer_celula, opcoes_embutido
from forca_bruta import resolver_forca_bruta
from modelos import Parametros, Pedido, Snapshot
from niveis import construir_universo
from prazos import (assembleia_aplicavel, campos_validade_prazo, oportunidade_desatualizada,
                    prazo_entrada_cliente_novo)
from ramo_fixo import chance_fixo

P0 = Parametros(milp_gap_relativo=0.0)
D_ = date.fromisoformat


class T1ProbabilidadeSequenciaSobre6(unittest.TestCase):
    """SINTÉTICO: histórico com W = 4 assembleias seguidas e 2 nulas."""
    c = cota("X", credito="70000", parcela="1000", teto="0", c=("0.10", "0.12", "0.14", "0.16", None, None))
    ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("100000"))

    def test_padrao_e_p_igual_w_sobre_6_com_w_e_cobertura_nos_campos(self):
        self.assertEqual(Parametros().modo_probabilidade, "sequencia_W_sobre_6")
        snap = Snapshot("s", "t", (self.c,))
        uni = construir_universo(snap, self.ped, Parametros())
        self.assertEqual([n.p for n in uni.tipos[0].niveis], [Fraction(w, 6) for w in (1, 2, 3, 4)])
        carta = carta_dict(next(iter(resolver_forca_bruta(uni, self.ped, Parametros())["ranking"])).cartas[0])
        self.assertEqual(carta["W"], 4)
        self.assertIn("ganharia_em", carta["cobertura"])
        self.assertAlmostEqual(carta["p"], carta["W_nivel"] / 6)

    def test_fracao_h_sobre_N_so_como_alternativa_explicita(self):
        uni = construir_universo(Snapshot("s", "t", (self.c,)), self.ped, Parametros(modo_probabilidade="fracao_h_sobre_N"))
        self.assertEqual(uni.tipos[0].niveis[-1].p, Fraction(4, 4))        # h/N, não W/6


class T2SemTetoDeSobra(unittest.TestCase):
    def test_sem_teto_e_sobra_explicita_no_gap_do_json(self):
        c = cota("X", credito="100000", parcela="1000", teto="0", c=("0.10",) * 6)      # alvo 65.000: sobra 35.000 (> 10%)
        ped = Pedido("veiculo", Dc("65000"), Dc("1500"), Dc("50000"))
        snap = Snapshot("s", "t", (c,))
        self.assertIsNone(Parametros().delta_credito)
        out = saida_funcao2(funcao2.resolver_funcao2(snap, ped, P0), snap, P0)
        self.assertEqual(out["ranking"][0]["gap"]["sobra_credito"], "35000.00")
        self.assertEqual(out["excluidos"].get("credito_acima_faixa", 0), 0)


class T3TetoDeEmbutidoPelaFlag(unittest.TestCase):
    GRUPOS = ("001000", "003300", "004100", "004104", "006207", "999999")     # números quaisquer: não podem mudar nada

    def opcoes(self, grupo, teto):
        c = cota("X", grupo=grupo, teto=teto)
        t = construir_universo(Snapshot("s", "t", (c,)), Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("1")), Parametros()).tipos[0]
        return opcoes_embutido(fazer_celula(t, replace(t.niveis[0], lance_pct=Dc("1")), Parametros()))

    def test_base_e_a_categoria_e_passo_de_5(self):
        # categoria = 70.000 * 1,16 = 81.200; 5% = 4.060; teto 10% -> {0, 5%, 10%}; teto 25% -> de 5 em 5 até 25%
        self.assertEqual(self.opcoes("001000", "0.10"), [Dc(x) for x in ("0", "4060.00", "8120.00")])
        self.assertEqual(self.opcoes("003500", "0.25"),
                         [Dc(x) for x in ("0", "4060.00", "8120.00", "12180.00", "16240.00", "20300.00")])
        self.assertEqual(self.opcoes("003500", "0"), [Dc(0)])

    def test_logica_nao_depende_do_numero_do_grupo(self):
        for teto in ("0", "0.10", "0.25"):
            ref = self.opcoes("001000", teto)
            for g in self.GRUPOS:
                self.assertEqual(self.opcoes(g, teto), ref, (g, teto))

    def test_excecao_e_dado_do_catalogo_sem_fixo_sem_embutido(self):
        # a "exceção" é só tem_lance_fixo=False e pct_embutido_max=0 nos dados; com os mesmos dados em qualquer grupo, o mesmo resultado
        ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("100000"))
        res = []
        for g in ("004100", "001000"):
            snap = Snapshot("s", "t", (cota("X", grupo=g, teto="0"),))
            uni = construir_universo(snap, ped, Parametros())
            rk = resolver_forca_bruta(uni, ped, Parametros())["ranking"]
            res.append([(c.embutido_total, c.prob) for c in rk])
            self.assertEqual(uni.alertas, ())                                  # sem alerta por número de grupo
        self.assertEqual(res[0], res[1])

    def test_nada_no_codigo_do_repo_cita_numero_de_grupo(self):
        """Revisão N10: varre o REPO inteiro (não só solver/) atrás de regra por número de grupo. Exclusões
        documentadas (EXCLUSOES_NUMERO_GRUPO): documentação (*.md, docs/), testes e fixtures SINTÉTICOS (que citam
        grupos de propósito para provar que o número não muda nada) e comentários `--` de SQL (exemplo de formato
        na 0001, já aplicada; mudar comentário de migração aplicada não traz ganho)."""
        import os
        import re
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        padrao = re.compile(r"\b00(33|41|62)\d\d\b")
        vistos = 0
        for dirpath, dirnames, filenames in os.walk(raiz):
            dirnames[:] = [d for d in dirnames if d not in EXCLUSOES_NUMERO_GRUPO["pastas"] and not d.startswith(".venv")]
            for nome in filenames:
                ext = os.path.splitext(nome)[1]
                if ext not in EXTENSOES_CODIGO or nome.startswith("test_") or nome in EXCLUSOES_NUMERO_GRUPO["arquivos"]:
                    continue
                caminho = os.path.join(dirpath, nome)
                texto = open(caminho, encoding="utf-8", errors="replace").read()
                if ext == ".sql":
                    texto = re.sub(r"--[^\n]*", "", texto)          # comentário SQL não é regra
                vistos += 1
                self.assertIsNone(padrao.search(texto), os.path.relpath(caminho, raiz))
        self.assertGreater(vistos, 20)                                  # garante que a varredura achou o código


EXTENSOES_CODIGO = {".py", ".sql", ".ts", ".js", ".mjs", ".json", ".toml", ".yml", ".yaml", ".sh", ".html"}
EXCLUSOES_NUMERO_GRUPO = {
    "pastas": {".git", "node_modules", "__pycache__", ".pytest_cache", "docs"},
    # fixtures sintéticas: citam grupos de propósito (o teste T3 prova que o número não altera nada)
    "arquivos": {"dados_sinteticos.py", "util_teste.py", "cofre_sintetico.py"},
}


class T4ChanceFixo(unittest.TestCase):
    ped = Pedido("veiculo", Dc("70000"), Dc("2500"), Dc("0"))

    def snap(self, ofertantes):
        a, b, c = ofertantes
        return Snapshot("sf", "t", (
            cota("F1", "003500", "70000", "0.16", "900", "0.25", fixo=a, qtd_fixo_contemplado_mes="3.50"),
            cota("F2", "003600", "70000", "0.14", "800", "0.25", fixo=b, qtd_fixo_contemplado_mes="1.00"),
            cota("F3", "003700", "70000", "0.15", "850", "0.10", fixo=c, qtd_fixo_contemplado_mes="2.00")))

    def test_funcao_pura(self):
        self.assertEqual(chance_fixo(Dc("4")), Fraction(1, 4))
        self.assertEqual(chance_fixo(Dc("0.5")), 1)                    # limitada a 1
        self.assertIsNone(chance_fixo(None))
        self.assertIsNone(chance_fixo(Dc("0")))

    def test_chance_fixo_tem_fonte_unica(self):
        """Revisão N2: o nível fixo (MILP/Função 2) e a coluna do ramo fixo usam a MESMA função."""
        import niveis
        import ramo_fixo
        self.assertIs(ramo_fixo.chance_fixo, niveis.chance_fixo)
        c = cota("FX", credito="70000", parcela="1000", teto="0.25", fixo="4", c=(None,) * 6)
        fixo = [n for n in niveis.calcular_niveis(c, P0)[3] if n.tipo == "fixo"]
        self.assertEqual(fixo[0].p, chance_fixo(Dc("4")))

    def test_saida_traz_chance_fixo_e_ausente_vira_none(self):
        s = self.snap(("4", "5", "5"))
        s = replace(s, cotas=(replace(s.cotas[0], n_ofertantes_fixo_medio=None),) + s.cotas[1:])
        out = saida_funcao2(funcao2.resolver_funcao2(s, self.ped, P0), s, P0)
        por_cota = {x["cota_id"]: x for x in out["ranking"]}
        self.assertIsNone(por_cota["F1"]["chance_fixo"])
        self.assertAlmostEqual(por_cota["F2"]["chance_fixo"], 0.2)

    def test_chance_fixo_nao_altera_score_nem_ordem(self):
        def rank(of):
            r = funcao2.resolver_funcao2(self.snap(of), self.ped, P0)
            return [(x["cota_id"], x["score"]) for x in r["ranking"]]
        self.assertEqual(rank(("4", "5", "5")), rank(("50", "1", "9")))


class T6MedianaComoDadoComercial(unittest.TestCase):
    def test_embutido_cobre_mediana(self):
        f = lambda m, teto: campos_validade_prazo(m, Dc(teto), None, None, None)["embutido_cobre_mediana"]   # noqa: E731
        self.assertTrue(f(Dc("0.08"), "0.10"))
        self.assertTrue(f(Dc("0.10"), "0.10"))         # I2: `<=` (embutido que iguala a mediana cobre o lance)
        self.assertFalse(f(Dc("0.15"), "0.10"))
        self.assertFalse(f(Dc("0.05"), "0"))           # grupo sem embutido nunca cobre
        self.assertIsNone(f(None, "0.10"))

    def test_mediana_nao_muda_probabilidade_nem_ranking(self):
        ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("100000"))
        res = []
        for med in (None, Dc("0.05"), Dc("0.90")):
            snap = Snapshot("s", "t", (cota("X", mediana_lance_livre=med), cota("Y", "001001", parcela="950")))
            uni = construir_universo(snap, ped, Parametros())
            rk = resolver_forca_bruta(uni, ped, Parametros())["ranking"]
            res.append([(sorted(c.cota_ids), c.prob) for c in rk])
        self.assertEqual(res[0], res[1])
        self.assertEqual(res[0], res[2])

    def test_mediana_aparece_na_carta(self):
        ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("100000"))
        snap = Snapshot("s", "t", (cota("X", mediana_lance_livre=Dc("0.0800")),))
        uni = construir_universo(snap, ped, Parametros())
        carta = carta_dict(resolver_forca_bruta(uni, ped, Parametros())["ranking"][0].cartas[0])
        self.assertEqual(carta["mediana_lance_livre"], "0.0800")
        self.assertTrue(carta["embutido_cobre_mediana"])


class T7Validade(unittest.TestCase):
    HOJE = D_("2026-10-27")

    def test_bordas_8_e_9_dias(self):
        self.assertFalse(oportunidade_desatualizada(D_("2026-10-19"), self.HOJE))     # exatamente 8 dias
        self.assertTrue(oportunidade_desatualizada(D_("2026-10-18"), self.HOJE))      # 9 dias
        self.assertFalse(oportunidade_desatualizada(self.HOJE, self.HOJE))

    def test_limite_e_parametro_e_formatos(self):
        self.assertTrue(oportunidade_desatualizada("2026-10-24", self.HOJE, max_dias=2))
        self.assertFalse(oportunidade_desatualizada("2026-10-25", self.HOJE, max_dias=2))
        self.assertFalse(oportunidade_desatualizada(datetime(2026, 10, 19, 23, 59), "2026-10-27T01:00:00"))
        self.assertTrue(oportunidade_desatualizada("2026-10-18T10:00:00+00:00", datetime(2026, 10, 27, 9, 0)))

    def test_sem_dado_ou_sem_hoje_e_none_e_nunca_erro(self):
        self.assertIsNone(oportunidade_desatualizada(None, self.HOJE))
        self.assertIsNone(oportunidade_desatualizada("2026-10-18", None))


class T8PrazoEntrada(unittest.TestCase):
    # calendário de 2026: 27/10 = terça; 30/10 = sexta; 31/10 = sábado; 01/11 = domingo; 02/11 = segunda
    def test_dia_util_normal(self):
        self.assertEqual(prazo_entrada_cliente_novo(D_("2026-11-05")), D_("2026-11-03"))   # quinta -> terça

    def test_prazo_cai_no_sabado_e_no_domingo_vale_a_sexta_anterior(self):
        self.assertEqual(prazo_entrada_cliente_novo(D_("2026-11-02")), D_("2026-10-30"))   # prazo seria sábado 31/10
        self.assertEqual(prazo_entrada_cliente_novo(D_("2026-11-03")), D_("2026-10-30"))   # prazo seria domingo 01/11

    def test_feriado_e_parametro_e_recua_para_o_dia_util_anterior(self):
        self.assertEqual(prazo_entrada_cliente_novo(D_("2026-11-02"), {D_("2026-10-30")}), D_("2026-10-29"))  # sexta feriado
        self.assertEqual(prazo_entrada_cliente_novo(D_("2026-11-04"), {"2026-11-02"}), D_("2026-10-30"))      # segunda feriado
        self.assertEqual(prazo_entrada_cliente_novo(D_("2026-11-05"), frozenset()), D_("2026-11-03"))         # sem feriado cadastrado

    def test_dias_antes_e_parametro(self):
        self.assertEqual(prazo_entrada_cliente_novo(D_("2026-11-05"), dias_antes=1), D_("2026-11-04"))

    def test_entrada_exatamente_no_dia_do_prazo_vale(self):
        prox = [D_("2026-11-02"), D_("2026-12-07")]
        self.assertEqual(assembleia_aplicavel(D_("2026-10-30"), prox), D_("2026-11-02"))   # prazo inclusivo
        self.assertEqual(assembleia_aplicavel("2026-10-27", prox), D_("2026-11-02"))

    def test_fora_do_prazo_vale_a_assembleia_seguinte(self):
        prox = ["2026-12-07", "2026-11-02"]                                                # fora de ordem de propósito
        self.assertEqual(assembleia_aplicavel(D_("2026-10-31"), prox), D_("2026-12-07"))
        self.assertEqual(assembleia_aplicavel(D_("2026-11-01"), prox), D_("2026-12-07"))
        self.assertIsNone(assembleia_aplicavel(D_("2026-12-31"), prox))
        # feriado na sexta 30/10 recua o prazo para quinta 29/10: entrar em 30/10 já é tarde
        self.assertEqual(assembleia_aplicavel(D_("2026-10-30"), prox, {D_("2026-10-30")}), D_("2026-12-07"))
        self.assertEqual(assembleia_aplicavel(D_("2026-10-29"), prox, {D_("2026-10-30")}), D_("2026-11-02"))

class T9CamposDeSaida(unittest.TestCase):
    ped = Pedido("veiculo", Dc("70000"), Dc("1500"), Dc("100000"))

    def carta(self, params, **kw):
        snap = Snapshot("s", "t", (cota("X", teto="0.10", **kw),))
        uni = construir_universo(snap, self.ped, params)
        return carta_dict(resolver_forca_bruta(uni, self.ped, params)["ranking"][0].cartas[0], params)

    def test_campos_preenchidos_com_hoje_e_proxima_assembleia(self):
        p = Parametros(hoje="2026-10-27")
        c = self.carta(p, data_coleta="2026-10-20", proxima_assembleia="2026-11-02", mediana_lance_livre=Dc("0.08"))
        self.assertEqual((c["data_coleta"], c["desatualizada"]), ("2026-10-20", False))
        self.assertEqual((c["prazo_entrada"], c["assembleia_aplicavel"], c["prazo_vencido"]), ("2026-10-30", "2026-11-02", False))
        self.assertTrue(c["embutido_cobre_mediana"])
        c2 = self.carta(Parametros(hoje="2026-10-31"), data_coleta="2026-10-20", proxima_assembleia="2026-11-02")
        self.assertEqual((c2["assembleia_aplicavel"], c2["prazo_vencido"]), (None, True))
        c3 = self.carta(Parametros(hoje="2026-10-29", feriados=("2026-10-30",)), proxima_assembleia="2026-11-02")
        self.assertEqual(c3["prazo_entrada"], "2026-10-29")

    def test_sem_dados_saem_none_sem_erro_e_campos_antigos_continuam(self):
        c = self.carta(Parametros())
        for k in ("data_coleta", "desatualizada", "prazo_entrada", "assembleia_aplicavel", "mediana_lance_livre",
                  "embutido_cobre_mediana", "proxima_assembleia", "prazo_vencido"):
            self.assertIsNone(c[k], k)
        for k in ("grupo", "credito", "taxa_adm_serie", "plano", "parcela_pre_contemplacao", "lance_rs", "cobertura", "W", "p"):
            self.assertIn(k, c)
        self.assertIsNone(self.carta(Parametros(hoje="2026-10-27"))["desatualizada"])    # hoje sem data_coleta

    def test_parametros_pela_api_json_e_gap_na_saida(self):
        p = parametros_de_dict({"hoje": "2026-10-27", "feriados": ["2026-10-30"], "max_dias_coleta": 3})
        self.assertEqual((p.hoje, p.feriados, p.max_dias_coleta), ("2026-10-27", ("2026-10-30",), 3))
        snap = Snapshot("s", "t", (cota("X", data_coleta="2026-10-20"),))
        out = funcao2.resolver_funcao2(snap, self.ped, replace(P0, hoje=p.hoje, max_dias_coleta=3))
        js = para_json(saida_funcao2(out, snap, replace(P0, hoje=p.hoje, max_dias_coleta=3)))
        self.assertIn('"desatualizada": true', js)
        self.assertIn('"versao_regras": "v1.1"', js)


class TRevisaoReviewer(unittest.TestCase):
    """Revisão do Cortex Reviewer (N4, N7, N9, I3). Datas SINTÉTICAS."""

    def test_n4_prazo_vencido_usa_a_assembleia_seguinte_da_lista(self):
        # hoje 31/10 (sáb): prazo da de 02/11 era 30/10 (venceu); a de 16/11 tem prazo 14/11 (vale)
        c = campos_validade_prazo(None, Dc("0.10"), None, ["2026-11-02", "2026-11-16"], "2026-10-31")
        self.assertEqual((c["proxima_assembleia"], c["assembleia_aplicavel"], c["prazo_entrada"], c["prazo_vencido"]),
                         ("2026-11-02", "2026-11-16", "2026-11-13", False))
        self.assertIsNone(c["motivo_assembleia_aplicavel"])

    def test_n4_uma_data_so_e_prazo_vencido_da_null_com_motivo(self):
        c = campos_validade_prazo(None, Dc("0.10"), None, "2026-11-02", "2026-10-31")
        self.assertEqual((c["assembleia_aplicavel"], c["prazo_vencido"]), (None, True))
        self.assertEqual(c["motivo_assembleia_aplicavel"], "prazo_vencido_sem_assembleia_seguinte_cadastrada")
        c = campos_validade_prazo(None, Dc("0.10"), None, ("2026-11-02", "2026-11-03"), "2026-11-05")
        self.assertEqual(c["motivo_assembleia_aplicavel"], "prazo_vencido_em_todas_as_assembleias_cadastradas")
        self.assertEqual(campos_validade_prazo(None, Dc("0"), None, None, "2026-10-31")["motivo_assembleia_aplicavel"],
                         "sem_proxima_assembleia")

    def test_n4_lista_no_snapshot_json_vira_tupla_e_chega_na_carta(self):
        from contrato import snapshot_de_dict, snapshot_para_dict
        c = replace(cota("L", credito="70000", parcela="1000", teto="0.10", c=("0.10",) * 6),
                    proxima_assembleia=None)
        d = snapshot_para_dict(Snapshot("s", "t", (c,)))
        d["cotas"][0]["proxima_assembleia"] = ["2026-11-16", "2026-11-02"]
        snap = snapshot_de_dict(d)
        self.assertEqual(snap.cotas[0].proxima_assembleia, ("2026-11-16", "2026-11-02"))
        ped = Pedido("veiculo", Dc("60000"), Dc("1500"), Dc("100000"))
        params = replace(P0, hoje="2026-10-31")
        carta = carta_dict(resolver_forca_bruta(construir_universo(snap, ped, params), ped, params)["ranking"][0].cartas[0],
                           params)
        self.assertEqual((carta["assembleia_aplicavel"], carta["prazo_vencido"]), ("2026-11-16", False))

    def test_n9_data_malformada_nao_derruba_e_vira_none_com_aviso(self):
        c = campos_validade_prazo(Dc("0.05"), Dc("0.10"), "27/10/2026", ["2026-13-40", "2026-11-16"], "ontem",
                                  feriados=("2026-11-15", "xx"))
        self.assertIsNone(c["data_coleta"])
        self.assertIsNone(c["desatualizada"])
        self.assertEqual(c["proxima_assembleia"], "2026-11-16")         # a válida da lista continua valendo
        self.assertIsNone(c["prazo_vencido"])                           # sem `hoje` válido não decide
        self.assertEqual(c["datas_invalidas"], ["hoje", "data_coleta", "proxima_assembleia", "feriados"])
        self.assertEqual(c["embutido_cobre_mediana"], True)            # o resto da saída segue normal
        ok = campos_validade_prazo(None, Dc("0"), "2026-10-27", "2026-11-16", "2026-10-28")
        self.assertEqual(ok["datas_invalidas"], [])

    def test_n9_parametro_hoje_malformado_na_funcao2_nao_quebra(self):
        c = replace(cota("H", credito="70000", parcela="1000", teto="0.10", c=("0.10",) * 6), data_coleta="lixo")
        snap, ped = Snapshot("s", "t", (c,)), Pedido("veiculo", Dc("60000"), Dc("1500"), Dc("100000"))
        params = replace(P0, hoje="2026/10/31")
        out = funcao2.resolver_funcao2(snap, ped, params)
        import json
        carta = json.loads(para_json(saida_funcao2(out, snap, params)))["ranking"][0]["cartas"][0]
        self.assertEqual(carta["datas_invalidas"], ["hoje", "data_coleta"])

    def test_n7_limite_de_8_dias_tem_fonte_unica(self):
        import modelos
        import prazos
        self.assertEqual(modelos.MAX_DIAS_COLETA, 8)
        self.assertEqual(Parametros().max_dias_coleta, modelos.MAX_DIAS_COLETA)
        self.assertEqual(prazos.MAX_DIAS_PADRAO, modelos.MAX_DIAS_COLETA)
        self.assertIsNone(prazos.extras_oportunidade(None, Dc("0"), "2026-10-19", None, None)["desatualizada"])

    def test_i3_producao_nao_importa_forca_bruta(self):
        import ast
        import os
        aqui = os.path.dirname(os.path.abspath(__file__))
        oraculo = {"forca_bruta.py", "util_teste.py", "dados_sinteticos.py"}
        for nome in sorted(os.listdir(aqui)):
            if not nome.endswith(".py") or nome.startswith("test_") or nome in oraculo:
                continue
            arv = ast.parse(open(os.path.join(aqui, nome), encoding="utf-8").read())
            mods = {n.module for n in ast.walk(arv) if isinstance(n, ast.ImportFrom)}
            mods |= {a.name for n in ast.walk(arv) if isinstance(n, ast.Import) for a in n.names}
            self.assertNotIn("forca_bruta", mods, nome)
        ignorados = open(os.path.join(aqui, ".dockerignore"), encoding="utf-8").read().split()
        for f in ("forca_bruta.py", "test_*.py", "util_teste.py", "dados_sinteticos.py"):
            self.assertIn(f, ignorados)


if __name__ == "__main__":
    unittest.main()
