"""Sorteia a amostra do conjunto sintético e monta o PDF A4 para impressão.

Cada documento sai em tamanho real (PNG de 200 dpi; NF-e e NFS-e a 95%, para
caber na área imprimível). Imprima sem ajuste de escala:
lp -o print-scaling=none -o media=A4 impressao.pdf

Uso: python3 scripts/montar_impressao.py [--por-tipo 30] [--semente 20261115] [--saida DIR]
"""

from __future__ import annotations

import argparse
import csv
import random
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from avaliar_ocr import DATASET_PADRAO, carregar_dataset

DPI = 200
A4 = (1654, 2339)
ORDEM = ("nfe", "nfse", "boleto", "nfce", "recibo")


def mm(valor: float) -> int:
    return round(valor * DPI / 25.4)


def fonte(tamanho_mm: float):
    return ImageFont.load_default(size=mm(tamanho_mm))


def rotulo(numero: int, item: dict) -> str:
    return f"#{numero:03d}  {item['id']}"


def folha() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    pagina = Image.new("L", A4, 255)
    return pagina, ImageDraw.Draw(pagina)


def abrir(item: dict) -> Image.Image:
    return Image.open(item["arquivo"]).convert("L")


def pagina_inteira(itens, escala):
    for numero, item in itens:
        img = abrir(item)
        img = img.resize((round(img.width * escala), round(img.height * escala)),
                         Image.LANCZOS)
        pagina, desenho = folha()
        x, y = (A4[0] - img.width) // 2, (A4[1] - img.height) // 2
        pagina.paste(img, (x, y))
        desenho.text((A4[0] - mm(8), A4[1] - mm(4.5)), rotulo(numero, item),
                     font=fonte(2.2), fill=0, anchor="rs")
        yield pagina


def boleto(itens):
    for numero, item in itens:
        img = abrir(item)
        pagina, desenho = folha()
        x, y = (A4[0] - img.width) // 2, mm(12)
        pagina.paste(img, (x, y))
        desenho.text((x, y + img.height + mm(8)), rotulo(numero, item),
                     font=fonte(3.5), fill=0, anchor="lt")
        yield pagina


