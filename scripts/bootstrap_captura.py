"""Câmera comum × scanner nas fotos reais (experimento 2), pareado por documento.

Acerto exato de cada modo, teste dos sinais e IC de 95% da diferença por
bootstrap dos documentos (5.000 reamostragens, semente 20261115).

Uso: python3 scripts/bootstrap_captura.py [--detalhes CSV] [--repeticoes N] [--semente N] [--saida DIR]
Requer numpy e scipy.
"""
import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import numpy as np
    from scipy.stats import binomtest
except ImportError:
    sys.exit("Este script requer numpy e scipy.")

RAIZ_REPO = Path(__file__).resolve().parents[1]
DETALHES_PADRAO = RAIZ_REPO / "resultados" / "experimento2_fotos_reais" / "detalhes.csv"
SAIDA_PADRAO = RAIZ_REPO / "resultados" / "analises"
MODOS = ("comum", "scanner")


def carregar(detalhes: Path):
    docs = defaultdict(lambda: {m: [0, 0, 0] for m in MODOS})
    tipos, perdidos_tipo = {}, Counter()
    with detalhes.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            c = docs[linha["numero"]][linha["modo"]]
            c[0] += linha["status"] == "exato"
            c[1] += 1
            c[2] += linha["status"] == "perdido"
            tipos[linha["numero"]] = linha["tipo"]
            if linha["status"] == "perdido":
                perdidos_tipo[(linha["modo"], linha["tipo"])] += 1
    incompletos = [n for n, d in docs.items() if any(d[m][1] == 0 for m in MODOS)]
    if incompletos:
        sys.exit(f"Documentos sem os dois modos: {incompletos[:5]}")
    return docs, tipos, perdidos_tipo


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detalhes", type=Path, default=DETALHES_PADRAO)
    parser.add_argument("--repeticoes", type=int, default=5000)
    parser.add_argument("--semente", type=int, default=20261115)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()

    docs, tipos, perdidos_tipo = carregar(args.detalhes)
    numeros = sorted(docs, key=int)
    ex = {m: np.array([docs[n][m][0] for n in numeros], dtype=float) for m in MODOS}
    ca = {m: np.array([docs[n][m][1] for n in numeros], dtype=float) for m in MODOS}
    n = len(numeros)

    acerto = {m: ex[m].sum() / ca[m].sum() for m in MODOS}
    dif_agregada = 100 * (acerto["comum"] - acerto["scanner"])
    por_doc = 100 * (ex["comum"] / ca["comum"] - ex["scanner"] / ca["scanner"])
    dif_media = por_doc.mean()

    comum_melhor = int((ex["comum"] > ex["scanner"]).sum())
    scanner_melhor = int((ex["scanner"] > ex["comum"]).sum())
    empates = n - comum_melhor - scanner_melhor
    p_sinais = binomtest(comum_melhor, comum_melhor + scanner_melhor, 0.5).pvalue

    rng = np.random.default_rng(args.semente)
    idx = rng.integers(0, n, size=(args.repeticoes, n))
    boot_agregada = 100 * (ex["comum"][idx].sum(1) / ca["comum"][idx].sum(1)
                           - ex["scanner"][idx].sum(1) / ca["scanner"][idx].sum(1))
    boot_media = por_doc[idx].mean(1)
    ic_agregada = np.percentile(boot_agregada, [2.5, 97.5])
    ic_media = np.percentile(boot_media, [2.5, 97.5])

    perdidos = {m: sum(docs[k][m][2] for k in numeros) for m in MODOS}

    linhas = [
        ("documentos", n), ("campos_por_modo", int(ca["comum"].sum())),
        ("acerto_comum_pct", 100 * acerto["comum"]), ("acerto_scanner_pct", 100 * acerto["scanner"]),
        ("diferenca_agregada_pp", dif_agregada),
        ("ic95_agregada_inf_pp", ic_agregada[0]), ("ic95_agregada_sup_pp", ic_agregada[1]),
        ("diferenca_media_por_documento_pp", dif_media),
        ("ic95_media_inf_pp", ic_media[0]), ("ic95_media_sup_pp", ic_media[1]),
        ("documentos_comum_melhor", comum_melhor), ("documentos_scanner_melhor", scanner_melhor),
        ("documentos_empate", empates), ("p_teste_sinais", p_sinais),
        ("perdidos_comum", perdidos["comum"]), ("perdidos_scanner", perdidos["scanner"]),
        ("repeticoes", args.repeticoes), ("semente", args.semente),
    ]
    linhas += [(f"perdidos_comum_{t}", perdidos_tipo[("comum", t)])
               for t in sorted({t for _, t in perdidos_tipo}) if perdidos_tipo[("comum", t)]]

    args.saida.mkdir(parents=True, exist_ok=True)
    destino = args.saida / "bootstrap_captura.csv"
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["medida", "valor"])
        for nome, valor in linhas:
            w.writerow([nome, f"{valor:.6g}" if isinstance(valor, float) else valor])

    print(f"Documentos pareados: {n}  (campos por modo: {int(ca['comum'].sum())})")
    print(f"Acerto exato: câmera comum {100 * acerto['comum']:.1f}%  scanner {100 * acerto['scanner']:.1f}%")
    print(f"Diferença (agregada): {dif_agregada:.2f} pp  IC 95% bootstrap [{ic_agregada[0]:.2f}; {ic_agregada[1]:.2f}]")
    print(f"Diferença (média por documento): {dif_media:.2f} pp  IC 95% bootstrap [{ic_media[0]:.2f}; {ic_media[1]:.2f}]")
    print(f"Teste dos sinais: comum melhor {comum_melhor}, scanner melhor {scanner_melhor}, "
          f"empate {empates}; p = {p_sinais:.2g}")
    print(f"Campos perdidos: comum {perdidos['comum']}, scanner {perdidos['scanner']}; "
          f"comum por tipo: {dict((t, k) for (m, t), k in perdidos_tipo.items() if m == 'comum')}")
    print(f"({args.repeticoes} reamostragens, semente {args.semente})\nSalvo em {destino}")


if __name__ == "__main__":
    main()
