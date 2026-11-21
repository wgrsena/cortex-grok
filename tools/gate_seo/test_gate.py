#!/usr/bin/env python3
"""Testes do parser e do gate (unittest, stdlib). Rodar: python3 tools/gate_seo/test_gate.py"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import gate  # noqa: E402
from canonico import parse  # noqa: E402

REPO = AQUI.parent.parent
CANON_OK = """# Requisitos SEO canônicos

**Versão: v2.0 — 2026-11-05**

## 1. Performance

### SEO-001 — CLS: width e height em img

- **Requisito:** toda imagem com width/height
- **Fonte:** https://web.dev/articles/optimize-cls
- **Data:** 2026-11-01
- **Severidade:** bloqueante
- **Status:** ativo

### SEO-002 — Autoria real

- [ ] Requisito: byline real
- [ ] Fonte: QRG p. 35
- [ ] Data de descoberta: 2026-11-02
- [ ] Severidade: bloqueante
- [ ] Status: ativo

### SEO-003 — Meta description única

- **Requisito:** meta description única
- **Fonte:** https://developers.google.com/search/docs/appearance/snippet
- **Data:** 2026-11-02
- **Severidade:** média
- **Status:** ativo

### SEO-004 — FAQ rich result

- **Requisito:** não esperar rich result de FAQ
- **Fonte:** /search/updates
- **Data:** 2026-10-31
- **Severidade:** bloqueante
- **Status:** substituído

### Testes antes do tráfego real

