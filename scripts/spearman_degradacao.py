"""Spearman entre o acerto exato de cada foto simulada e cada parâmetro de degradação.

Uso: python3 scripts/spearman_degradacao.py [--detalhes CSV] [--dataset DIR] [--saida DIR]
Requer scipy.
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

try:
    from scipy.stats import spearmanr
except ImportError:
    sys.exit("Este script requer scipy (pip install scipy).")

RAIZ_REPO = Path(__file__).resolve().parents[1]
DETALHES_PADRAO = RAIZ_REPO / "resultados" / "experimento1_sintetico" / "detalhes.csv"
DATASET_PADRAO = RAIZ_REPO / "dados" / "sinteticos"
SAIDA_PADRAO = RAIZ_REPO / "resultados" / "analises"

# (coluna no CSV, rótulo na monografia, valor a partir de foto_degradacao)
PARAMETROS = [
    ("desfoque_raio", "Raio do desfoque", lambda d: d["desfoque_raio"]),
    ("largura_px", "Largura da imagem", lambda d: d["largura_px"]),
    ("contraste", "Contraste", lambda d: d["contraste"]),
    ("deslocamento_perspectiva_px", "Deslocamento de perspectiva",
     lambda d: d["deslocamento_perspectiva_px"]),
    ("qualidade_jpeg", "Qualidade JPEG", lambda d: d["qualidade_jpeg"]),
    ("intensidade_iluminacao", "Intensidade da iluminação irregular",
     lambda d: d["intensidade_iluminacao"]),
    ("ruido_sigma", "Desvio padrão do ruído", lambda d: d["ruido_sigma"]),
    ("rotacao_modulo", "Ângulo de rotação (em módulo)", lambda d: abs(d["rotacao_graus"])),
]

MODELOS = [("nfe", "NF-e"), ("nfce", "NFC-e"), ("nfse", "NFS-e"),
           ("boleto", "Boleto"), ("recibo", "Recibo")]


def carregar_degradacao(dataset: Path):
    graus = {}
    boletos = json.loads((dataset / "boletos_sinteticos/imagens/metadados.json")
                         .read_text(encoding="utf-8"))
    for meta in boletos["imagens"]:
        graus[("boleto", meta["id"])] = meta["foto_degradacao"]
    docs = json.loads((dataset / "documentos_sinteticos/imagens/metadados.json")
                      .read_text(encoding="utf-8"))
    for tipo in ("nfe", "nfce", "nfse", "recibo"):
        for meta in docs[tipo]:
            graus[(tipo, meta["id"])] = meta["foto_degradacao"]
    return graus


def acerto_por_foto(detalhes: Path):
    contagem = defaultdict(lambda: [0, 0])
    with detalhes.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if linha["variante"] != "foto":
                continue
            c = contagem[(linha["tipo"], linha["id"])]
            c[0] += linha["status"] == "exato"
            c[1] += 1
    return {chave: exatos / campos for chave, (exatos, campos) in contagem.items()}


def p_normal(rho: float, n: int) -> float:
    z = abs(rho) * math.sqrt(n - 1)
    return math.erfc(z / math.sqrt(2))


def correlacao(xs, ys):
    resultado = spearmanr(xs, ys)
    rho, p_t = float(resultado.statistic), float(resultado.pvalue)
    n = len(xs)
    return {"rho": rho, "n": n, "p_t": p_t, "p_normal": p_normal(rho, n)}


def fmt_p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detalhes", type=Path, default=DETALHES_PADRAO)
    parser.add_argument("--dataset", type=Path, default=DATASET_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()

    acertos = acerto_por_foto(args.detalhes)
    graus = carregar_degradacao(args.dataset)
    faltando = sorted(set(acertos) - set(graus))
    if faltando:
        sys.exit(f"Fotos sem foto_degradacao nos metadados: {faltando[:5]}")
    fotos = sorted(acertos)

    linhas = []
    for coluna, rotulo, valor in PARAMETROS:
        r = correlacao([valor(graus[f]) for f in fotos], [acertos[f] for f in fotos])
        linhas.append({"escopo": "todas", "parametro": coluna, "rotulo": rotulo, **r})
    _, rotulo_desfoque, desfoque = PARAMETROS[0]
    for tipo, nome in MODELOS:
        doc = [f for f in fotos if f[0] == tipo]
        r = correlacao([desfoque(graus[f]) for f in doc], [acertos[f] for f in doc])
        linhas.append({"escopo": nome, "parametro": "desfoque_raio", "rotulo": rotulo_desfoque, **r})

    args.saida.mkdir(parents=True, exist_ok=True)
    destino = args.saida / "spearman_degradacao.csv"
    campos = ["escopo", "parametro", "rotulo", "n", "rho", "p_t", "p_normal"]
    with destino.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({**linha, "rho": f"{linha['rho']:.4f}",
                               "p_t": f"{linha['p_t']:.6g}", "p_normal": f"{linha['p_normal']:.6g}"})

    print(f"Fotos simuladas: {len(fotos)}  (acerto médio exato: "
          f"{sum(acertos.values()) / len(fotos):.1%})\n")
    cab = f"{'Escopo':<8} {'Parâmetro':<38} {'n':>4} {'rho':>8} {'p (t)':>9} {'p (normal)':>11}"
    print(cab)
    print("-" * len(cab))
    for linha in linhas:
        print(f"{linha['escopo']:<8} {linha['rotulo']:<38} {linha['n']:>4} {linha['rho']:>8.3f} "
              f"{fmt_p(linha['p_t']):>9} {fmt_p(linha['p_normal']):>11}")
    print(f"\nSalvo em {destino}")


if __name__ == "__main__":
    main()
