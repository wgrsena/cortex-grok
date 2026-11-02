#!/usr/bin/env python3
"""Compositor dos cards de oportunidade do Midas (v0.8.0).

Lê midas/cards/dados-cards.json (saída do injetar.py) e desenha, sobre a foto ilustrativa da faixa
(oportunidades/assets/img/faixa-<N>-<prop>.jpg, gerada por IA), os campos do card: carta de crédito, entrada,
parcela (1ª, com seguro), próxima assembleia e lance, com a data da coleta, o CTA com o FR e o aviso.
Campo sem fonte sai com o texto da rota ("dado não disponível"), nunca vazio nem estimado.

Pillow já instalado na box e já usado pelo Midas (compose.py, gen_imgs.py); nada novo é instalado.
Metadados FR-SPEC v1.0.0 gravados com exiftool (/workspace/tools/exiftool ou $EXIFTOOL).

Uso: python3 midas/cards/compor.py [--lote 20261101] [--saida midas/cards/saida]
ID: BLOG-<lote>-oportunidade-<N>mil-v08-<prop>-<NNN> (16x9-001, 4x3-002, 1x1-003), sem sobrescrever a v0.7.
"""
import argparse
import json
import os
import subprocess
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
IMG = ROOT / "oportunidades" / "assets" / "img"
EXIFTOOL = os.environ.get("EXIFTOOL", "/workspace/tools/exiftool/exiftool")
FONT = os.environ.get("MIDAS_FONT", "/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf")
TEAL, INK, GREY, SOFT = (14, 124, 123), (17, 24, 39), (90, 98, 112), (241, 245, 249)
PROPS = (("16x9", 1200, 675, "001"), ("4x3", 1200, 900, "002"), ("1x1", 1200, 1200, "003"))
AVISO = "Resultado passado não garante contemplação."
ILUSTRATIVA = "Imagem ilustrativa gerada por IA; não é o bem da carta."


def font(size, wght):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([min(32, max(14, size)), wght])
    except Exception:
        pass
    return f


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def dbr(iso):
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


def blocos(card, dados):
    """Lista ordenada do que vai no painel (o texto vem pronto do injetor)."""
    mil = f"{card['faixa'] // 1000} MIL"
    cartas = f"{card['n_cartas']} carta{'s' if card['n_cartas'] > 1 else ''}"
    campos = [("Entrada", card["entrada"]), ("Parcela (1ª, com seguro)", card["parcela"]),
              ("Próxima assembleia", card["assembleia"]), ("Lance", card["lance"])]
    return {"kicker": f"CARTA DE CRÉDITO · FAIXA {mil}", "credito": card["credito"]["texto"],
            "sub": f"Combinação {card['combinacao']} · {cartas} · motor de oportunidades",
            "campos": campos,
            "fonte": f"Dados da coleta de {dbr(dados['data_coleta'])} (portal e calendário da administradora)",
            "cta": f"Simule com o código {dados['fr']} e veja se essa carta serve para você.",
            "aviso": AVISO, "ia": ILUSTRATIVA}


