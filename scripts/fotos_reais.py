"""Experimento 2: OCR nas fotos reais, câmera comum × scanner.

  coletar    recebe as capturas da tela do app (não publicado) em fotos/ e capturas.jsonl
  relatorio  avalia cada captura contra o gabarito e gera relatorio.md e detalhes.csv

Uso: python3 scripts/fotos_reais.py relatorio [--saida DIR] [--base DETALHES_EXPERIMENTO1]
"""
import argparse
import base64
import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from avaliar_ocr import (CAMPOS, DATASET_PADRAO, RAIZ_REPO, TIPOS, avaliar_campo, carregar_dataset,
                         digitos, normalizar, pct, pegar, tabela_md)

MODOS = ("comum", "scanner")
NOME_MODO = {"comum": "câmera comum", "scanner": "scanner"}
LIMIAR_CONFIANCA = 0.74


def ler_lista(caminho: Path):
    with caminho.open(encoding="utf-8") as f:
        return [{"numero": int(l["numero"]), "tipo": l["tipo"], "id": l["id"]}
                for l in csv.DictReader(f)]


def ler_capturas(caminho: Path):
    capturas = {}
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                registro = json.loads(linha)
                capturas[(registro["numero"], registro["modo"])] = registro
    return capturas


def coletar(args):
    lista = ler_lista(args.lista)
    por_numero = {d["numero"]: d for d in lista}
    fotos = args.saida / "fotos"
    fotos.mkdir(parents=True, exist_ok=True)
    jsonl = args.saida / "capturas.jsonl"

    class Servidor(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _responder(self, corpo, status=200):
            dados = json.dumps(corpo, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)

        def do_GET(self):
            if urlparse(self.path).path != "/lista":
                return self._responder({"erro": "não encontrado"}, 404)
            feitos = defaultdict(list)
            for numero, modo in ler_capturas(jsonl):
                feitos[numero].append(modo)
            self._responder([{**d, "feitos": feitos[d["numero"]]} for d in lista])

        def do_POST(self):
            if urlparse(self.path).path != "/captura":
                return self._responder({"erro": "não encontrado"}, 404)
            registro = json.loads(self.rfile.read(int(self.headers["content-length"])))
            doc = por_numero.get(registro.get("numero"))
            if doc is None or registro.get("modo") not in MODOS:
                return self._responder({"erro": "número ou modo inválido"}, 400)
            arquivo = fotos / f"{doc['numero']:03d}_{registro['modo']}.jpg"
            arquivo.write_bytes(base64.b64decode(registro.pop("jpeg")))
            registro.update(tipo=doc["tipo"], id=doc["id"], arquivo=arquivo.name,
                            quando=datetime.now().isoformat(timespec="seconds"))
            with jsonl.open("a", encoding="utf-8") as f:
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")
            conf = registro.get("confianca")
            avisos = registro.get("avisos_imagem", []) + registro.get("avisos_texto", [])
            print(f"#{doc['numero']:03d} {doc['id']:11s} {registro['modo']:7s} "
                  f"{registro.get('largura')}x{registro.get('altura')} "
                  f"conf={'-' if conf is None else f'{conf:.3f}'} "
                  f"{registro['condicao']}{'  avisos: ' + ','.join(avisos) if avisos else ''}"
                  f"{'  ERRO: ' + registro['erro'] if registro.get('erro') else ''}", flush=True)
            self._responder({"ok": True})

    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Servidor)
    print(f"Recebendo capturas em http://127.0.0.1:{args.porta} -> {args.saida}  "
          f"(Ctrl+C para encerrar)", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


def avaliar_texto(tipo, gabarito, texto):
    texto_norm, texto_dig = normalizar(texto), digitos(texto)
    resultado = {}
    for nome, caminho, formato in CAMPOS[tipo]:
        valor = pegar(gabarito, caminho)
        if valor is not None:
            resultado[nome] = (valor, *avaliar_campo(valor, formato, texto_norm, texto_dig))
    return resultado


def ler_base(caminho: Path | None):
    if not caminho:
        return {}
    contagem = defaultdict(lambda: [0, 0])
    with caminho.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            c = contagem[(linha["tipo"], linha["id"], linha["variante"])]
            c[0] += linha["status"] == "exato"
            c[1] += 1
    return contagem


def relatorio(args):
    itens = carregar_dataset(args.dataset)
    capturas = ler_capturas(args.saida / "capturas.jsonl")
    if not capturas:
        sys.exit(f"Nenhuma captura em {args.saida / 'capturas.jsonl'}.")

    detalhes, imagens = [], []
    for (numero, modo), cap in sorted(capturas.items()):
        gabarito = itens[f"{cap['tipo']}/png/{cap['id']}"]["gabarito"]
        texto = (cap.get("ocr") or {}).get("full_text") or ""
        campos = avaliar_texto(cap["tipo"], gabarito, texto)
        for nome, (valor, status, dist) in campos.items():
            detalhes.append({"numero": numero, "tipo": cap["tipo"], "id": cap["id"],
                             "modo": modo, "condicao": cap.get("condicao"), "campo": nome,
                             "esperado": valor, "status": status,
                             "distancia": "" if dist is None else dist})
        exatos = sum(1 for _, s, _ in campos.values() if s == "exato")
        quase = sum(1 for _, s, _ in campos.values() if s == "quase")
        imagens.append({"numero": numero, "tipo": cap["tipo"], "id": cap["id"], "modo": modo,
                        "condicao": cap.get("condicao"), "campos": len(campos),
                        "exato": exatos, "quase": quase, "conf": cap.get("confianca"),
                        "avisos_imagem": cap.get("avisos_imagem", []),
                        "avisos_texto": cap.get("avisos_texto", []),
                        "lado": min(cap.get("largura") or 0, cap.get("altura") or 0),
                        "nitidez": cap.get("nitidez"), "ms": cap.get("ms"),
                        "erro": cap.get("erro")})

    def resumo(grupo):
        campos = sum(i["campos"] for i in grupo)
        confs = [i["conf"] for i in grupo if i["conf"] is not None]
        return [len(grupo), campos, pct(sum(i["exato"] for i in grupo), campos),
                pct(sum(i["quase"] for i in grupo), campos),
                sum(1 for i in grupo if i["exato"] == i["campos"]),
                f"{statistics.mean(confs):.3f}" if confs else "-",
                sum(1 for i in grupo if i["conf"] is not None and i["conf"] < LIMIAR_CONFIANCA),
                sum(1 for i in grupo if i["avisos_imagem"]),
                f"{statistics.median([i['lado'] for i in grupo]):.0f}"]

    cab = ["Tipo", "Modo", "Imagens", "Campos", "Exato", "Quase", "Imagens 100%",
           "Confiança média", "Confiança < 0,74", "Aviso imagem", "Menor lado (px, mediana)"]
    linhas = []
    for tipo in (*TIPOS, "TOTAL"):
        for modo in MODOS:
            grupo = [i for i in imagens if i["modo"] == modo and tipo in ("TOTAL", i["tipo"])]
            if grupo:
                linhas.append([f"**{tipo}**" if tipo == "TOTAL" else tipo, NOME_MODO[modo],
                               *resumo(grupo)])

    por_doc = defaultdict(dict)
    for i in imagens:
        por_doc[i["numero"]][i["modo"]] = i
    pares = [d for d in por_doc.values() if len(d) == 2]
    melhor = defaultdict(int)
    for d in pares:
        a, b = (d[m]["exato"] / d[m]["campos"] for m in MODOS)
        melhor["scanner" if b > a else "comum" if a > b else "empate"] += 1

    base = ler_base(args.base)
    linhas_base = []
    if base:
        for tipo in (*TIPOS, "TOTAL"):
            docs = [d for d in pares if tipo in ("TOTAL", d["comum"]["tipo"])]
            if not docs:
                continue
            linha = [f"**{tipo}**" if tipo == "TOTAL" else tipo, len(docs)]
            for variante in ("png", "foto"):
                e = sum(base[(d["comum"]["tipo"], d["comum"]["id"], variante)][0] for d in docs)
                t = sum(base[(d["comum"]["tipo"], d["comum"]["id"], variante)][1] for d in docs)
                linha.append(pct(e, t))
            for modo in MODOS:
                e = sum(d[modo]["exato"] for d in docs)
                t = sum(d[modo]["campos"] for d in docs)
                linha.append(pct(e, t))
            linhas_base.append(linha)

    linhas_cond = []
    for condicao in sorted({i["condicao"] for i in imagens}):
        for modo in MODOS:
            grupo = [i for i in imagens if i["modo"] == modo and i["condicao"] == condicao]
            if grupo:
                linhas_cond.append([condicao, NOME_MODO[modo], *resumo(grupo)[:7]])

    linhas_limiar = []
    for limiar in (0.70, 0.72, LIMIAR_CONFIANCA, 0.76, 0.78, 0.80):
        avisadas = [i for i in imagens if i["conf"] is not None and i["conf"] < limiar]
        ruins = [i for i in imagens if i["exato"] / i["campos"] < 0.75]
        demais = [i for i in imagens if i not in avisadas]
        acerto = lambda g: pct(sum(i["exato"] for i in g), sum(i["campos"] for i in g))
        linhas_limiar.append([
            f"**{limiar:.2f}**" if limiar == LIMIAR_CONFIANCA else f"{limiar:.2f}",
            len(avisadas), f"{sum(1 for i in avisadas if i in ruins)}/{len(ruins)}",
            sum(1 for i in avisadas if i["exato"] == i["campos"]), acerto(avisadas),
            acerto(demais)])

    piores = sorted(imagens, key=lambda i: (i["exato"] / i["campos"], i["numero"]))[:15]
    linhas_piores = [[f"#{i['numero']:03d}", i["id"], NOME_MODO[i["modo"]], i["condicao"],
                      f"{i['exato']}/{i['campos']}",
                      "-" if i["conf"] is None else f"{i['conf']:.3f}",
                      ", ".join(i["avisos_imagem"] + i["avisos_texto"]) or ""]
                     for i in piores]

    md = [
        "# OCR com fotos reais: câmera comum × scanner",
        "",
        f"Gerado em {datetime.now():%Y-%m-%d %H:%M}. Capturas: {len(imagens)}; "
        f"documentos com as duas capturas: {len(pares)}.",
        "",
        "Documentos sintéticos impressos (amostra de `impressao/lista.csv`; NF-e e NFS-e "
        "reduzidas a 95% para caber na área imprimível) e fotografados com o celular. "
        "Mesma métrica por campo do benchmark sintético (`avaliar_ocr.py`). *Confiança < 0,74* "
        "conta as capturas que o aviso de leitura incerta (retirado do app em 2026-11-15) "
        "teria avisado; *aviso imagem* = resolução baixa, escura ou desfocada.",
        "",
        "## Resumo",
        "",
        tabela_md(cab, linhas),
        "",
        "## Comparação pareada",
        "",
        f"Em {len(pares)} documentos com as duas capturas, o scanner acertou mais campos em "
        f"{melhor['scanner']}, a câmera comum em {melhor['comum']} e houve empate em "
        f"{melhor['empate']}.",
        "",
    ]
    if linhas_base:
        md += ["## Sintético × real (mesmos documentos, acerto exato)", "",
               tabela_md(["Tipo", "Documentos", "PNG", "Foto sintética", "Câmera comum",
                          "Scanner"], linhas_base), ""]
    md += [
        "## Por condição de captura", "",
        tabela_md(["Condição", "Modo", *cab[2:9]], linhas_cond), "",
        "## Limiar de confiança nas fotos reais", "",
        "Captura ruim = menos de 75% dos campos certos, como na varredura sintética.", "",
        tabela_md(["Limiar", "Avisos", "Capturas ruins avisadas", "Avisos sem erro",
                   "Acerto das avisadas", "Acerto das demais"], linhas_limiar), "",
        "## Piores capturas", "",
        tabela_md(["Nº", "Documento", "Modo", "Condição", "Campos exatos", "Confiança",
                   "Avisos"], linhas_piores), "",
    ]
    (args.saida / "relatorio.md").write_text("\n".join(md), encoding="utf-8")
    with (args.saida / "detalhes.csv").open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(detalhes[0]))
        escritor.writeheader()
        escritor.writerows(detalhes)
    print(tabela_md(cab, linhas))
    print(f"\nRelatório: {args.saida / 'relatorio.md'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="passo", required=True)
    p_col = sub.add_parser("coletar")
    p_col.add_argument("--saida", type=Path, required=True)
    p_col.add_argument("--lista", type=Path, default=RAIZ_REPO / "dados" / "fotos_reais" / "lista.csv")
    p_col.add_argument("--porta", type=int, default=8766)
    p_rel = sub.add_parser("relatorio")
    p_rel.add_argument("--saida", type=Path,
                       default=RAIZ_REPO / "resultados" / "experimento2_fotos_reais")
    p_rel.add_argument("--dataset", type=Path, default=DATASET_PADRAO)
    p_rel.add_argument("--base", type=Path,
                       default=RAIZ_REPO / "resultados" / "experimento1_sintetico" / "detalhes.csv",
                       help="detalhes.csv do benchmark sintético (opcional)")
    args = parser.parse_args()
    if args.passo == "relatorio" and args.base and not args.base.exists():
        args.base = None
    coletar(args) if args.passo == "coletar" else relatorio(args)


if __name__ == "__main__":
    main()
