"""CER por campo do OCR nos experimentos 1 e 2.

CER = d / n, limitado a 1: d é a menor distância de edição entre o valor esperado
e um trecho do texto normalizado; n é o tamanho do valor. CER médio = média por
campo; CER global = soma de d / soma de n.

Uso: python3 scripts/cer_campos.py [--dataset DIR] [--sintetico DIR] [--reais DIR] [--saida DIR]
"""
import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


RAIZ_REPO = Path(__file__).resolve().parents[1]


def carregar_benchmark():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import avaliar_ocr  # noqa: E402
    return avaliar_ocr


def cer_campo(av, valor, formato, texto_norm, texto_dig):
    status, _ = av.avaliar_campo(valor, formato, texto_norm, texto_dig)
    alvos = [a for a in av.esperados(valor, formato) if a]
    if status == "exato":
        n = min(len(a) for a in alvos)
        return status, 0, n, 0.0
    base = texto_dig if formato == "digitos" else texto_norm
    melhor = None
    for alvo in alvos:
        d = av.menor_distancia(alvo, base) if base else len(alvo)
        cer = min(d / len(alvo), 1.0)
        if melhor is None or cer < melhor[2]:
            melhor = (min(d, len(alvo)), len(alvo), cer)
    return (status, *melhor)


def avaliar_texto(av, tipo, gabarito, texto):
    texto_norm, texto_dig = av.normalizar(texto), av.digitos(texto)
    for nome, caminho, formato in av.CAMPOS[tipo]:
        valor = av.pegar(gabarito, caminho)
        if valor is None:
            continue
        yield nome, valor, cer_campo(av, valor, formato, texto_norm, texto_dig)


def linhas_sintetico(av, itens, pasta: Path):
    resultados = av.ler_resultados(pasta / "ocr.jsonl")
    for chave, item in itens.items():
        reg = resultados.get(chave)
        if reg is None:
            continue
        texto = (reg.get("ocr") or {}).get("full_text") or ""
        for nome, valor, (status, d, n, cer) in avaliar_texto(av, item["tipo"], item["gabarito"], texto):
            yield {"conjunto": "sintetico", "variante": item["variante"], "tipo": item["tipo"],
                   "documento": item["id"], "campo": nome, "esperado": valor,
                   "status": status, "d": d, "n": n, "cer": cer}


def linhas_reais(av, itens, pasta: Path):
    capturas = {}
    for linha in (pasta / "capturas.jsonl").read_text(encoding="utf-8").splitlines():
        if linha.strip():
            reg = json.loads(linha)
            capturas[(reg["numero"], reg["modo"])] = reg
    nome_modo = {"comum": "camera", "scanner": "scanner"}
    for (_, modo), cap in sorted(capturas.items()):
        gabarito = itens[f"{cap['tipo']}/png/{cap['id']}"]["gabarito"]
        texto = (cap.get("ocr") or {}).get("full_text") or ""
        for nome, valor, (status, d, n, cer) in avaliar_texto(av, cap["tipo"], gabarito, texto):
            yield {"conjunto": "real", "variante": nome_modo[modo], "tipo": cap["tipo"],
                   "documento": cap["id"], "campo": nome, "esperado": valor,
                   "status": status, "d": d, "n": n, "cer": cer}


def resumo(grupo):
    cers = [l["cer"] for l in grupo]
    soma_n = sum(l["n"] for l in grupo)
    return {
        "campos": len(grupo),
        "exato": sum(l["status"] == "exato" for l in grupo) / len(grupo),
        "cer_medio": statistics.mean(cers),
        "cer_global": sum(l["d"] for l in grupo) / soma_n if soma_n else 0.0,
        "cer_mediana_erros": statistics.median([c for c in cers if c > 0]) if any(cers) else 0.0,
    }


def pct(x):
    return f"{100 * x:.1f}%"


def tabela(cab, linhas):
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" if i == 0 else "---:" for i in range(len(cab))) + "|"]
    out += ["| " + " | ".join(str(c) for c in l) + " |" for l in linhas]
    return "\n".join(out)


VARIANTES = [("sintetico", "png", "Sintético PNG"), ("sintetico", "foto", "Sintético foto"),
             ("real", "camera", "Real câmera"), ("real", "scanner", "Real scanner")]


def relatorio(av, linhas):
    grupos = defaultdict(list)
    for l in linhas:
        grupos[(l["conjunto"], l["variante"], l["tipo"])].append(l)
        grupos[(l["conjunto"], l["variante"], "TOTAL")].append(l)

    partes = ["# CER por campo do OCR (ML Kit)", "",
              "CER = distância de edição entre o valor esperado e o trecho mais parecido do texto "
              "do OCR, dividida pelo tamanho do valor esperado (limitada a 1). *CER médio* é a média "
              "por campo; *CER global* é Σd/Σn. *Mediana nos erros* considera só os campos com CER > 0.",
              "", "## Por tipo e variante", ""]
    cab = ["Variante", "Tipo", "Campos", "Exato", "CER médio", "CER global", "Mediana nos erros"]
    tab = []
    for conj, var, rotulo in VARIANTES:
        for tipo in (*av.TIPOS, "TOTAL"):
            g = grupos.get((conj, var, tipo))
            if not g:
                continue
            r = resumo(g)
            tab.append([rotulo, f"**{tipo}**" if tipo == "TOTAL" else tipo, r["campos"], pct(r["exato"]),
                        pct(r["cer_medio"]), pct(r["cer_global"]), pct(r["cer_mediana_erros"])])
    partes += [tabela(cab, tab), "", "## Por campo (CER médio)", ""]

    por_campo = defaultdict(list)
    for l in linhas:
        por_campo[(l["tipo"], l["campo"], l["conjunto"], l["variante"])].append(l)
    cab = ["Tipo", "Campo"] + [r for *_, r in VARIANTES]
    tab = []
    for tipo in av.TIPOS:
        for nome, _, _ in av.CAMPOS[tipo]:
            celulas = []
            for conj, var, _ in VARIANTES:
                g = por_campo.get((tipo, nome, conj, var))
                celulas.append(pct(statistics.mean(l["cer"] for l in g)) if g else "-")
            if any(c != "-" for c in celulas):
                tab.append([tipo, nome, *celulas])
    partes += [tabela(cab, tab), ""]
    return "\n".join(partes)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", type=Path, default=RAIZ_REPO / "dados" / "sinteticos")
    p.add_argument("--sintetico", type=Path, default=RAIZ_REPO / "resultados" / "experimento1_sintetico")
    p.add_argument("--reais", type=Path, default=RAIZ_REPO / "resultados" / "experimento2_fotos_reais")
    p.add_argument("--saida", type=Path, default=RAIZ_REPO / "resultados" / "cer")
    args = p.parse_args()

    av = carregar_benchmark()
    itens = av.carregar_dataset(args.dataset)
    linhas = []
    if args.sintetico:
        linhas += linhas_sintetico(av, itens, args.sintetico)
    if args.reais:
        linhas += linhas_reais(av, itens, args.reais)
    if not linhas:
        sys.exit("Nada a avaliar: passe --sintetico e/ou --reais.")

    args.saida.mkdir(parents=True, exist_ok=True)
    with (args.saida / "cer_campos.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        for l in linhas:
            w.writerow({**l, "cer": f"{l['cer']:.4f}"})
    md = relatorio(av, linhas)
    (args.saida / "cer.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