def nfce(itens):
    for i in range(0, len(itens), 2):
        par = itens[i:i + 2]
        pagina, desenho = folha()
        imgs = [abrir(item) for _, item in par]
        vao = mm(34)
        largura = sum(img.width for img in imgs) + vao * (len(imgs) - 1)
        x = (A4[0] - largura) // 2
        centro_vao = x + imgs[0].width + vao // 2
        for j, ((numero, item), img) in enumerate(zip(par, imgs)):
            pagina.paste(img, (x, (A4[1] - img.height) // 2))
            texto = f"<- {rotulo(numero, item)}" if j == 0 else f"{rotulo(numero, item)} ->"
            y = mm(20) if j == 0 else A4[1] - mm(20)
            if len(imgs) == 1:
                desenho.text((x + img.width + mm(6), mm(20)), texto, font=fonte(3), fill=0,
                             anchor="lt")
            else:
                desenho.multiline_text((centro_vao, y), texto.replace("  ", "\n"),
                                       font=fonte(3), fill=0, anchor="mm", align="center")
            x += img.width + vao
        yield pagina


def recibo(itens):
    for i in range(0, len(itens), 2):
        pagina, desenho = folha()
        y = mm(5)
        for numero, item in itens[i:i + 2]:
            img = abrir(item)
            x = (A4[0] - img.width) // 2
            desenho.text((x, y), rotulo(numero, item), font=fonte(3.5), fill=0, anchor="lt")
            pagina.paste(img, (x, y + mm(5)))
            y += mm(5) + img.height + mm(4)
        yield pagina


def salvar_pdf(paginas: list[Image.Image], caminho: Path) -> None:
    objetos: list[bytes] = []

    def novo(conteudo: bytes) -> int:
        objetos.append(conteudo)
        return len(objetos)

    largura_pt, altura_pt = (v * 72 / DPI for v in A4)
    raiz = novo(b"")
    paginas_obj = novo(b"")
    filhos = []
    for pagina in paginas:
        dados = zlib.compress(pagina.tobytes(), 9)
        imagem = novo(
            b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray "
            b"/BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n"
            % (pagina.width, pagina.height, len(dados)) + dados + b"\nendstream")
        desenho = b"q %.2f 0 0 %.2f 0 0 cm /Im0 Do Q" % (largura_pt, altura_pt)
        conteudo = novo(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(desenho), desenho))
        filhos.append(novo(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
            b"/Resources << /XObject << /Im0 %d 0 R >> >> /Contents %d 0 R >>"
            % (paginas_obj, largura_pt, altura_pt, imagem, conteudo)))
    objetos[raiz - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % paginas_obj
    objetos[paginas_obj - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % f for f in filhos), len(filhos))

    saida = bytearray(b"%PDF-1.4\n")
    posicoes = []
    for n, conteudo in enumerate(objetos, 1):
        posicoes.append(len(saida))
        saida += b"%d 0 obj\n" % n + conteudo + b"\nendobj\n"
    xref = len(saida)
    saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    saida += b"".join(b"%010d 00000 n \n" % p for p in posicoes)
    saida += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1, raiz, xref)
    caminho.write_bytes(saida)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dataset", type=Path, default=DATASET_PADRAO)
    parser.add_argument("--por-tipo", type=int, default=30)
    parser.add_argument("--semente", type=int, default=20261115)
    parser.add_argument("--escala-a4", type=float, default=0.95,
                        help="redução das NF-e/NFS-e para caber na área imprimível")
    parser.add_argument("--saida", type=Path, default=Path("impressao"))
    args = parser.parse_args()

    itens = carregar_dataset(args.dataset)
    sorteio = random.Random(args.semente)
    escolhidos = {}
    for tipo in ORDEM:
        ids = sorted(i["id"] for i in itens.values() if i["tipo"] == tipo and i["variante"] == "png")
        if args.por_tipo > len(ids):
            parser.error(f"{tipo}: só há {len(ids)} documentos")
        escolhidos[tipo] = sorted(sorteio.sample(ids, args.por_tipo))

    args.saida.mkdir(parents=True, exist_ok=True)
    montadores = {"nfe": lambda x: pagina_inteira(x, args.escala_a4),
                  "nfse": lambda x: pagina_inteira(x, args.escala_a4),
                  "boleto": boleto, "nfce": nfce, "recibo": recibo}
    escalas = {"nfe": args.escala_a4, "nfse": args.escala_a4}
    paginas, linhas, numero = [], [], 0
    for tipo in ORDEM:
        numerados = []
        for id_ in escolhidos[tipo]:
            numero += 1
            numerados.append((numero, itens[f"{tipo}/png/{id_}"]))
        inicio = len(paginas)
        paginas.extend(montadores[tipo](numerados))
        por_folha = 2 if tipo in ("nfce", "recibo") else 1
        for k, (n, item) in enumerate(numerados):
            linhas.append({"numero": n, "tipo": tipo, "id": item["id"],
                           "folha": inicio + k // por_folha + 1,
                           "escala": escalas.get(tipo, 1.0)})
        print(f"{tipo:7s} {len(numerados):3d} docs  folhas {inicio + 1}-{len(paginas)}")

    salvar_pdf(paginas, args.saida / "impressao.pdf")
    with open(args.saida / "lista.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    tamanho = (args.saida / "impressao.pdf").stat().st_size / 1e6
    print(f"\n{len(linhas)} documentos em {len(paginas)} folhas -> "
          f"{args.saida / 'impressao.pdf'} ({tamanho:.1f} MB) e lista.csv")


if __name__ == "__main__":
    main()
