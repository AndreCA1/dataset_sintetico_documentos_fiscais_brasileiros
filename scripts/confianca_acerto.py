"""Confiança média das linhas do ML Kit × acerto exato por imagem (experimento 1).

Spearman e Pearson nas 500 imagens e nas 250 fotos simuladas, e varredura de
limiares do aviso de leitura incerta (imagem ruim = acerto exato < 75%).

Uso: python3 scripts/confianca_acerto.py [--saida-benchmark DIR] [--saida DIR]
Requer scipy.
"""
import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

try:
    from scipy.stats import pearsonr, spearmanr
except ImportError:
    sys.exit("Este script requer scipy (pip install scipy).")

RAIZ_REPO = Path(__file__).resolve().parents[1]
BENCHMARK_PADRAO = RAIZ_REPO / "resultados" / "experimento1_sintetico"
SAIDA_PADRAO = RAIZ_REPO / "resultados" / "analises"
LIMIAR_APP = 0.74
CORTE_RUIM = 0.75
LIMIARES = (0.65, 0.68, 0.70, 0.72, 0.74, 0.75, 0.76, 0.78, 0.80)


def confianca_por_imagem(ocr_jsonl: Path):
    conf, sem_conf = {}, 0
    with ocr_jsonl.open(encoding="utf-8") as f:
        for linha in f:
            registro = json.loads(linha)
            linhas = [l for b in (registro.get("ocr") or {}).get("blocks", []) for l in b.get("lines") or []]
            valores = [l["confidence"] for l in linhas if l.get("confidence") is not None]
            sem_conf += len(linhas) - len(valores)
            if valores:
                conf[registro["chave"]] = statistics.mean(valores)
    return conf, sem_conf


def acerto_por_imagem(detalhes: Path):
    contagem = defaultdict(lambda: [0, 0])
    with detalhes.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            c = contagem[linha["chave"]]
            c[0] += linha["status"] == "exato"
            c[1] += 1
    return contagem


# Postos sem média nos empates: cálculo de 14/11 (coluna original_14_11), só para comparação.
def postos_sem_empate(v):
    ordem = sorted(range(len(v)), key=lambda i: v[i])
    postos = [0] * len(v)
    for posicao, i in enumerate(ordem):
        postos[i] = posicao
    return postos


def correlacoes(xs, ys):
    sp, pe = spearmanr(xs, ys), pearsonr(xs, ys)
    return {"n": len(xs),
            "spearman": float(sp.statistic), "p_spearman": float(sp.pvalue),
            "pearson": float(pe.statistic), "p_pearson": float(pe.pvalue),
            "original_14_11": statistics.correlation(postos_sem_empate(xs), postos_sem_empate(ys))}


def fmt_p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--saida-benchmark", type=Path, default=BENCHMARK_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()

    conf, sem_conf = confianca_por_imagem(args.saida_benchmark / "ocr.jsonl")
    acertos = acerto_por_imagem(args.saida_benchmark / "detalhes.csv")
    chaves = [c for c in acertos if c in conf]
    fora = sorted(set(acertos) - set(conf))
    acerto = {c: acertos[c][0] / acertos[c][1] for c in chaves}
    ruim = {c: acerto[c] < CORTE_RUIM for c in chaves}

    recortes = [("500 imagens", chaves), ("fotos", [c for c in chaves if "/foto/" in c])]
    linhas_corr = []
    for nome, cs in recortes:
        r = correlacoes([conf[c] for c in cs], [acerto[c] for c in cs])
        ruins = [c for c in cs if ruim[c]]
        linhas_corr.append({"recorte": nome, **r, "ruins": len(ruins),
                            "ruins_avisadas": sum(conf[c] < LIMIAR_APP for c in ruins)})

    linhas_lim = []
    for nome, cs in recortes:
        total_ruins = sum(ruim[c] for c in cs)
        for t in LIMIARES:
            av = [c for c in cs if conf[c] < t]
            na = [c for c in cs if conf[c] >= t]
            taxa = lambda s: sum(acertos[c][0] for c in s) / max(1, sum(acertos[c][1] for c in s))
            linhas_lim.append({
                "recorte": nome, "limiar": t, "avisos": len(av),
                "ruins_avisadas": sum(ruim[c] for c in av), "ruins": total_ruins,
                "avisos_sem_erro": sum(acertos[c][0] == acertos[c][1] for c in av),
                "avisos_em_png": sum("/png/" in c for c in av),
                "acerto_avisadas": taxa(av), "acerto_demais": taxa(na)})

    args.saida.mkdir(parents=True, exist_ok=True)
    destino_corr = args.saida / "confianca_acerto.csv"
    with destino_corr.open("w", encoding="utf-8", newline="") as f:
        campos = ["recorte", "n", "spearman", "p_spearman", "pearson", "p_pearson",
                  "original_14_11", "ruins", "ruins_avisadas"]
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for l in linhas_corr:
            w.writerow({**l, **{k: f"{l[k]:.4f}" for k in ("spearman", "pearson", "original_14_11")},
                        **{k: f"{l[k]:.6g}" for k in ("p_spearman", "p_pearson")}})
    destino_lim = args.saida / "confianca_limiares.csv"
    with destino_lim.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas_lim[0]))
        w.writeheader()
        for l in linhas_lim:
            w.writerow({**l, "limiar": f"{l['limiar']:.2f}", "acerto_avisadas": f"{l['acerto_avisadas']:.4f}",
                        "acerto_demais": f"{l['acerto_demais']:.4f}"})

    print(f"Imagens: {len(chaves)}  (sem confiança: {len(fora)}; linhas sem confidence: {sem_conf})")
    print(f"Ruim = acerto exato < {CORTE_RUIM:.0%}; aviso = confiança < {LIMIAR_APP}\n")
    cab = (f"{'Recorte':<12} {'n':>4} {'Spearman':>9} {'p':>8} {'Pearson':>8} {'p':>8} "
           f"{'orig. 14/11':>11} {'ruins':>6} {'avisadas':>9}")
    print(cab)
    print("-" * len(cab))
    for l in linhas_corr:
        print(f"{l['recorte']:<12} {l['n']:>4} {l['spearman']:>9.3f} {fmt_p(l['p_spearman']):>8} "
              f"{l['pearson']:>8.3f} {fmt_p(l['p_pearson']):>8} {l['original_14_11']:>11.3f} "
              f"{l['ruins']:>6} {l['ruins_avisadas']:>9}")

    png_ruins = [c for c in chaves if ruim[c] and "/png/" in c]
    for c in png_ruins:
        print(f"\nPNG limpo entre as ruins: {c} ({acertos[c][0]}/{acertos[c][1]}, confiança {conf[c]:.3f})")

    for nome, _ in recortes:
        print(f"\nVarredura de limiares ({nome}):")
        cab = (f"{'limiar':>6} {'avisos':>6} {'ruins avisadas':>14} {'sem erro':>8} "
               f"{'em PNG':>6} {'acerto avisadas':>15} {'acerto demais':>13}")
        print(cab)
        for l in (l for l in linhas_lim if l["recorte"] == nome):
            print(f"{l['limiar']:>6.2f} {l['avisos']:>6} {l['ruins_avisadas']:>8}/{l['ruins']:<5} "
                  f"{l['avisos_sem_erro']:>8} {l['avisos_em_png']:>6} {l['acerto_avisadas']:>15.1%} "
                  f"{l['acerto_demais']:>13.1%}")
    print(f"\nSalvo em {destino_corr} e {destino_lim}")


if __name__ == "__main__":
    main()