def painel(im, box, s, b):
    """Desenha o painel branco em box=(x, y, w) com escala s; devolve (imagem, altura)."""
    x, y, w = box
    d0 = ImageDraw.Draw(im)
    fk, fcr, fsub = font(int(20 * s), 700), font(int(56 * s), 800), font(int(18 * s), 500)
    flab, fval, flac = font(int(17 * s), 500), font(int(28 * s), 750), font(int(21 * s), 500)
    ffon, fcta, fav = font(int(17 * s), 500), font(int(22 * s), 650), font(int(17 * s), 500)
    pad, gap = int(36 * s), int(14 * s)
    inner = w - 2 * pad
    colw = (inner - gap) // 2
    ctal, fonl = wrap(d0, b["cta"], fcta, inner), wrap(d0, b["fonte"], ffon, inner)
    avl = wrap(d0, b["aviso"] + " " + b["ia"], fav, inner)
    cell_h = int(17 * s * 1.5) + int(30 * s * 1.25) + int(16 * s)
    h = (pad + int(fk.size * 1.7) + int(fcr.size * 1.15) + int(fsub.size * 1.6) + gap
         + 2 * cell_h + gap + len(fonl) * int(ffon.size * 1.4) + gap
         + len(ctal) * int(fcta.size * 1.35) + int(10 * s) + len(avl) * int(fav.size * 1.4) + pad)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x + 6, y + 12, x + w + 6, y + h + 12), int(18 * s), fill=(0, 0, 0, 80))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(int(16 * s))))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x, y, x + w, y + h), int(18 * s), fill=(255, 255, 255, 255))
    cy = y + pad
    d.rectangle((x + pad, cy - int(12 * s), x + pad + int(56 * s), cy - int(8 * s)), fill=TEAL)
    d.text((x + pad, cy), b["kicker"], font=fk, fill=TEAL); cy += int(fk.size * 1.7)
    d.text((x + pad, cy), b["credito"], font=fcr, fill=INK); cy += int(fcr.size * 1.15)
    d.text((x + pad, cy), b["sub"], font=fsub, fill=GREY); cy += int(fsub.size * 1.6) + gap
    for i, (rot, c) in enumerate(b["campos"]):
        cx = x + pad + (i % 2) * (colw + gap)
        ty = cy + (i // 2) * (cell_h + int(8 * s))
        d.rounded_rectangle((cx, ty, cx + colw, ty + cell_h), int(10 * s), fill=SOFT)
        d.text((cx + int(14 * s), ty + int(8 * s)), rot, font=flab, fill=GREY)
        vy = ty + int(8 * s) + int(17 * s * 1.5)
        if c["lacuna"]:
            d.text((cx + int(14 * s), vy + int(4 * s)), c["texto"], font=flac, fill=GREY)
        else:
            d.text((cx + int(14 * s), vy), c["texto"], font=fval, fill=INK)
    cy += 2 * cell_h + int(8 * s) + gap
    for l in fonl:
        d.text((x + pad, cy), l, font=ffon, fill=GREY); cy += int(ffon.size * 1.4)
    cy += gap
    for l in ctal:
        d.text((x + pad, cy), l, font=fcta, fill=TEAL); cy += int(fcta.size * 1.35)
    cy += int(10 * s)
    for l in avl:
        d.text((x + pad, cy), l, font=fav, fill=GREY); cy += int(fav.size * 1.4)
    return im, h


LAYOUT = {  # prop: (x, y, w, escala, ancorado_embaixo)
    "16x9": (36, 30, 680, 0.86, False),
    "4x3": (40, 40, 680, 1.0, False),
    "1x1": (40, None, 1120, 1.12, True),
}


def compor(card, dados, prop, W, H):
    im = Image.open(IMG / f"faixa-{card['faixa'] // 1000}-{prop}.jpg").convert("RGB")
    assert im.size == (W, H), (prop, im.size)
    im = im.convert("RGBA")
    x, y, w, s, embaixo = LAYOUT[prop]
    b = blocos(card, dados)
    if embaixo:  # mede numa cópia e reposiciona
        _, h = painel(im.copy(), (x, 0, w), s, b)
        y = H - h - 40
    im, h = painel(im, (x, y, w), s, b)
    assert y >= 0 and y + h <= H - 10, ("painel não cabe", prop, y, h, H)
    return im.convert("RGB")


def metadados(path, ident, card, dados):
    fr = dados["fr"]
    headline = f"Carta de crédito de consórcio de carro na faixa de {card['faixa'] // 1000} mil: o que o motor achou"
    desc = (f"Card de oportunidade (faixa de {card['faixa'] // 1000} mil, combinação {card['combinacao']}) com crédito, parcela e "
            f"próxima assembleia da coleta de {dbr(dados['data_coleta'])}; entrada e lance: dado não disponível. "
            f"Simule com o código {fr}. Foto ilustrativa gerada por IA. {AVISO}")
    args = [EXIFTOOL, "-q", "-overwrite_original", "-charset", "iptc=UTF8", "-codedcharacterset=utf8",
            "-XMP-iptcExt:DigitalSourceType=http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
            "-XMP-photoshop:Credit=Conecta Cortex — Midas (foto gerada por IA)", "-IPTC:Credit=Midas (IA)",
            "-XMP-dc:Creator=Conecta Cortex — Midas (gerado com IA)", "-IPTC:By-line=Conecta Cortex — Midas (IA)",
            "-XMP-dc:Rights=© Conecta Consórcios", "-IPTC:CopyrightNotice=© Conecta Consórcios",
            f"-XMP-dc:Description={desc}", f"-IPTC:Caption-Abstract={desc}",
            f"-XMP-photoshop:Headline={headline}", f"-IPTC:Headline={headline}",
            f"-XMP-photoshop:TransmissionReference={fr}",
            f"-XMP-dc:Identifier={ident}", f"-XMP-dc:Title={ident}", f"-IPTC:ObjectName={ident}"]
    for k in (fr, ident, "variante:card", "FLUXO-REV", f"cards-oportunidade-v{dados['versao']}", f"coleta-{dados['data_coleta']}"):
        args += [f"-XMP-dc:Subject+={k}", f"-IPTC:Keywords+={k}"]
    subprocess.run(args + [str(path)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", default=None, help="AAAAMMDD (default: hoje do dados-cards.json)")
    ap.add_argument("--saida", default=str(AQUI / "saida"))
    a = ap.parse_args()
    dados = json.loads((AQUI / "dados-cards.json").read_text(encoding="utf-8"))
    lote = a.lote or dados["hoje"].replace("-", "")
    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    feitos = []
    for card in dados["cards"]:
        if not card.get("combinacao"):
            print("faixa", card["faixa"], "sem combinação: card não gerado")
            continue
        for prop, W, H, nnn in PROPS:
            ident = f"BLOG-{lote}-oportunidade-{card['faixa'] // 1000}mil-v08-{prop}-{nnn}"
            p = out / f"{ident}.jpg"
            if p.exists() and not os.environ.get("MIDAS_REGERAR"):
                raise SystemExit(f"{p.name} já existe (não sobrescrevo; MIDAS_REGERAR=1 para refazer)")
            compor(card, dados, prop, W, H).save(p, "JPEG", quality=88, optimize=True, progressive=True)
            metadados(p, ident, card, dados)
            feitos.append(p)
            print(p.relative_to(ROOT), f"{p.stat().st_size // 1024} KB")
    return feitos


if __name__ == "__main__":
    main()
