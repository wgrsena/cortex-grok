"""Checagens automáticas do blog contra as seções do docs/CANONICO_SEO.md v1.0.0 (stdlib pura).

Cada checagem cobre só a parte mecânica da seção (cobertura PARCIAL). A falha de uma checagem viola o ID;
o OK de todas não basta para passar: a seção ainda precisa de atestado manual (revisor + data + commit).
Lê o HTML gerado e o XMP bruto das imagens (sem exiftool, sem dependência nova).

ID de criativo: regex do FR-SPEC v1.1.0 §2 (Midas), `BLOG-AAAAMMDD-<proporção>[-vN]`.
Proporções exigidas (§8): 9x16, 1x1, 4x5, 16x9. Largura mínima (§7): 1080 px.
"""
import json
import re
import struct
from html.parser import HTMLParser
from pathlib import Path

RE_ID_CRIATIVO = re.compile(r"BLOG-\d{8}-(?:1x1|4x5|16x9|9x16)(?:-v\d+)?", re.I)
RE_ID_CRIATIVO_SLUG = re.compile(r"blog-\d{8}", re.I)  # slug: basta conter o prefixo do ID (data do render)
PROPORCOES = {"9x16": 9 / 16, "1x1": 1.0, "4x5": 4 / 5, "16x9": 16 / 9}
GIRO = "programagiroautomotivo.com.br"
IGNORAR = {".git", "tools", "docs", "node_modules", "__pycache__"}


