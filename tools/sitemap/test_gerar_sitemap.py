#!/usr/bin/env python3
"""Testes do gerador de sitemap/robots (unittest, stdlib). Uso: python3 tools/sitemap/test_gerar_sitemap.py"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
GERADOR = Path("tools") / "sitemap" / "gerar_sitemap.py"
BOTS = ["GPTBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Amazonbot",
        "CCBot", "Bytespider", "anthropic-ai", "cohere-ai", "Applebot-Extended", "Meta-ExternalAgent"]


def rodar(raiz: Path, *args, script=GERADOR):
    p = subprocess.run([sys.executable, str(raiz / script), *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def urls(raiz: Path):
    arv = ET.parse(raiz / "sitemap.xml").getroot()
    return {u.find("s:loc", NS).text: {c.tag.split("}")[1]: c.text for c in u} for u in arv.findall("s:url", NS)}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name) / "site"
        shutil.copytree(ROOT, self.raiz, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def tearDown(self):
        self._tmp.cleanup()

    def cfg(self, **kw):
        p = self.raiz / "config" / "site.json"
        c = json.loads(p.read_text(encoding="utf-8"))
        c.update(kw)
        p.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")

    def aprovar(self, *rels, tirar_noindex=True):
        for rel in rels:
            f = self.raiz / rel
            t = f.read_text(encoding="utf-8")
            if tirar_noindex:
                t = t.replace('content="noindex, max-image-preview:large"', 'content="max-image-preview:large"')
            f.write_text(t, encoding="utf-8")
        self.cfg(paginas_aprovadas_wagner=list(rels))

    def novo_artigo(self, slug, data):
        d = self.raiz / slug
        d.mkdir()
        t = (self.raiz / "artigo-exemplo" / "index.html").read_text(encoding="utf-8")
        t = t.replace("/artigo-exemplo/", f"/{slug}/").replace("2026-11-01T09:00:00-03:00", f"{data}T09:00:00-03:00")
        (d / "index.html").write_text(t, encoding="utf-8")


class TestRepo(unittest.TestCase):
    def test_arquivos_do_repo_em_dia(self):
        code, out = rodar(ROOT, "--check")
        self.assertEqual(code, 0, out)

    def test_hoje_sitemap_vazio_e_valido(self):
        self.assertEqual(urls(ROOT), {})
        sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://lab.cortexconecta.com.br/artigo-exemplo/ [destaque, prioridade 0.9]", sm)


class TestSitemap(Base):
    def test_aprovadas_entram_com_prioridade_lastmod_e_changefreq(self):
        self.aprovar("index.html", "artigo-exemplo/index.html")
        self.assertEqual(rodar(self.raiz)[0], 0)
        u = urls(self.raiz)
        self.assertEqual(u["https://lab.cortexconecta.com.br/"],
                         {"loc": "https://lab.cortexconecta.com.br/", "lastmod": "2026-11-01", "changefreq": "weekly", "priority": "1.0"})
        self.assertEqual(u["https://lab.cortexconecta.com.br/artigo-exemplo/"]["priority"], "0.9")
        self.assertEqual(u["https://lab.cortexconecta.com.br/artigo-exemplo/"]["lastmod"], "2026-11-01")
        code, out = rodar(self.raiz, script=Path("tools") / "check.py")
        self.assertEqual(code, 0, out)

    def test_artigo_comum_08_e_home_com_data_mais_recente(self):
        self.novo_artigo("outro-artigo", "2026-11-05")
        self.aprovar("index.html", "artigo-exemplo/index.html", "outro-artigo/index.html")
        rodar(self.raiz)
        u = urls(self.raiz)
        self.assertEqual(u["https://lab.cortexconecta.com.br/outro-artigo/"]["priority"], "0.8")
        self.assertEqual(u["https://lab.cortexconecta.com.br/outro-artigo/"]["lastmod"], "2026-11-05")
        self.assertEqual(u["https://lab.cortexconecta.com.br/"]["lastmod"], "2026-11-05")
        self.assertTrue(all(k.startswith("https://") for k in u))

    def test_aprovada_com_noindex_fica_fora(self):
        self.aprovar("artigo-exemplo/index.html", tirar_noindex=False)
        rodar(self.raiz)
        self.assertEqual(urls(self.raiz), {})
        self.assertIn("aprovada mas ainda com noindex", (self.raiz / "sitemap.xml").read_text(encoding="utf-8"))

    def test_dominio_vem_do_config(self):
        self.aprovar("index.html")
        self.cfg(base_url="https://exemplo.com.br/")
        rodar(self.raiz)
        self.assertEqual(list(urls(self.raiz)), ["https://exemplo.com.br/"])
        self.assertIn("Sitemap: https://exemplo.com.br/sitemap.xml", (self.raiz / "robots.txt").read_text(encoding="utf-8"))


class TestRobots(Base):
    def test_bots_de_ia_liberados_e_disallow_so_do_que_existe(self):
        shutil.rmtree(self.raiz / "docs")
        rodar(self.raiz)
        rb = (self.raiz / "robots.txt").read_text(encoding="utf-8")
        grupos = [g for g in rb.split("\n\n") if "User-agent:" in g]
        for bot in BOTS + ["*"]:
            g = next(g for g in grupos if f"User-agent: {bot}\n" in g)
            self.assertIn("Allow: /\n", g)
            self.assertNotRegex(g, r"Disallow: /\n")
            self.assertIn("Disallow: /tools/", g)
            self.assertNotIn("/docs/", g)
        self.assertTrue(rb.rstrip().endswith("Sitemap: https://lab.cortexconecta.com.br/sitemap.xml"))


class TestCheckL7(Base):
    def test_sitemap_editado_a_mao_falha(self):
        f = self.raiz / "sitemap.xml"
        f.write_text(f.read_text(encoding="utf-8").replace("<urlset", "<!-- x --><urlset"), encoding="utf-8")
        code, out = rodar(self.raiz, script=Path("tools") / "check.py")
        self.assertEqual(code, 1, out)
        self.assertIn("[L7] sitemap.xml desatualizado", out)

    def test_bot_bloqueado_falha(self):
        f = self.raiz / "robots.txt"
        f.write_text(f.read_text(encoding="utf-8").replace("User-agent: GPTBot\nAllow: /", "User-agent: GPTBot\nDisallow: /"), encoding="utf-8")
        code, out = rodar(self.raiz, script=Path("tools") / "check.py")
        self.assertEqual(code, 1, out)
        self.assertIn("[L7] robots.txt não libera GPTBot", out)

    def test_placeholder_conectacortex_diverge_do_canonical(self):
        """Documenta a divergência: com base_url=https://conectacortex.com.br o canonical das páginas
        (lab.cortexconecta.com.br) deixa de bater e o check reprova (L5/L1 do JSON-LD)."""
        self.cfg(base_url="https://conectacortex.com.br")
        rodar(self.raiz)
        code, out = rodar(self.raiz, script=Path("tools") / "check.py")
        self.assertEqual(code, 1, out)
        self.assertIn("[L5]", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
