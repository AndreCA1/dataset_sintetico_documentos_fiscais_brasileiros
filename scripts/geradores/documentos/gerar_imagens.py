"""Converte notas (PDF, 200 dpi) e recibos (HTML) em PNG limpo e foto simulada e grava imagens/metadados.json.

Uso (em dados/sinteticos/documentos_sinteticos):
  python3 ../../../scripts/geradores/documentos/gerar_imagens.py . [--semente 42] [--dpi 200] [--sem-foto] [--tipos nfe nfce nfse recibo]
Requer pymupdf, playwright (com chromium), pillow e numpy.
"""
import argparse
import json
import random
import sys
from pathlib import Path

import pymupdf
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from degradacao import simular_foto  # noqa: E402

TIPOS = ["nfe", "nfce", "nfse", "recibo"]


def pdf_para_png(pdf: Path, destino: Path, dpi: int) -> int:
    doc = pymupdf.open(pdf)
    doc[0].get_pixmap(dpi=dpi).save(destino)
    return len(doc)


def htmls_para_png(htmls: list[Path], pasta: Path) -> list[Path]:
    from playwright.sync_api import sync_playwright

    gerados = []
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 820, "height": 1000}, device_scale_factor=2)
        for html in htmls:
            pagina.goto(html.resolve().as_uri(), wait_until="load")
            destino = pasta / f"{html.stem}.png"
            pagina.locator(".recibo").screenshot(path=str(destino))
            gerados.append(destino)
        navegador.close()
    return gerados


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", type=Path)
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--sem-foto", action="store_true")
    ap.add_argument("--tipos", nargs="+", default=TIPOS, choices=TIPOS)
    args = ap.parse_args()

    base = args.base
    rng = random.Random(args.semente)
    metadados = {}
    for tipo in args.tipos:
        pasta_png = base / "imagens" / tipo / "png"
        pasta_foto = base / "imagens" / tipo / "foto"
        pasta_png.mkdir(parents=True, exist_ok=True)
        if not args.sem_foto:
            pasta_foto.mkdir(parents=True, exist_ok=True)

        itens = []
        if tipo == "recibo":
            pngs = htmls_para_png(sorted((base / tipo / "html").glob("*.html")), pasta_png)
            paginas = {p.stem: 1 for p in pngs}
        else:
            pngs, paginas = [], {}
            for pdf in sorted((base / tipo / "pdf").glob("*.pdf")):
                destino = pasta_png / f"{pdf.stem}.png"
                paginas[pdf.stem] = pdf_para_png(pdf, destino, args.dpi)
                pngs.append(destino)

        for png in pngs:
            item = {"id": png.stem, "png": str(png.relative_to(base)),
                    "png_tamanho_px": list(Image.open(png).size), "paginas_documento": paginas[png.stem]}
            if not args.sem_foto:
                jpg = pasta_foto / f"{png.stem}.jpg"
                item["foto"] = str(jpg.relative_to(base))
                item["foto_degradacao"] = simular_foto(png, jpg, rng)
            itens.append(item)
        multipag = [i["id"] for i in itens if i["paginas_documento"] > 1]
        print(f"{tipo}: {len(itens)} imagens" + (f" (só 1ª página de: {', '.join(multipag)})" if multipag else ""))
        metadados[tipo] = itens

    caminho = base / "imagens" / "metadados.json"
    anteriores = json.loads(caminho.read_text("utf-8")) if caminho.exists() else {}
    anteriores.update({"semente": args.semente, "dpi_pdf": args.dpi, **metadados})
    caminho.write_text(json.dumps(anteriores, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
