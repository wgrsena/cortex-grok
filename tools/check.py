#!/usr/bin/env python3
"""Check do blog (stdlib pura). Uso: python3 tools/check.py   → exit 0 se não houver FALHA.

FALHA = viola requisito (bloqueia commit/publicação). AVISO = pendência conhecida (TODO).
Regras numeradas como no checklist do README (R1–R12) + regras do lab (L1–L6).
"""
import json
import re
import struct
import sys
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
GIRO = "https://programagiroautomotivo.com.br/wagner"
DST_OK = {"trainedAlgorithmicMedia", "compositeSynthetic", "algorithmicMedia", "compositeWithTrainedAlgorithmicMedia"}

PROIBIDAS = [
    r"garantid[oa]s?", r"garantimos", r"contempla[çc][ãa]o\s+(certa|imediata|r[áa]pida|assegurada)",
    r"prazo\s+(certo|fixo\s+de\s+contempla)", r"sem\s+juros", r"aprova[çc][ãa]o\s+(imediata|na\s+hora)",
    r"100\s*%\s*(seguro|certo|aprovado)", r"renda\s+extra", r"melhor\s+investimento", r"sem\s+risco",
    r"lucro\s+certo", r"contemplado\s+em\s+\d+",
]
CLICKBAIT = [r"voc[êe] n[ãa]o vai acreditar", r"segredo", r"chocante", r"imperd[íi]vel", r"urgente",
             r"[úu]ltim[oa]s? (dia|chance|vagas)", r"ningu[ée]m (te )?conta", r"!{2,}", r"\?!", r"truque"]
NUM_SEM_FONTE = re.compile(r"(\d[\d.,]*\s*%|R\$\s*\d|\b\d+\s*(dias|meses|anos|parcelas)\b)", re.I)


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find_all(self, tag=None, cls=None):
        return [n for n in self.iter() if (tag is None or n.tag == tag)
                and (cls is None or cls in n.attrs.get("class", "").split())]

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent

    def has_class_up(self, cls):
        return any(cls in a.attrs.get("class", "").split() for a in self.ancestors())

    def elem_children(self):
        return [c for c in self.children if isinstance(c, Node)]


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root
        self.comments = []

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)

    def handle_comment(self, data):
        self.comments.append(data)


def png_info(path: Path):
    """(largura, altura, DigitalSourceType|None, título XMP) lendo IHDR e iTXt XMP."""
    b = path.read_bytes()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", b[16:24])
    i, xmp = 8, ""
    while i < len(b):
        ln = struct.unpack(">I", b[i:i + 4])[0]
        tipo, dados = b[i + 4:i + 8], b[i + 8:i + 8 + ln]
        if tipo == b"iTXt" and dados.startswith(b"XML:com.adobe.xmp\x00"):
            resto = dados[len(b"XML:com.adobe.xmp\x00"):]
            comp, _met = resto[0], resto[1]
            resto = resto[2:]
            resto = resto.split(b"\x00", 2)[2]  # pula language tag e translated keyword
            xmp = (zlib.decompress(resto) if comp else resto).decode("utf-8", "replace")
        i += 12 + ln
    m = re.search(r"digitalsourcetype/(\w+)", xmp)
    t = re.search(r'<rdf:li[^>]*>([^<]*)</rdf:li>', xmp)
    return w, h, (m.group(1) if m else None), (t.group(1) if t else "")


class Rel:
    def __init__(self):
        self.falhas, self.avisos, self.oks = [], [], 0

    def ok(self, cond, regra, msg, aviso=False):
        if cond:
            self.oks += 1
        else:
            (self.avisos if aviso else self.falhas).append(f"[{regra}] {msg}")


def url_local(url: str) -> Path:
    return ROOT / urlsplit(url).path.lstrip("/")


def page_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    rel = rel[:-len("index.html")] if rel.endswith("index.html") else rel
    return f"{BASE}/{rel}"