class _Pag(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.texto, self.ldjson, self.links, self.imgs = [], [], [], []
        self._ld = None
        self._skip = 0
        self.secoes = {}      # classe/aria → [hrefs]
        self._pilha = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("type") == "application/ld+json":
            self._ld = []
        elif tag in ("script", "style"):
            self._skip += 1
        if tag in ("section", "div", "article") and (a.get("class") or a.get("aria-labelledby")):
            self._pilha.append((tag, (a.get("class") or "") + " " + (a.get("aria-labelledby") or "")))
        elif tag in ("section", "div", "article"):
            self._pilha.append((tag, ""))
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            for _, nome in self._pilha:
                for k in nome.split():
                    self.secoes.setdefault(k, []).append(a["href"])
        if tag in ("img", "source"):
            self.imgs.append(a.get("src") or a.get("srcset") or "")

    def handle_endtag(self, tag):
        if tag == "script" and self._ld is not None:
            self.ldjson.append("".join(self._ld))
            self._ld = None
        elif tag in ("script", "style") and self._skip:
            self._skip -= 1
        if tag in ("section", "div", "article") and self._pilha:
            self._pilha.pop()

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
        elif not self._skip:
            self.texto.append(data)


def paginas(alvo: Path):
    for p in sorted(alvo.rglob("*.html")):
        if not IGNORAR & set(p.relative_to(alvo).parts):
            yield p


def ler(p: Path):
    h = _Pag()
    h.feed(p.read_text(encoding="utf-8"))
    ld = []
    for bloco in h.ldjson:
        try:
            j = json.loads(bloco)
            ld.extend(j if isinstance(j, list) else [j])
        except ValueError:
            pass
    return h, ld


def tipo_artigo(ld):
    return [o for o in ld if isinstance(o, dict) and o.get("@type") in ("Article", "BlogPosting", "NewsArticle")]


def dimensoes(f: Path):
    b = f.read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None


def xmp(f: Path) -> str:
    b = f.read_bytes()
    i = b.find(b"<x:xmpmeta")
    j = b.find(b"</x:xmpmeta>", i)
    return b[i:j].decode("utf-8", "replace") if i >= 0 and j > i else ""


def xmp_campo(x: str, tag: str) -> str:
    m = re.search(rf'{re.escape(tag)}="([^"]*)"', x)
    if m:
        return m.group(1)
    m = re.search(rf"<{re.escape(tag)}[^>]*>(.*?)</{re.escape(tag)}>", x, re.S)
    return re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else ""


def proporcao(wh):
    w, h = wh
    for nome, r in PROPORCOES.items():
        if abs(w / h - r) / r <= 0.01:
            return nome
    return f"{w}x{h}"


def _img_local(alvo: Path, url: str, base_url: str):
    rel = url.replace(base_url.rstrip("/") + "/", "") if base_url and url.startswith(base_url) else url.lstrip("/")
    f = alvo / rel
    return f if f.exists() else None


def avaliar(alvo: Path) -> dict:
    """→ {ID: [(ok: bool, msg)]}  (só IDs com alguma checagem automática)."""
    alvo = Path(alvo)
    cfg = {}
    if (alvo / "config" / "site.json").exists():
        cfg = json.loads((alvo / "config" / "site.json").read_text(encoding="utf-8"))
    base = cfg.get("base_url", "")
    R = {k: [] for k in ("CANON-SEO-01", "CANON-SEO-03", "CANON-SEO-04", "CANON-SEO-05", "CANON-SEO-07", "CANON-SEO-08")}
    artigos = []
    for p in paginas(alvo):
        h, ld = ler(p)
        nome = str(p.relative_to(alvo))
        txt = " ".join(" ".join(h.texto).split()) + " " + json.dumps(ld, ensure_ascii=False)
        # §1 embalagem
        achados = [m.group(0) for rx in (r"\bmedianas?\b", r"\barquimedes\b", r"\bgrupos?\s+(?:da\s+)?disal\b",
                                         r"\bembutido\s*(?:de\s*)?\d", r"\d+(?:[.,]\d+)?\s*%\s*(?:de\s+)?embutido")
                   for m in re.finditer(rx, txt, re.I)]
        R["CANON-SEO-01"].append((not achados, f"{nome}: termos proibidos {achados}" if achados else f"{nome}: sem grupo Disal / mediana / embutido com número / Arquimedes"))
        # §3 citação
        ruins = [m.group(0) for rx in (r"a\s+conferir", r"fonte:\s*google") for m in re.finditer(rx, txt, re.I)]
        R["CANON-SEO-03"].append((not ruins, f"{nome}: {ruins}" if ruins else f"{nome}: sem 'A CONFERIR' / 'Fonte: Google'"))
        for art in tipo_artigo(ld):
            artigos.append((p, h, art))
    if not artigos:
        R["CANON-SEO-07"].append((False, "nenhuma página com JSON-LD Article/BlogPosting"))
    for p, h, art in artigos:
        nome = str(p.relative_to(alvo))
        slug = p.parent.name
        # §4 slug com ID de criativo
        R["CANON-SEO-04"].append((bool(RE_ID_CRIATIVO_SLUG.search(slug)),
                                  f"{nome}: slug '{slug}' {'tem' if RE_ID_CRIATIVO_SLUG.search(slug) else 'sem'} ID de criativo (BLOG-AAAAMMDD…)"))
        # §5 E-E-A-T: Giro e LinkedIn linkados na bio; foto do autor existe
        bio = h.secoes.get("about-author", []) + h.secoes.get("author", []) + h.secoes.get("sobre-autor", [])
        R["CANON-SEO-05"].append((any(GIRO in u for u in bio), f"{nome}: link Giro Automotivo na bio {'presente' if any(GIRO in u for u in bio) else 'AUSENTE'}"))
        R["CANON-SEO-05"].append((any("linkedin.com/" in u for u in bio), f"{nome}: LinkedIn na bio {'presente' if any('linkedin.com/' in u for u in bio) else 'AUSENTE'}"))
        autores = art.get("author") or []
        autores = autores if isinstance(autores, list) else [autores]
        fotos = [_img_local(alvo, a.get("image", ""), base) for a in autores if isinstance(a, dict)]
        R["CANON-SEO-05"].append((bool(fotos) and all(fotos), f"{nome}: foto do autor {'no repo' if fotos and all(fotos) else 'AUSENTE'}"))
        # §7 dados estruturados + IPTC/XMP das imagens do Article
        R["CANON-SEO-07"].append((True, f"{nome}: JSON-LD {art.get('@type')}"))
        imgs = art.get("image") or []
        imgs = imgs if isinstance(imgs, list) else [imgs]
        props = set()
        for u in imgs:
            f = _img_local(alvo, u if isinstance(u, str) else u.get("url", ""), base)
            if not f:
                R["CANON-SEO-07"].append((False, f"{nome}: imagem {u} não está no repo"))
                continue
            x, wh = xmp(f), dimensoes(f)
            if wh:
                props.add(proporcao(wh))
            tr = xmp_campo(x, "photoshop:TransmissionReference")
            ident = xmp_campo(x, "dc:identifier")
            criador = xmp_campo(x, "dc:creator")
            giro = xmp_campo(x, "Iptc4xmpCore:CreatorWorkURL") or xmp_campo(x, "xmpRights:WebStatement")
            falta = [n for n, ok in (("TransmissionReference=FR-001", tr == "FR-001"), ("autor", "Wagner Sena" in criador),
                                     ("link Giro", GIRO in giro), ("ID criativo", bool(RE_ID_CRIATIVO.fullmatch(ident or "")))) if not ok]
            R["CANON-SEO-07"].append((not falta, f"{f.name}: XMP/IPTC sem {falta}" if falta else f"{f.name}: XMP/IPTC completo"))
            if wh and wh[0] < 1080:
                R["CANON-SEO-07"].append((False, f"{f.name}: largura {wh[0]} < 1080"))
            titulo = xmp_campo(x, "dc:title")
            if "placeholder" in (titulo + " " + f.name).lower():
                R["CANON-SEO-08"].append((False, f"{f.name}: imagem placeholder ('{titulo}')"))
        faltam = [k for k in PROPORCOES if k not in props]
        R["CANON-SEO-08"].append((not faltam, f"{nome}: proporções {sorted(props)}; faltam {faltam}" if faltam else f"{nome}: 4 proporções"))
    return {k: v for k, v in R.items() if v}
