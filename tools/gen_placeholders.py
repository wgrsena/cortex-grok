#!/usr/bin/env python3
"""Gera as imagens placeholder do blog em PNG (stdlib pura) com XMP IPTC embutido.

Por que PNG gerado aqui: o box não tem exiftool nem Pillow, e a regra é não instalar
dependência. O PNG aceita XMP num chunk iTXt com a chave "XML:com.adobe.xmp", que é
onde exiftool e o Google leem o IPTC Extension (Iptc4xmpExt:DigitalSourceType).

Os placeholders são preenchimento sólido gerado por algoritmo, então recebem o código
honesto `algorithmicMedia`. As artes finais feitas por IA (Midas) devem receber
`trainedAlgorithmicMedia` com exiftool (ver README, item 8 do checklist).

Uso: python3 tools/gen_placeholders.py
"""
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
NEWSCODES = "http://cv.iptc.org/newscodes/digitalsourcetype/"


def xmp_packet(source_type: str, titulo: str) -> bytes:
    return f"""<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
   <Iptc4xmpExt:DigitalSourceType>{NEWSCODES}{source_type}</Iptc4xmpExt:DigitalSourceType>
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">{titulo}</rdf:li></rdf:Alt></dc:title>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>""".encode("utf-8")


def chunk(tipo: bytes, dados: bytes) -> bytes:
    return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)


def png(path: Path, w: int, h: int, rgb_topo, rgb_base, source_type: str, titulo: str) -> None:
    linhas = bytearray()
    for y in range(h):
        t = y / max(h - 1, 1)
        cor = bytes(int(a + (b - a) * t) for a, b in zip(rgb_topo, rgb_base))
        linhas += b"\x00" + cor * w
    itxt = b"XML:com.adobe.xmp\x00\x00\x00\x00\x00" + xmp_packet(source_type, titulo)
    dados = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"iTXt", itxt)
        + chunk(b"IDAT", zlib.compress(bytes(linhas), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(dados)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    capa = [("16x9", 1200, 675), ("4x3", 1200, 900), ("1x1", 1200, 1200)]
    for prop, w, h in capa:
        png(IMG / f"artigo-exemplo-{prop}.png", w, h, (230, 244, 239), (11, 110, 79),
            "algorithmicMedia", f"PLACEHOLDER capa artigo-exemplo {prop}")
    # Foto do autor: é a foto real (assets/img/autor-wagner-sena.jpg), não é gerada aqui.


if __name__ == "__main__":
    main()
