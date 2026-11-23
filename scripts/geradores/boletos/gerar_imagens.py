"""Converte os boletos HTML em PNG limpo e foto simulada e grava imagens/metadados.json.

Uso (em dados/sinteticos/boletos_sinteticos):
  python3 ../../../scripts/geradores/boletos/gerar_imagens.py . [--semente 42] [--escala 2] [--sem-foto] [--com-instrucoes]
Requer playwright (com chromium), pillow e numpy.
"""
import argparse
import io
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from playwright.sync_api import sync_playwright

LARGURA_A4_PX = 794


def cortar_branco_inferior(png: Path, margem: int) -> None:
    img = Image.open(png).convert("RGB")
    escuro = np.asarray(img.convert("L")) < 200
    linhas = np.where(escuro.any(axis=1))[0]
    if len(linhas):
        img.crop((0, 0, img.width, min(img.height, linhas[-1] + margem))).save(png)


def capturar_pngs(base: Path, saida: Path, escala: float, com_instrucoes: bool) -> list[Path]:
    htmls = sorted((base / "html").glob("boleto_*.html"))
    saida.mkdir(parents=True, exist_ok=True)
    gerados = []
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(
            viewport={"width": LARGURA_A4_PX, "height": 1123},
            device_scale_factor=escala,
        )
        if not com_instrucoes:
            pagina.emulate_media(media="print")
        for html in htmls:
            pagina.goto(html.resolve().as_uri(), wait_until="load")
            destino = saida / f"{html.stem}.png"
            pagina.screenshot(path=str(destino), full_page=True)
            cortar_branco_inferior(destino, margem=int(24 * escala))
            gerados.append(destino)
            print(f"  png  {destino.name}")
        navegador.close()
    return gerados


def coeficientes_perspectiva(destino, origem):
    linhas = []
    for (x, y), (u, v) in zip(destino, origem):
        linhas.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        linhas.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    a = np.array(linhas, dtype=float)
    b = np.array(origem, dtype=float).reshape(8)
    return np.linalg.solve(a, b).tolist()


def fundo_mesa(tamanho, rng: random.Random) -> Image.Image:
    w, h = tamanho
    cor = rng.choice([(120, 92, 70), (160, 130, 100), (90, 90, 95), (200, 195, 185), (60, 65, 75)])
    np_rng = np.random.default_rng(rng.randrange(2**32))
    textura = np_rng.normal(0, 8, (h, w, 1))
    arr = np.clip(np.array(cor, dtype=float) + textura, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def simular_foto(png: Path, destino: Path, rng: random.Random) -> dict:
    img = Image.open(png).convert("RGB")
    w, h = img.size

    largura_alvo = rng.randint(1100, 1600)
    img = img.resize((largura_alvo, round(h * largura_alvo / w)), Image.LANCZOS)
    w, h = img.size

    margem = int(w * rng.uniform(0.06, 0.14))
    tela_w, tela_h = w + 2 * margem, h + 2 * margem
    tela = fundo_mesa((tela_w, tela_h), rng)
    sombra = Image.new("L", (tela_w, tela_h), 0)
    ImageDraw.Draw(sombra).rectangle(
        [margem + 8, margem + 8, margem + w + 8, margem + h + 8], fill=110
    )
    tela.paste((0, 0, 0), mask=sombra.filter(ImageFilter.GaussianBlur(12)))
    tela.paste(img, (margem, margem))

    desloc = w * rng.uniform(0.01, 0.05)
    cantos = [(margem, margem), (margem + w, margem), (margem + w, margem + h), (margem, margem + h)]
    novos = [(x + rng.uniform(-desloc, desloc), y + rng.uniform(-desloc, desloc)) for x, y in cantos]
    coef = coeficientes_perspectiva(novos, cantos)
    tela_rgba = tela.convert("RGBA")
    fundo = fundo_mesa((tela_w, tela_h), rng).convert("RGBA")
    warped = tela_rgba.transform((tela_w, tela_h), Image.PERSPECTIVE, coef, Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    fundo.alpha_composite(warped)
    img = fundo.convert("RGB")

    angulo = rng.uniform(-4.0, 4.0)
    img = img.rotate(angulo, resample=Image.BICUBIC, expand=False, fillcolor=(40, 40, 40))

    arr = np.asarray(img).astype(float)
    yy, xx = np.mgrid[0:img.height, 0:img.width]
    teta = rng.uniform(0, 2 * np.pi)
    grad = (np.cos(teta) * xx / img.width + np.sin(teta) * yy / img.height)
    grad = (grad - grad.min()) / (np.ptp(grad) or 1)
    intensidade_luz = rng.uniform(0.15, 0.40)
    arr *= (1 - intensidade_luz * grad)[..., None]

    tom = np.array([rng.uniform(0.95, 1.05), 1.0, rng.uniform(0.90, 1.05)])
    arr *= tom
    sigma_ruido = rng.uniform(2.0, 7.0)
    arr += np.random.default_rng(rng.randrange(2**32)).normal(0, sigma_ruido, arr.shape)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    contraste = rng.uniform(0.85, 1.10)
    img = ImageEnhance.Contrast(img).enhance(contraste)
    desfoque = rng.uniform(0.0, 1.3)
    if desfoque > 0.15:
        img = img.filter(ImageFilter.GaussianBlur(desfoque))
    qualidade = rng.randint(55, 88)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=qualidade)
    destino.write_bytes(buf.getvalue())

    return {
        "largura_px": img.width,
        "altura_px": img.height,
        "rotacao_graus": round(angulo, 2),
        "deslocamento_perspectiva_px": round(desloc, 1),
        "intensidade_iluminacao": round(intensidade_luz, 3),
        "ruido_sigma": round(sigma_ruido, 2),
        "desfoque_raio": round(desfoque, 2),
        "contraste": round(contraste, 3),
        "qualidade_jpeg": qualidade,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", type=Path, help="pasta boletos_sinteticos (contém html/ e gabarito.json)")
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--escala", type=float, default=2.0, help="fator de resolução da captura (2 = ~1588 px de largura)")
    ap.add_argument("--sem-foto", action="store_true", help="gera apenas os PNGs limpos")
    ap.add_argument("--com-instrucoes", action="store_true", help="mantém o bloco 'Instruções de Impressão' na imagem")
    args = ap.parse_args()

    base = args.base
    pasta_png = base / "imagens" / "png"
    pasta_foto = base / "imagens" / "foto"

    print("Capturando PNGs...")
    pngs = capturar_pngs(base, pasta_png, args.escala, args.com_instrucoes)

    metadados = []
    rng = random.Random(args.semente)
    if not args.sem_foto:
        print("Simulando fotos...")
        pasta_foto.mkdir(parents=True, exist_ok=True)
    for png in pngs:
        item = {
            "id": png.stem,
            "png": str(png.relative_to(base)),
            "png_tamanho_px": list(Image.open(png).size),
        }
        if not args.sem_foto:
            jpg = pasta_foto / f"{png.stem}.jpg"
            item["foto"] = str(jpg.relative_to(base))
            item["foto_degradacao"] = simular_foto(png, jpg, rng)
            print(f"  foto {jpg.name}")
        metadados.append(item)

    (base / "imagens" / "metadados.json").write_text(
        json.dumps(
            {"semente": args.semente, "escala_captura": args.escala, "imagens": metadados},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Concluído: {len(pngs)} boletos em {base / 'imagens'}")


if __name__ == "__main__":
    main()