- [ ] Rich Results Test
"""


def snapshot(d: Path, texto: str, pasta=gate.PASTA_CANONICA_ID, sha=None):
    md = d / "canon.md"
    md.write_text(texto, encoding="utf-8")
    meta = {"arquivo": "canon.md", "sha256": sha or hashlib.sha256(md.read_bytes()).hexdigest(),
            "drive_id": "X", "pasta_drive_id": pasta, "pasta_drive_nome": "teste"}
    p = d / "canon.meta.json"
    p.write_text(json.dumps(meta), encoding="utf-8")
    return p


def alvo_com_check(d: Path, falhas=()):
    a = d / "alvo"
    (a / "tools").mkdir(parents=True)
    linhas = "".join(f'print("FALHA [{r}] x.html: problema")\n' for r in falhas)
    (a / "tools" / "check.py").write_text(
        f"import sys\nprint('Páginas: 1')\n{linhas}sys.exit({1 if falhas else 0})\n", encoding="utf-8")
    return a


class TestParser(unittest.TestCase):
    def test_campos_nas_duas_grafias(self):
        c = parse(CANON_OK)
        self.assertEqual(c.versao, "v2.0")
        self.assertEqual([r.id for r in c.requisitos], ["SEO-001", "SEO-002", "SEO-003", "SEO-004"])
        r2 = c.requisitos[1]
        self.assertEqual((r2.data, r2.severidade, r2.status), ("2026-11-02", "bloqueante", "ativo"))
        self.assertTrue(c.requisitos[0].bloqueante and c.requisitos[0].ativo)
        self.assertFalse(c.requisitos[2].bloqueante)
        self.assertFalse(c.requisitos[3].ativo)
        self.assertEqual(c.requisitos[0].faltando(), [])

    def test_bloco_sem_requisito_nao_conta(self):
        self.assertNotIn("Testes antes do tráfego real", [r.titulo for r in parse(CANON_OK).requisitos])

    def test_id_em_campo(self):
        c = parse("Versão: v1\n### Título\n- **ID:** SEO-010\n- **Requisito:** x\n")
        self.assertEqual(c.requisitos[0].id, "SEO-010")

    def test_escape_do_google_docs(self):
        c = parse("**Versão: v1.3 — 2026-11-02**\n### INP \\< 200 ms\n- **Requisito:** INP abaixo de 200 ms\n- **Status:** ativo\n")
        self.assertEqual(c.requisitos[0].titulo, "INP < 200 ms")
        self.assertEqual(c.versao, "v1.3")

    def test_diario_v13_real(self):
        """Snapshot real do DIARIO_SEO_PITAGORAS v1.3: 106 requisitos, nenhum com ID nem severidade."""
        md = REPO / "docs" / "seo-canonico" / "candidato-DIARIO_SEO_PITAGORAS-v1.3.md"
        c = parse(md.read_text(encoding="utf-8"))
        self.assertEqual(c.versao, "v1.3")
        self.assertEqual(len(c.requisitos), 106)
        self.assertTrue(all(not r.id and not r.severidade for r in c.requisitos))
        self.assertTrue(all(r.status and r.fonte and r.data for r in c.requisitos))


class TestGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    MAPA = {"SEO-001": ["R7"]}
    AT2 = {"SEO-002": {"revisor": "Wagner", "data": "2026-11-05", "commit": ""}}

    def test_canonico_ausente_bloqueia(self):
        r = gate.avaliar(self.d / "nao-existe.meta.json", alvo_com_check(self.d), mapa=self.MAPA)
        self.assertEqual(r["resultado"], "BLOCK")
        self.assertEqual(r["bloqueios"], ["GATE-CANON-AUSENTE"])

    def test_sha_divergente_bloqueia(self):
        m = snapshot(self.d, CANON_OK, sha="0" * 64)
        r = gate.avaliar(m, alvo_com_check(self.d), atestado=self.AT2, mapa=self.MAPA)
        self.assertIn("GATE-CANON-SHA", r["bloqueios"])

    def test_fora_da_pasta_canonica_bloqueia(self):
        m = snapshot(self.d, CANON_OK, pasta="outra")
        r = gate.avaliar(m, alvo_com_check(self.d), atestado=self.AT2, mapa=self.MAPA)
        self.assertIn("GATE-CANON-FORA-DA-PASTA", r["bloqueios"])

    def test_sem_versao_sem_id_sem_severidade_bloqueia(self):
        m = snapshot(self.d, "### LCP\n- **Requisito:** x\n- **Fonte:** y\n- **Data de descoberta:** 2026-10-31\n- **Status:** ativo\n")
        r = gate.avaliar(m, alvo_com_check(self.d), mapa={})
        for cod in ("GATE-CANON-SEM-VERSAO", "GATE-CANON-SEM-ID", "GATE-CANON-SEM-SEVERIDADE"):
            self.assertIn(cod, r["bloqueios"])
        self.assertEqual(r["violados"], [])

    def test_id_duplicado_bloqueia(self):
        m = snapshot(self.d, CANON_OK.replace("SEO-003", "SEO-001"))
        r = gate.avaliar(m, alvo_com_check(self.d), atestado=self.AT2, mapa=self.MAPA)
        self.assertIn("GATE-CANON-ID-DUPLICADO", r["bloqueios"])

    def test_pass_com_auto_ok_e_manual_atestado(self):
        r = gate.avaliar(snapshot(self.d, CANON_OK), alvo_com_check(self.d), atestado=self.AT2, mapa=self.MAPA)
        self.assertEqual(r["resultado"], "PASS", r["bloqueios"])
        self.assertEqual([v["id"] for v in r["auto_ok"]], ["SEO-001"])
        self.assertEqual([v["id"] for v in r["manual_atestado"]], ["SEO-002"])

    def test_violacao_automatica_reporta_id(self):
        r = gate.avaliar(snapshot(self.d, CANON_OK), alvo_com_check(self.d, ["R7"]), atestado=self.AT2, mapa=self.MAPA)
        self.assertEqual(r["resultado"], "BLOCK")
        self.assertEqual(r["bloqueios"], ["SEO-001"])

    def test_manual_sem_atestado_nao_passa_calado(self):
        r = gate.avaliar(snapshot(self.d, CANON_OK), alvo_com_check(self.d), mapa=self.MAPA)
        self.assertEqual(r["bloqueios"], ["SEO-002 (manual pendente)"])

    def test_atestado_de_outro_commit_nao_vale(self):
        at = {"SEO-002": {"revisor": "Wagner", "data": "2026-11-05", "commit": "deadbee"}}
        r = gate.avaliar(snapshot(self.d, CANON_OK), alvo_com_check(self.d), atestado=at, mapa=self.MAPA)
        self.assertIn("SEO-002 (manual pendente)", r["bloqueios"])

    def test_nao_bloqueante_e_substituido_ignorados(self):
        r = gate.avaliar(snapshot(self.d, CANON_OK), alvo_com_check(self.d), atestado=self.AT2, mapa=self.MAPA)
        tudo = {x["id"] for k in ("violados", "manual_pendente", "manual_atestado", "auto_ok") for x in r[k]}
        self.assertEqual(tudo, {"SEO-001", "SEO-002"})

    def test_falha_do_check_sem_id_tambem_bloqueia(self):
        r = gate.avaliar(snapshot(self.d, CANON_OK), alvo_com_check(self.d, ["L4"]), atestado=self.AT2, mapa=self.MAPA)
        self.assertEqual(r["bloqueios"], ["GATE-CHECKPY"])

    def test_verificacao_no_proprio_canonico(self):
        t = CANON_OK.replace("- **Severidade:** bloqueante\n- **Status:** ativo\n\n### SEO-002",
                             "- **Severidade:** bloqueante\n- **Status:** ativo\n- **Verificação:** auto:R5,R6\n\n### SEO-002", 1)
        r = gate.avaliar(snapshot(self.d, t), alvo_com_check(self.d, ["R6"]), atestado=self.AT2, mapa={})
        self.assertEqual(r["bloqueios"], ["SEO-001"])

    def test_check_ausente_vira_manual(self):
        a = self.d / "vazio"
        a.mkdir()
        r = gate.avaliar(snapshot(self.d, CANON_OK), a, atestado=self.AT2, mapa=self.MAPA)
        self.assertEqual(r["bloqueios"], ["SEO-001 (manual pendente)"])

    def test_cli_exit_code_e_readme(self):
        readme = self.d / "README.md"
        readme.write_text("# x\n\n## Validação SEO por PR\n\n| Data (America/Bahia) | PR | Commit | Versão do canônico lida (arquivo · sha256) | Resultado |\n|---|---|---|---|---|\n\nNota abaixo da tabela.\n\n## Outra\n", encoding="utf-8")
        rc = gate.main(["--canonico", str(self.d / "nada.meta.json"), "--alvo", str(alvo_com_check(self.d)),
                        "--pr", "9", "--registrar-readme", str(readme)])
        self.assertEqual(rc, 1)
        t = readme.read_text(encoding="utf-8")
        self.assertIn("| 9 |", t)
        self.assertIn("BLOCK: GATE-CANON-AUSENTE", t)
        self.assertLess(t.index("| 9 |"), t.index("Nota abaixo da tabela."))


CANON_SECOES = """# CANÔNICO SEO — TESTE
Versão 1.0.0 | Data 2026-11-02 | Autor Pitágoras | Aprovação Wagner Sena | Status FONTE DA VERDADE

