"""Valida notas e recibos contra o gabarito: campos no documento, DV da chave, totais e código de barras.

Uso: python3 ../../../scripts/geradores/documentos/validar.py .
Requer pymupdf e pyzbar.
"""
import html as htmlmod
import json
import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).parent))
from comum import dinheiro, dv_mod11_chave  # noqa: E402


def normalizar(t: str) -> str:
    return re.sub(r"\s+", " ", t)


def texto_pdf(p: Path) -> str:
    return normalizar(" ".join(pg.get_text() for pg in pymupdf.open(p)))


def texto_html(p: Path) -> str:
    raw = re.sub(r"<style.*?</style>", " ", p.read_text("utf-8"), flags=re.S)
    return normalizar(htmlmod.unescape(re.sub(r"<[^>]+>", " ", raw)))


def campos_nota(tipo, d):
    c = {
        "emitente": d["emitente"]["nome"],
        "emitente CNPJ": d["emitente"]["documento"],
        "data emissão": d["data_emissao_formatada"],
        "valor total": dinheiro(d["valor_total"]),
    }
    if tipo == "nfe":
        c["número"] = d["numero_formatado"]
    else:
        c["número"] = str(d["numero"])
    dest = d["destinatario"]
    if dest:
        c["destinatário doc"] = dest["documento"]
        if dest["nome"]:
            c["destinatário"] = dest["nome"]
    return c


def campos_recibo(d):
    return {
        "data": d["data_formatada"],
        "valor": dinheiro(d["valor"]),
        "conta débito": f"{d['conta_debito']['codigo']} - {d['conta_debito']['nome']}",
        "conta crédito": f"{d['conta_credito']['codigo']} - {d['conta_credito']['nome']}",
        "histórico": d["historico"],
        "forma de pagamento": d["forma_pagamento_detalhe"],
    }


def ler_barras(base: Path):
    try:
        from PIL import Image
        from pyzbar.pyzbar import ZBarSymbol, decode
    except ImportError:
        print("  (pyzbar indisponível: leitura de código de barras ignorada)")
        return
    gab = json.loads((base / "nfe" / "gabarito.json").read_text("utf-8"))["documentos"]
    for pasta, ext in (("png", "png"), ("foto", "jpg")):
        ok = errado = 0
        for d in gab:
            arq = base / "imagens" / "nfe" / pasta / f"{d['id']}.{ext}"
            if not arq.exists():
                continue
            lidos = [r.data.decode() for r in decode(Image.open(arq), symbols=[ZBarSymbol.CODE128])]
            ok += d["chave_acesso"] in lidos
            errado += bool(lidos) and d["chave_acesso"] not in lidos
        print(f"  código de barras DANFE ({pasta}): {ok}/{len(gab)} lidos corretamente, {errado} lidos errado")


def main(base: Path) -> int:
    problemas = []
    for tipo in ("nfe", "nfce", "nfse", "recibo"):
        arq = base / tipo / "gabarito.json"
        if not arq.exists():
            continue
        docs = json.loads(arq.read_text("utf-8"))["documentos"]
        n_antes = len(problemas)
        for d in docs:
            erro = lambda m: problemas.append(f"{d['id']}: {m}")  # noqa: E731
            if tipo == "recibo":
                txt = texto_html(base / tipo / d["arquivo_html"])
                esperados = campos_recibo(d)
            else:
                txt = texto_pdf(base / tipo / d["arquivo_pdf"])
                esperados = campos_nota(tipo, d)
                if tipo != "nfse":
                    ch = d["chave_acesso"]
                    if len(ch) != 44 or dv_mod11_chave(ch[:43]) != int(ch[43]):
                        erro("DV da chave de acesso inválido")
                    soma = round(sum(i["valor_total"] for i in d["itens"]), 2)
                    if abs(soma - d["valor_produtos"]) > 0.01:
                        erro("soma dos itens difere do valor dos produtos")
                    if abs(d["valor_produtos"] + d["valor_frete"] - d["valor_desconto"] - d["valor_total"]) > 0.01:
                        erro("produtos + frete - desconto difere do total")
                elif abs(d["valor_total"] - d["retencoes_federais"] - d["valor_liquido"]) > 0.01:
                    erro("valor líquido da NFS-e incoerente")
            for campo, valor in esperados.items():
                if normalizar(valor) not in txt:
                    erro(f"campo '{campo}' ({valor}) não encontrado no documento")
        print(f"{tipo}: {len(docs)} documentos verificados, {len(problemas) - n_antes} problema(s)")
    ler_barras(base)
    for p in problemas:
        print("  -", p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
