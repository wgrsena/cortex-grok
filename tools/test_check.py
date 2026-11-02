#!/usr/bin/env python3
"""Autoteste do check: cada mutação proibida precisa gerar FALHA. Uso: python3 tools/test_check.py"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = "artigo-exemplo/index.html"
AUTOR = "autor/wagner-sena/index.html"

MUTACOES = {
    "capa com lazy": ('fetchpriority="high"', 'fetchpriority="high" loading="lazy"', "[R5]"),
    "sem noindex": ('content="noindex, max-image-preview:large"', 'content="max-image-preview:large"', "[L4]"),
    "promessa": ("Na prática:", "Contemplação garantida. Na prática:", "[R10/R11]"),
    "número sem fonte": ("Na prática:", "Até 40% de lance. Na prática:", "[R12]"),
    "prazo sem fonte": ("Na prática:", "Contemplação em 6 meses. Na prática:", "[R12]"),
    "botão": ('<p class="cta-end">', '<button>WhatsApp</button><p class="cta-end">', "[L6]"),
    "CTA sem FR": ("artigo FR-001 (FLUXO-REV)”", "artigo”", "[L6]"),
    "img sem dimensões": ('width="56" height="56" ', "", "[R7]"),
    "CTA sem ref": ("ref=FLUXO-REV", "ref=X", "[L2]"),
    "clickbait": ("<h1>Como funciona", "<h1>O segredo de como funciona", "[R4]"),
    "autor: foto com lazy": ('fetchpriority="high"', 'fetchpriority="high" loading="lazy"', "[R5]", AUTOR),
    "autor: link externo solto": ('<li><a href="https://www.linkedin.com/in/wgrsena"', '<li><a href="https://exemplo.com/"', "[L1]", AUTOR),
    "autor: Giro sem link": ('No YouTube, está no <a href="https://programagiroautomotivo.com.br/wagner" rel="noopener">Giro Automotivo</a>.', "No YouTube, está no Giro Automotivo.", "[L7]", AUTOR),
    "autor: sem noindex": ('content="noindex, max-image-preview:large"', 'content="max-image-preview:large"', "[L4]", AUTOR),
}


def rodar(raiz: Path):
    p = subprocess.run([sys.executable, str(raiz / "tools" / "check.py")], capture_output=True, text=True)
    return p.returncode, p.stdout


class TestCheck(unittest.TestCase):
    def test_base_passa(self):
        code, out = rodar(ROOT)
        self.assertEqual(code, 0, out)

    def test_mutacoes_falham(self):
        for nome, (de, para, regra, *arq) in MUTACOES.items():
            with self.subTest(nome), tempfile.TemporaryDirectory() as tmp:
                raiz = Path(tmp) / "site"
                shutil.copytree(ROOT, raiz, ignore=shutil.ignore_patterns(".git"))
                f = raiz / (arq[0] if arq else ART)
                t = f.read_text(encoding="utf-8")
                self.assertIn(de, t)
                f.write_text(t.replace(de, para, 1), encoding="utf-8")
                code, out = rodar(raiz)
                self.assertEqual(code, 1, f"{nome}: deveria falhar\n{out}")
                self.assertIn(regra, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