## 1. REGRA A
Texto da regra A.

## 2. REGRA B
Texto da regra B.
"""


def canon_repo(d: Path, texto=CANON_SECOES, aprovacao=True, rel="docs/CANONICO_SEO.md", sha=None, sev="bloqueante"):
    """Canônico versionado no alvo (formato seções) + meta origem=repo."""
    a = alvo_com_check(d)
    (a / rel).parent.mkdir(parents=True, exist_ok=True)
    (a / rel).write_text(texto, encoding="utf-8")
    meta = {"origem": "repo", "arquivo_repo": rel, "formato": "secoes-numeradas", "prefixo_id": "CANON-SEO",
            "severidade_padrao": sev, "sha256": sha or hashlib.sha256((a / rel).read_bytes()).hexdigest()}
    if aprovacao:
        meta["aprovacao_repo"] = {"por": "Wagner Sena", "data": "2026-11-02", "ref": "t69u"}
    m = d / "repo.meta.json"
    m.write_text(json.dumps(meta), encoding="utf-8")
    return m, a


def at_secoes(**vereditos):
    return {k.replace("_", "-"): {"revisor": "Cortex Build", "data": "2026-11-02", "commit": "", "veredito": v, "motivo": "m"}
            for k, v in vereditos.items()}


class TestCanonicoRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_secoes_ids_mecanicos(self):
        from canonico import parse_secoes
        c = parse_secoes(CANON_SECOES, severidade_padrao="bloqueante", arquivo="docs/CANONICO_SEO.md")
        self.assertEqual(c.versao, "1.0.0")
        self.assertEqual([r.id for r in c.requisitos], ["CANON-SEO-01", "CANON-SEO-02"])
        self.assertTrue(all(r.bloqueante and r.ativo and not r.faltando() for r in c.requisitos))
        self.assertEqual(c.requisitos[0].requisito, "Texto da regra A.")

    def test_repo_aprovado_passa_com_todas_ok(self):
        m, a = canon_repo(self.d)
        r = gate.avaliar(m, a, atestado=at_secoes(CANON_SEO_01="ok", CANON_SEO_02="ok"), mapa={})
        self.assertEqual(r["resultado"], "PASS", r["bloqueios"])

    def test_repo_sem_aprovacao_bloqueia(self):
        m, a = canon_repo(self.d, aprovacao=False)
        r = gate.avaliar(m, a, atestado=at_secoes(CANON_SEO_01="ok", CANON_SEO_02="ok"), mapa={})
        self.assertIn("GATE-CANON-FORA-DA-PASTA", r["bloqueios"])

    def test_excecao_so_para_o_path_aprovado(self):
        m, a = canon_repo(self.d, rel="docs/OUTRO.md")
        r = gate.avaliar(m, a, atestado=at_secoes(CANON_SEO_01="ok", CANON_SEO_02="ok"), mapa={})
        self.assertIn("GATE-CANON-FORA-DA-PASTA", r["bloqueios"])

    def test_canonico_alterado_no_pr_bloqueia(self):
        m, a = canon_repo(self.d, sha="0" * 64)
        r = gate.avaliar(m, a, atestado=at_secoes(CANON_SEO_01="ok", CANON_SEO_02="ok"), mapa={})
        self.assertIn("GATE-CANON-SHA", r["bloqueios"])

    def test_sem_severidade_no_meta_bloqueia(self):
        m, a = canon_repo(self.d, sev="")
        r = gate.avaliar(m, a, mapa={})
        self.assertIn("GATE-CANON-SEM-SEVERIDADE", r["bloqueios"])

    def test_violado_e_pendente_bloqueiam_com_id(self):
        m, a = canon_repo(self.d)
        r = gate.avaliar(m, a, atestado=at_secoes(CANON_SEO_01="violado", CANON_SEO_02="pendente"), mapa={})
        self.assertEqual(r["bloqueios"], ["CANON-SEO-01", "CANON-SEO-02 (manual pendente)"])

    def test_sem_atestado_nao_passa(self):
        m, a = canon_repo(self.d)
        r = gate.avaliar(m, a, mapa={})
        self.assertEqual(r["resultado"], "BLOCK")
        self.assertEqual(len(r["manual_pendente"]), 2)


class TestCanonV110(unittest.TestCase):
    """v1.1.0 (t71u): severidade por seção (§4 = aviso) e aprovação do Wagner (§10)."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_severidade_por_secao_vira_aviso_e_nao_bloqueia(self):
        from canonico import parse_secoes
        c = parse_secoes(CANON_SECOES, severidade_padrao="bloqueante", severidade_por_secao={"CANON-SEO-02": "aviso"})
        self.assertEqual([r.bloqueante for r in c.requisitos], [True, False])

    def test_aviso_aparece_na_saida(self):
        m, a = canon_repo(self.d)
        meta = json.loads(m.read_text()); meta["severidade_por_secao"] = {"CANON-SEO-02": "aviso"}; m.write_text(json.dumps(meta))
        orig = gate.canon_checks.avaliar
        gate.canon_checks.avaliar = lambda alvo: {"CANON-SEO-02": [(False, "slug sem ID")]}
        try:
            r = gate.avaliar(m, a, atestado=at_secoes(CANON_SEO_01="ok"), mapa={})
        finally:
            gate.canon_checks.avaliar = orig
        self.assertEqual(r["resultado"], "PASS", r["bloqueios"])
        self.assertEqual([v["id"] for v in r["avisos"]], ["CANON-SEO-02"])
        self.assertIn("AVISO CANON-SEO-02", gate.texto(r))

    def test_aprovacao_wagner(self):
        ok, _ = gate.aprovacao_wagner({"CANON-SEO-10": {"por": "Wagner Sena", "data": "2026-11-02", "ref": "t71u", "commit": "abc1234ffff"}}, "abc1234")
        self.assertTrue(ok)
        self.assertFalse(gate.aprovacao_wagner({}, "abc1234")[0])
        self.assertFalse(gate.aprovacao_wagner({"CANON-SEO-10": {"por": "Wagner Sena", "data": "d", "ref": "r", "commit": "0000000"}}, "abc1234")[0])
        self.assertFalse(gate.aprovacao_wagner({"CANON-SEO-10": {"por": "Outro", "data": "d", "ref": "r", "commit": "abc1234"}}, "abc1234")[0])

    def test_bio_do_autor_fora_da_citacao_mas_dentro_da_embalagem(self):
        import canon_checks
        a = self.d / "s"; a.mkdir()
        (a / "index.html").write_text('<html><body><p>Texto.</p><section class="about-author"><p>5 estrelas. A conferir.</p></section>'
                                      '<p data-fonte="Declaração do próprio Wagner Sena">Fonte: Google</p><p>grupo Disal</p></body></html>', encoding="utf-8")
        r = canon_checks.avaliar(a)
        self.assertTrue(all(ok for ok, _ in r["CANON-SEO-03"]), r["CANON-SEO-03"])
        self.assertFalse(all(ok for ok, _ in r["CANON-SEO-01"]))

    def test_sem_baseline_lighthouse_falha_cwv(self):
        import canon_checks
        self.assertFalse(canon_checks.cwv(self.d)[0][0])


class TestCanonChecks(unittest.TestCase):
    def test_pr1_real_v110(self):
        """Roda as checagens automáticas no worktree do PR #1, se existir ao lado (../cg-blog)."""
        import canon_checks
        blog = REPO.parent / "cg-blog"
        if not (blog / "artigo-exemplo" / "index.html").exists():
            self.skipTest("worktree do blog ausente")
        res = canon_checks.avaliar(blog)
        falhou = {k for k, v in res.items() if any(not ok for ok, _ in v)}
        self.assertTrue({"CANON-SEO-07", "CANON-SEO-08"} <= falhou, falhou)  # capas placeholder sem FR-001
        self.assertIn("CANON-SEO-04", falhou)  # slug sem ID (aviso na v1.1.0)
        self.assertNotIn("CANON-SEO-01", falhou)
        self.assertNotIn("CANON-SEO-03", falhou)


if __name__ == "__main__":
    unittest.main(verbosity=2)
