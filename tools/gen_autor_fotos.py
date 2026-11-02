#!/usr/bin/env python3
"""Gera as fotos do autor (WebP + JPEG) a partir dos originais aprovados pelo Wagner (Drive).

Ferramenta de build local: precisa de Pillow (não é dependência do site nem do check.py).
Uso: python3 tools/gen_autor_fotos.py /pasta/com/os/originais

Originais (Drive, aprovados pelo Wagner em 02/11/2026; NUNCA usar wagner-frente.png 1YJcPsUPzKAGSiGwK5JBPytbziJJo_WDU):
  azul           1_UAGhfPUG0DJMpBXfrXRq8tDW8_A2zRx  "Wagner Sena.png" 600×750 PNG recortado (fundo transparente), ombros inteiros
  azul-esfumado  1n5FYsxoNqjwytLoNB7hDz4fpevWFReJw  "Wagner Sena.png" 600×750 PNG recortado, ombros esfumados nas laterais
  preta          1JXkhI1diSbtfdnGfYx2l4Yqvac36Ncjn  "Wagner Sena - camisa preta.png" 511×640, fundo preto

Recortes (x0, y0, x1, y1) em pixels do original; valores fora da imagem viram margem com a cor de fundo.
  retrato = quadrado cabeça + ombros (página do autor);  rosto = quadrado mais fechado (byline 56 px / avatar).
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "autor"
FUNDO = (246, 249, 252)  # --bg-soft

FOTOS = {
    "azul":          {"arq": "foto2-1_UAG.png",              "retrato": (5, -30, 605, 570), "rosto": (75, -20, 535, 440)},
    "azul-esfumado": {"arq": "foto1-1n5FY.png",              "retrato": (5, -30, 605, 570), "rosto": (75, -20, 535, 440)},
    "preta":         {"arq": "foto3-1JXkh-camisa-preta.png", "retrato": (12, -20, 523, 491), "rosto": (63, -25, 473, 385)},
}
TAMANHOS = {"retrato": (240, 480), "rosto": (112,)}


def achatar(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "LA"):
        base = Image.new("RGB", im.size, FUNDO)
        base.paste(im, mask=im.getchannel("A"))
        return base
    return im.convert("RGB")


def recortar(im, caixa, cor):
    x0, y0, x1, y1 = caixa
    tela = Image.new("RGBA", (x1 - x0, y1 - y0), cor + (0,) if im.mode == "RGBA" else cor + (255,))
    tela.paste(im.convert("RGBA"), (-x0, -y0))
    return tela


def main(origem: Path):
    for nome, cfg in FOTOS.items():
        im = Image.open(origem / cfg["arq"])
        cor = (0, 0, 0) if im.mode == "RGB" else FUNDO
        destino = OUT if nome == PADRAO else OUT / "alternativas"
        destino.mkdir(parents=True, exist_ok=True)
        for tipo, lados in TAMANHOS.items():
            q = achatar(recortar(im, cfg[tipo], cor))
            for lado in lados:
                r = q.resize((lado, lado), Image.LANCZOS)
                base = destino / f"wagner-sena-{nome}-{tipo}-{lado}"
                r.save(f"{base}.webp", "WEBP", quality=82, method=6)
                if lado == max(lados):
                    r.save(f"{base}.jpg", "JPEG", quality=85, optimize=True, progressive=True)
                print(base.relative_to(ROOT))


PADRAO = "azul"  # escolhida após os previews de 02/11/2026 (ver README › Autor)

if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/autor-fotos"))
