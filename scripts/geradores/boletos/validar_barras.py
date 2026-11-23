"""Lê o código de barras das imagens dos boletos e compara com o gabarito.

Uso: python3 ../../../scripts/geradores/boletos/validar_barras.py .
Requer pyzbar e libzbar.
"""
import json
import sys
from pathlib import Path

from PIL import Image
from pyzbar.pyzbar import ZBarSymbol, decode

base = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
gabarito = {b["id"]: b["codigo_barras"] for b in json.loads((base / "gabarito.json").read_text("utf-8"))["boletos"]}

for pasta, ext in (("png", "png"), ("foto", "jpg")):
    if not (base / "imagens" / pasta).exists():
        continue
    certos, nao_lidos, errados = 0, [], []
    for bid, esperado in gabarito.items():
        lidos = [d.data.decode() for d in decode(Image.open(base / "imagens" / pasta / f"{bid}.{ext}"), symbols=[ZBarSymbol.I25])]
        if esperado in lidos:
            certos += 1
        elif lidos:
            errados.append((bid, lidos))
        else:
            nao_lidos.append(bid)
    print(f"{pasta}: {certos}/{len(gabarito)} corretos, {len(nao_lidos)} não lidos, {len(errados)} lidos errado")
    for bid, lidos in errados:
        print(f"  ERRADO {bid}: {lidos}")
