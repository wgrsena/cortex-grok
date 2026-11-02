#!/usr/bin/env python3
"""Gera sitemap.xml e robots.txt a partir dos posts do blog (Python stdlib pura).

Uso:
  python3 tools/sitemap/gerar_sitemap.py            grava sitemap.xml e robots.txt na raiz
  python3 tools/sitemap/gerar_sitemap.py --check    exit 1 se os arquivos da raiz estiverem desatualizados
  python3 tools/sitemap/gerar_sitemap.py --preview  lista todas as páginas candidatas (inclusive as com noindex)

Fonte dos posts: todo index.html do repo. Home = /index.html. Artigo = página com JSON-LD
Article/BlogPosting/NewsArticle; lastmod = data de datePublished. Destaque = página apontada pelo
primeiro link de <article class="featured"> da home.
Prioridade: home 1.0 · artigo em destaque 0.9 · demais artigos 0.8. changefreq weekly.
Lastmod da home = publicação mais recente entre os artigos.

Só entra no sitemap página aprovada pelo Wagner (config/site.json › paginas_aprovadas_wagner) e sem
noindex. As demais ficam listadas num comentário do XML como pendentes (regra L4 do check.py).
Domínio: config/site.json › base_url (valor único para canonical, sitemap e robots).
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
TIPOS_ARTIGO = {"Article", "BlogPosting", "NewsArticle"}
PRIORIDADE = {"home": "1.0", "destaque": "0.9", "artigo": "0.8"}
IGNORAR = {".git", "tools", "node_modules"}


class _Pagina(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.robots, self.ld, self.featured_href = "", [], None
        self._in_ld, self._buf, self._featured_depth = False, [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and (a.get("name") or "").lower() == "robots":
            self.robots = (a.get("content") or "").lower()
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld, self._buf = True, []
        elif tag == "article" and "featured" in (a.get("class") or "").split():
            self._featured_depth = 1
        elif tag == "article" and self._featured_depth:
            self._featured_depth += 1
        elif tag == "a" and self._featured_depth and self.featured_href is None and a.get("href"):
            self.featured_href = a["href"]

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self._in_ld = False
            try:
                d = json.loads("".join(self._buf))
            except json.JSONDecodeError:
                return
            self.ld.extend(d if isinstance(d, list) else [d])
        elif tag == "article" and self._featured_depth:
            self._featured_depth -= 1

    def handle_data(self, data):
        if self._in_ld:
            self._buf.append(data)


def _ler(path: Path) -> _Pagina:
    p = _Pagina()
    p.feed(path.read_text(encoding="utf-8"))
    return p


def _url(base: str, rel: str) -> str:
    rel = rel[: -len("index.html")] if rel.endswith("index.html") else rel
    return f"{base}/{rel}"


def coletar(root: Path = ROOT):
    """Lista de dicts {rel, url, tipo, lastmod, prioridade, indexavel, motivo} de todas as páginas candidatas."""
    cfg = json.loads((root / "config" / "site.json").read_text(encoding="utf-8"))
    base = cfg["base_url"].rstrip("/")
    aprovadas = set(cfg.get("paginas_aprovadas_wagner", []))
    paginas = sorted(p for p in root.rglob("index.html") if not IGNORAR & set(p.relative_to(root).parts))
    lidas = {p.relative_to(root).as_posix(): _ler(p) for p in paginas}

    destaque = None
    home = lidas.get("index.html")
    if home and home.featured_href:
        alvo = urlsplit(urljoin(f"{base}/", home.featured_href)).path.lstrip("/")
        destaque = (alvo.rstrip("/") + "/index.html").lstrip("/") if not alvo.endswith(".html") else alvo

    itens = []
    for rel, pg in lidas.items():
        artigos = [d for d in pg.ld if isinstance(d, dict) and d.get("@type") in TIPOS_ARTIGO]
        if rel == "index.html":
            tipo, data = "home", None
        elif artigos:
            tipo = "destaque" if rel == destaque else "artigo"
            m = re.match(r"\d{4}-\d{2}-\d{2}", str(artigos[0].get("datePublished", "")))
            data = m.group(0) if m else None
        else:
            continue  # página sem Article (ex.: página institucional) fica fora até ter regra própria
        motivo = None
        if rel not in aprovadas:
            motivo = "não aprovada pelo Wagner"
        elif "noindex" in pg.robots:
            motivo = "aprovada mas ainda com noindex"
        elif tipo != "home" and not data:
            motivo = "sem datePublished no JSON-LD"
        itens.append({"rel": rel, "url": _url(base, rel), "tipo": tipo, "lastmod": data,
                      "prioridade": PRIORIDADE[tipo], "indexavel": motivo is None, "motivo": motivo})

    datas = [i["lastmod"] for i in itens if i["tipo"] != "home" and i["lastmod"]]
    for i in itens:
        if i["tipo"] == "home":
            i["lastmod"] = max(datas) if datas else None
    ordem = {"home": 0, "destaque": 1, "artigo": 2}
    itens.sort(key=lambda i: (ordem[i["tipo"]], -int((i["lastmod"] or "0").replace("-", "")), i["rel"]))
    return cfg, itens


def gerar_sitemap(root: Path = ROOT) -> str:
    _cfg, itens = coletar(root)
    pend = [i for i in itens if not i["indexavel"]]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           "<!-- GERADO por tools/sitemap/gerar_sitemap.py. Não editar à mão.",
           "     Só entram páginas aprovadas pelo Wagner e sem noindex (README › Aprovação)."]
    if pend:
        out.append("     Pendentes (fora do sitemap):")
        out += [f"       {escape(i['url'])} [{i['tipo']}, prioridade {i['prioridade']}] — {i['motivo']}" for i in pend]
    out[-1] += " -->"
    out.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for i in itens:
        if not i["indexavel"]:
            continue
        out.append("  <url>")
        out.append(f"    <loc>{escape(i['url'])}</loc>")
        if i["lastmod"]:
            out.append(f"    <lastmod>{i['lastmod']}</lastmod>")
        out.append("    <changefreq>weekly</changefreq>")
        out.append(f"    <priority>{i['prioridade']}</priority>")
        out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def gerar_robots(root: Path = ROOT) -> str:
    cfg = json.loads((root / "config" / "site.json").read_text(encoding="utf-8"))
    base = cfg["base_url"].rstrip("/")
    disallow = [d for d in cfg.get("robots_disallow", []) if (root / d.strip("/")).exists()]
    corpo = ["Allow: /"] + [f"Disallow: {d}" for d in disallow]
    out = ["# GERADO por tools/sitemap/gerar_sitemap.py a partir de config/site.json. Não editar à mão.",
           "# Não bloquear páginas aqui: o noindex fica na meta tag de cada página, e o Google",
           "# só enxerga o noindex se puder rastrear a página (diário Pitágoras, seção 9).",
           "# Disallow só para pastas internas do repo (ferramentas, config, docs), repetido em cada grupo",
           "# porque o crawler segue apenas o grupo mais específico que casa com ele.",
           "", "# Crawlers de IA liberados explicitamente"]
    for bot in cfg.get("crawlers_ia", []):
        out += [f"User-agent: {bot}"] + corpo + [""]
    out += ["# Demais crawlers", "User-agent: *"] + corpo + ["", f"Sitemap: {base}/sitemap.xml"]
    return "\n".join(out) + "\n"


def desatualizados(root: Path = ROOT):
    """Arquivos da raiz cujo conteúdo difere do que o gerador produziria."""
    esperado = {"sitemap.xml": gerar_sitemap(root), "robots.txt": gerar_robots(root)}
    return [n for n, t in esperado.items()
            if not (root / n).exists() or (root / n).read_text(encoding="utf-8") != t]


def main(argv):
    if "--preview" in argv:
        _cfg, itens = coletar(ROOT)
        for i in itens:
            print(f"{i['prioridade']}  {i['lastmod'] or '-':10}  {i['tipo']:8}  {i['url']}  "
                  f"{'INDEXÁVEL' if i['indexavel'] else 'pendente: ' + i['motivo']}")
        return 0
    if "--check" in argv:
        d = desatualizados(ROOT)
        for n in d:
            print(f"desatualizado: {n} — rode python3 tools/sitemap/gerar_sitemap.py")
        return 1 if d else 0
    (ROOT / "sitemap.xml").write_text(gerar_sitemap(ROOT), encoding="utf-8")
    (ROOT / "robots.txt").write_text(gerar_robots(ROOT), encoding="utf-8")
    _cfg, itens = coletar(ROOT)
    print(f"sitemap.xml: {sum(i['indexavel'] for i in itens)} URL(s) · pendentes: {sum(not i['indexavel'] for i in itens)} · robots.txt gravado")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