def checar_cta(a: Node, r: Rel, onde: str):
    href = a.attrs.get("href", "")
    u = urlsplit(href)
    q = parse_qs(u.query)
    host = u.hostname or ""
    r.ok(host in CFG["dominios_cta"], "L1", f"{onde}: CTA fora de wa.me/cortexconecta.com.br: {href}")
    r.ok(q.get("utm_campaign") == [CFG["etiqueta_origem"]], "L2", f"{onde}: CTA sem utm_campaign={CFG['etiqueta_origem']}: {href}")
    r.ok(q.get("ref") == [CFG["codigo_fluxo"]], "L2", f"{onde}: CTA sem ref={CFG['codigo_fluxo']}: {href}")
    if host == "wa.me":
        num = u.path.strip("/")
        r.ok(num == CFG["whatsapp_oficial"], "L3", f"{onde}: número do wa.me ({num}) diferente de config/site.json")
        r.ok(CFG["codigo_fluxo"] in unquote(q.get("text", [""])[0]), "L2", f"{onde}: texto pré-preenchido do wa.me sem {CFG['codigo_fluxo']}")


def checar_pagina(path: Path, r: Rel, sitemap_urls: set):
    b = Builder()
    b.feed(path.read_text(encoding="utf-8"))
    doc, nome = b.root, path.relative_to(ROOT).as_posix()
    url = page_url(path)
    head_meta = {m.attrs.get("name") or m.attrs.get("property"): m.attrs.get("content", "") for m in doc.find_all("meta")}

    # L4 noindex até aprovação + coerência com sitemap
    robots = head_meta.get("robots", "")
    aprovada = nome in CFG["paginas_aprovadas_wagner"]
    if aprovada:
        r.ok("noindex" not in robots, "L4", f"{nome}: aprovada pelo Wagner mas ainda com noindex")
        r.ok(url in sitemap_urls, "L4", f"{nome}: aprovada mas fora do sitemap.xml")
    else:
        r.ok("noindex" in robots, "L4", f"{nome}: página nova sem <meta name=robots content=noindex>")
        r.ok(url not in sitemap_urls, "L4", f"{nome}: página com noindex listada no sitemap.xml")
    r.ok("max-image-preview:large" in robots, "R3", f"{nome}: falta max-image-preview:large (Discover)")

    # L5 canonical/og:url no subdomínio
    canon = [l.attrs.get("href") for l in doc.find_all("link") if l.attrs.get("rel") == "canonical"]
    r.ok(canon == [url], "L5", f"{nome}: canonical {canon} ≠ {url}")
    r.ok(head_meta.get("og:url") == url, "L5", f"{nome}: og:url ≠ canonical")

    # R7 width/height em tudo que ocupa espaço
    for n in doc.iter():
        if n.tag in ("img", "iframe", "embed", "video", "object") or (n.tag == "source" and n.parent.tag == "picture"):
            wh = all(re.fullmatch(r"\d+", n.attrs.get(k, "") or "") for k in ("width", "height"))
            r.ok(wh, "R7", f"{nome}: <{n.tag} {n.attrs.get('src') or n.attrs.get('srcset')}> sem width/height numéricos")

    # R5/R6 capa: sem lazy, fetchpriority=high; e só a capa com high
    capas = [n for n in doc.find_all("img") if n.has_class_up("cover") or n.has_class_up("featured")]
    r.ok(len(capas) >= 1, "R5", f"{nome}: nenhuma imagem de capa encontrada (.cover/.featured)")
    for c in capas[:1]:
        r.ok(c.attrs.get("loading") != "lazy", "R5", f"{nome}: capa com loading=lazy")
        r.ok(c.attrs.get("fetchpriority") == "high", "R6", f"{nome}: capa sem fetchpriority=high")
    altas = [n for n in doc.find_all("img") if n.attrs.get("fetchpriority") == "high"]
    r.ok(len(altas) <= 1, "R6", f"{nome}: mais de uma imagem com fetchpriority=high")

    # R1/R2/R3/R8 imagens das capas: arquivo, proporção, pixels, largura, IPTC
    # (foto real do autor em .author-photo não é banner: fica fora de R1–R3/R8, mas segue R5–R7)
    banners = [c for c in capas if not c.has_class_up("author-photo")]
    srcs = {c.attrs.get("src") for c in banners} | {s.attrs.get("srcset") for c in banners for s in c.parent.find_all("source")}
    for s in filter(None, srcs):
        checar_imagem((path.parent / s).resolve(), r, nome)

    # JSON-LD
    ld = []
    for s in doc.find_all("script"):
        if s.attrs.get("type") == "application/ld+json":
            try:
                ld.append(json.loads(s.text()))
            except json.JSONDecodeError as e:
                r.ok(False, "R1", f"{nome}: JSON-LD inválido: {e}")
    artigos = [d for d in ld if d.get("@type") in ("Article", "BlogPosting", "NewsArticle")]
    if "artigo" in nome or doc.find_all("article", "article"):
        r.ok(len(artigos) == 1, "R1", f"{nome}: precisa de exatamente 1 JSON-LD Article")
        for a in artigos:
            imgs = a.get("image", [])
            r.ok(isinstance(imgs, list) and len(imgs) == 3, "R1", f"{nome}: JSON-LD image deve ter 3 URLs (16:9, 4:3, 1:1)")
            props = set()
            for u in imgs if isinstance(imgs, list) else []:
                r.ok(u.startswith(BASE + "/"), "R1", f"{nome}: imagem do JSON-LD fora do subdomínio: {u}")
                info = checar_imagem(url_local(u), r, nome)
                if info:
                    w, h = info[0], info[1]
                    props.add(min(("16x9", 16 / 9), ("4x3", 4 / 3), ("1x1", 1.0), key=lambda p: abs(p[1] - w / h))[0])
            r.ok(props == {"16x9", "4x3", "1x1"}, "R1", f"{nome}: proporções no JSON-LD = {sorted(props)}")
            for k in ("headline", "datePublished", "dateModified", "publisher"):
                r.ok(k in a, "R1", f"{nome}: JSON-LD sem {k}")
            autores = a.get("author") or []
            autores = autores if isinstance(autores, list) else [autores]
            r.ok(any(x.get("@type") == "Person" and x.get("name") and x.get("image") for x in autores),
                 "R9", f"{nome}: author precisa ser Person com name e image")
            r.ok(not any("TODO" in json.dumps(x) for x in autores), "R9", f"{nome}: autor ainda é placeholder (TODO)", aviso=True)

        # L6 fim do artigo: CTA no texto com código FR
        prose = doc.find_all("div", "prose")
        ultimo = prose[0].elem_children()[-1] if prose and prose[0].elem_children() else None
        links = ultimo.find_all("a", "cta") if ultimo is not None else []
        r.ok(ultimo is not None and ultimo.tag == "p" and links, "L6", f"{nome}: artigo não termina com parágrafo contendo link de CTA")
        for a in links:
            r.ok(re.search(r"\bFR-\d{3,}\b", a.text()) is not None, "L6", f"{nome}: texto do CTA final sem código FR")
            r.ok(CFG["codigo_fluxo"] in a.text(), "L6", f"{nome}: texto do CTA final sem {CFG['codigo_fluxo']}")

        # R12 número sem fonte (fora do bloco .sources e sem data-fonte)
        for p in prose[:1]:
            for n in p.iter():
                if n.tag in ("p", "li") and not n.has_class_up("sources") and "data-fonte" not in n.attrs \
                        and not any("data-fonte" in x.attrs for x in n.ancestors()):
                    m = NUM_SEM_FONTE.search(n.text())
                    r.ok(m is None, "R12", f"{nome}: número sem fonte: “{m.group(0) if m else ''}” — marque o elemento com data-fonte e cite a fonte")
        r.ok(bool(doc.find_all(cls="sources")), "R12", f"{nome}: artigo sem bloco de fontes")
        r.ok(bool(doc.find_all(cls="notice")), "R10", f"{nome}: artigo YMYL sem aviso")

    # L1 sem <button>; CTAs válidos; links externos só CTA ou fontes
    r.ok(not doc.find_all("button"), "L6", f"{nome}: <button> encontrado (CTA deve ser link no texto)")
    for a in doc.find_all("a"):
        href = a.attrs.get("href", "")
        host = urlsplit(href).hostname
        if "cta" in a.attrs.get("class", "").split() or host == "wa.me":
            checar_cta(a, r, nome)
        elif host:
            perfil = href in CFG.get("perfis_autor", [])
            r.ok(a.has_class_up("sources") or perfil, "L1", f"{nome}: link externo que não é CTA, fonte nem perfil do autor: {href}")
        # L7 Giro Automotivo citado = link para o perfil do Wagner no programa
        if "giro automotivo" in a.text().lower():
            r.ok(href == GIRO, "L7", f"{nome}: link do Giro Automotivo deve ser {GIRO}")
    for n in doc.iter():
        if n.tag in ("p", "li") and "giro automotivo" in n.text().lower():
            r.ok(any(x.attrs.get("href") == GIRO for x in n.find_all("a")), "L7", f"{nome}: Giro Automotivo citado sem link para {GIRO}")

    # R4/R10/R11 vocabulário proibido e clickbait
    visivel = " ".join([doc.text(), head_meta.get("description", "")] + [i.attrs.get("alt", "") for i in doc.find_all("img")])
    visivel = re.sub(r"\{[\s\S]*?\}\s*$", " ", visivel)
    for pad in PROIBIDAS:
        m = re.search(pad, visivel, re.I)
        r.ok(m is None, "R10/R11", f"{nome}: termo proibido em YMYL: “{m.group(0) if m else ''}”")
    titulos = [t.text() for t in doc.find_all("title")] + [h.text() for h in doc.iter() if h.tag in ("h1", "h2", "h3")] \
        + [head_meta.get("og:title", "")]
    for t in titulos:
        for pad in CLICKBAIT:
            r.ok(re.search(pad, t, re.I) is None, "R4", f"{nome}: título com cara de clickbait: “{t.strip()}”")
        r.ok(not re.search(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{5,}\b(?:\s+\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{5,}\b)", t), "R4", f"{nome}: título em CAIXA ALTA: “{t.strip()}”")
    h1 = doc.find_all("h1")
    r.ok(len(h1) == 1, "L5", f"{nome}: precisa de exatamente 1 h1 (tem {len(h1)})")

    # Avisos de pendência
    r.ok("TODO" not in doc.text(), "PEND", f"{nome}: há marcadores TODO visíveis na página", aviso=True)


_cache = {}


def checar_imagem(p: Path, r: Rel, nome: str):
    if p in _cache:
        return _cache[p]
    r.ok(p.exists(), "R1", f"{nome}: imagem não existe: {p.relative_to(ROOT) if ROOT in p.parents else p}")
    info = png_info(p) if p.exists() and p.suffix == ".png" else None
    if p.exists() and p.suffix != ".png":
        r.ok(False, "R8", f"{p.name}: formato não-PNG — o check lê só PNG; confira IPTC com exiftool", aviso=True)
    if info:
        w, h, dst, titulo = info
        r.ok(w * h >= 50000, "R2", f"{p.name}: {w}x{h} = {w*h} px (< 50.000)")
        r.ok(w >= 1200, "R3", f"{p.name}: largura {w}px (< 1200, Discover)")
        r.ok(dst in DST_OK, "R8", f"{p.name}: sem IPTC DigitalSourceType válido (achado: {dst})")
        r.ok("PLACEHOLDER" not in titulo, "PEND", f"{p.name}: imagem ainda é placeholder (trocar pela arte final com trainedAlgorithmicMedia)", aviso=True)
    _cache[p] = info
    return info


def main():
    r = Rel()
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_urls = set(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", re.sub(r"<!--[\s\S]*?-->", "", sm)))
    rb = (ROOT / "robots.txt").read_text(encoding="utf-8")
    r.ok(not re.search(r"^\s*Disallow:\s*/\s*$", rb, re.M), "L4", "robots.txt bloqueia o site (Disallow: /)")
    r.ok(f"Sitemap: {BASE}/sitemap.xml" in rb, "L4", "robots.txt sem linha Sitemap")
    r.ok(CFG["whatsapp_oficial"] != CFG["whatsapp_placeholder"], "PEND", "número oficial do WhatsApp ainda é placeholder (config/site.json)", aviso=True)
    paginas = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    for p in paginas:
        checar_pagina(p, r, sitemap_urls)
    print(f"Páginas: {len(paginas)} · checagens OK: {r.oks} · FALHAS: {len(r.falhas)} · avisos: {len(r.avisos)}")
    for f in r.falhas:
        print("FALHA", f)
    for a in sorted(set(r.avisos)):
        print("AVISO", a)
    sys.exit(1 if r.falhas else 0)


if __name__ == "__main__":
    main()
