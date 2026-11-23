"""Degradação que simula foto de celular (a mesma dos boletos).
"""
import io
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


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

    largura_alvo = min(1600, int(w * rng.uniform(0.70, 1.0)))
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


