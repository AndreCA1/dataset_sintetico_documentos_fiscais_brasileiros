"""Valida os boletos contra o gabarito: DVs, fator de vencimento, valor e campos no HTML.

Uso: python3 ../../../scripts/geradores/boletos/validar.py .
"""
import html as htmlmod
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path


def mod10(num: str) -> int:
    total = 0
    for i, d in enumerate(reversed(num)):
        p = int(d) * (2 if i % 2 == 0 else 1)
        total += p // 10 + p % 10
    return (10 - total % 10) % 10


def mod11_barras(num43: str) -> int:
    total, peso = 0, 2
    for d in reversed(num43):
        total += int(d) * peso
        peso = 2 if peso == 9 else peso + 1
    r = 11 - total % 11
    return 1 if r in (0, 1, 10, 11) else r


def data_do_fator(fator: int, venc: date) -> date:
    # O fator de vencimento reinicia em 1000 em 22/02/2025 (FEBRABAN).
    if venc >= date(2025, 2, 22):
        return date(2025, 2, 22) + timedelta(days=fator - 1000)
    return date(1997, 10, 7) + timedelta(days=fator)


def texto_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", htmlmod.unescape(raw))


def main(base: Path) -> int:
    gab = json.loads((base / "gabarito.json").read_text(encoding="utf-8"))
    erros = []
    for b in gab["boletos"]:
        bid = b["id"]
        ld, cb = b["linha_digitavel_numeros"], b["codigo_barras"]
        e = lambda msg: erros.append(f"{bid}: {msg}")

        if len(ld) != 47 or len(cb) != 44:
            e(f"tamanhos inválidos LD={len(ld)} CB={len(cb)}")
            continue
        for ini, fim in ((0, 9), (10, 20), (21, 31)):
            if mod10(ld[ini:fim]) != int(ld[fim]):
                e(f"DV do campo da LD {ld[ini:fim + 1]} inválido")
        if mod11_barras(cb[:4] + cb[5:]) != int(cb[4]):
            e("DV geral do código de barras inválido")
        reconstruido = ld[0:4] + ld[32] + ld[33:47] + ld[4:9] + ld[10:20] + ld[21:31]
        if reconstruido != cb:
            e("linha digitável não corresponde ao código de barras")

        venc = date.fromisoformat(b["data_vencimento"])
        if data_do_fator(int(cb[5:9]), venc) != venc:
            e(f"fator de vencimento {cb[5:9]} não corresponde a {venc}")
        if int(cb[9:19]) != round(b["valor_documento"] * 100):
            e(f"valor no código de barras {cb[9:19]} != {b['valor_documento']}")
        if cb[0:3] != b["banco"]["codigo"]:
            e(f"código do banco {cb[0:3]} != {b['banco']['codigo']}")

        txt = texto_html(base / b["arquivo_html"])
        brl = lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        esperados = {
            "vencimento": venc.strftime("%d/%m/%Y"),
            "valor documento": brl(b["valor_documento"]),
            "valor cobrado": brl(b["valor_cobrado"]),
            "cedente": b["beneficiario"]["nome"],
            "cedente CNPJ": b["beneficiario"]["cnpj"],
            "sacado": b["pagador"]["nome"],
            "sacado CPF": b["pagador"]["cpf"],
            "linha digitável": b["linha_digitavel"],
        }
        if b["desconto_abatimento_impresso"]:
            esperados["desconto"] = b["desconto_abatimento_impresso"]
        for campo, valor in esperados.items():
            if valor not in txt:
                e(f"campo '{campo}' ({valor}) não encontrado no HTML")
        if 'class="barcode"' not in (base / b["arquivo_html"]).read_text(encoding="utf-8"):
            e("imagem do código de barras ausente")

    n = len(gab["boletos"])
    print(f"{n} boletos verificados, {len(erros)} problema(s)")
    for linha in erros:
        print("  -", linha)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
