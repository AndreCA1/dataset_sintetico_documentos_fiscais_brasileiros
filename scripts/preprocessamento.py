"""Experimento 3: pré-processamento com OpenCV antes do ML Kit nas fotos da câmera comum.

Variantes: original, recodificada (JPEG sem alterar os pixels), cinza, mediana (3x3),
clahe, inclinacao (até ±10°), adaptativa, otsu e completo
(cinza -> mediana -> inclinação -> limiar adaptativo).

  coletar    gera as variantes e as serve ao teste de integração do app (não publicado)
  relatorio  gera relatorio.md e detalhes.csv a partir do ocr.jsonl

Uso: python3 scripts/preprocessamento.py relatorio [--saida DIR]
Gerar as variantes requer opencv-python-headless e numpy.
"""
import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from avaliar_ocr import (CAMPOS, DATASET_PADRAO, RAIZ_REPO, TIPOS, avaliar_campo, carregar_dataset,
                         digitos, ler_resultados, normalizar, pct, pegar, tabela_md)

VARIANTES = ("original", "recodificada", "cinza", "mediana", "clahe", "inclinacao",
             "adaptativa", "otsu", "completo")
ROTULO = {
    "original": "Original", "recodificada": "Recodificada", "cinza": "Escala de cinza",
    "mediana": "Mediana 3x3", "clahe": "CLAHE", "inclinacao": "Correção de inclinação",
    "adaptativa": "Limiar adaptativo", "otsu": "Limiar de Otsu", "completo": "Pipeline completo",
}
QUALIDADE_JPEG = 95
ADAPTATIVA_C = 15
INCLINACAO_MAX = 10.0
INCLINACAO_PASSO = 0.5


def _cv():
    import cv2
    import numpy as np
    return cv2, np


def bloco_adaptativo(cinza) -> int:
    lado = max(31, min(cinza.shape[:2]) // 100)
    return lado if lado % 2 else lado + 1


def limiar_adaptativo(cinza):
    cv2, _ = _cv()
    return cv2.adaptiveThreshold(cinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, bloco_adaptativo(cinza), ADAPTATIVA_C)


def angulo_inclinacao(cinza) -> float:
    cv2, np = _cv()
    escala = 1000 / max(cinza.shape[:2])
    pequena = cv2.resize(cinza, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
    binaria = cv2.adaptiveThreshold(pequena, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 15, 10)
    h, w = binaria.shape
    centro = (w / 2, h / 2)
    y0, y1, x0, x1 = int(h * 0.2), int(h * 0.8), int(w * 0.2), int(w * 0.8)
    melhor, melhor_angulo = -1.0, 0.0
    passos = int(2 * INCLINACAO_MAX / INCLINACAO_PASSO) + 1
    for i in range(passos):
        angulo = -INCLINACAO_MAX + i * INCLINACAO_PASSO
        m = cv2.getRotationMatrix2D(centro, angulo, 1.0)
        girada = cv2.warpAffine(binaria, m, (w, h), flags=cv2.INTER_NEAREST)
        perfil = girada[y0:y1, x0:x1].sum(axis=1, dtype=np.float64)
        valor = float(np.sum(np.diff(perfil) ** 2))
        if valor > melhor:
            melhor, melhor_angulo = valor, angulo
    return melhor_angulo


def girar(imagem, angulo: float):
    cv2, _ = _cv()
    if abs(angulo) < INCLINACAO_PASSO / 2:
        return imagem
    h, w = imagem.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angulo, 1.0)
    return cv2.warpAffine(imagem, m, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def gerar(variante: str, caminho: Path):
    if variante == "original":
        return caminho.read_bytes(), {}
    cv2, np = _cv()
    dados = np.frombuffer(caminho.read_bytes(), dtype=np.uint8)
    # IMREAD_COLOR aplica a orientação EXIF, como o ML Kit.
    cor = cv2.imdecode(dados, cv2.IMREAD_COLOR)
    if cor is None:
        raise ValueError(f"não consegui decodificar {caminho}")
    extras = {}
    if variante == "recodificada":
        saida = cor
    elif variante == "inclinacao":
        angulo = angulo_inclinacao(cv2.cvtColor(cor, cv2.COLOR_BGR2GRAY))
        extras["angulo"] = angulo
        saida = girar(cor, angulo)
    else:
        cinza = cv2.cvtColor(cor, cv2.COLOR_BGR2GRAY)
        if variante == "cinza":
            saida = cinza
        elif variante == "mediana":
            saida = cv2.medianBlur(cinza, 3)
        elif variante == "clahe":
            saida = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(cinza)
        elif variante == "adaptativa":
            saida = limiar_adaptativo(cinza)
        elif variante == "otsu":
            _, saida = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif variante == "completo":
            suave = cv2.medianBlur(cinza, 3)
            angulo = angulo_inclinacao(suave)
            extras["angulo"] = angulo
            saida = limiar_adaptativo(girar(suave, angulo))
        else:
            raise ValueError(variante)
    ok, jpeg = cv2.imencode(".jpg", saida, [cv2.IMWRITE_JPEG_QUALITY, QUALIDADE_JPEG])
    if not ok:
        raise ValueError(f"não consegui codificar {variante} de {caminho}")
    return jpeg.tobytes(), extras


def carregar_fotos(pasta_reais: Path, pasta_fotos: Path | None = None):
    pasta_fotos = pasta_fotos or pasta_reais / "fotos"
    fotos = {}
    for linha in (pasta_reais / "capturas.jsonl").read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        reg = json.loads(linha)
        if reg["modo"] != "comum":
            continue
        fotos[reg["numero"]] = {"tipo": reg["tipo"], "id": reg["id"],
                                "arquivo": pasta_fotos / reg["arquivo"]}
    return dict(sorted(fotos.items()))


def chave(variante: str, numero: int) -> str:
    return f"{variante}/{numero:03d}"


def coletar(args):
    fotos = carregar_fotos(args.reais, args.fotos)
    if args.limite:
        fotos = dict(list(fotos.items())[: args.limite])
    variantes = args.variantes or VARIANTES
    itens = {chave(v, n): (v, n) for n in fotos for v in variantes}
    args.saida.mkdir(parents=True, exist_ok=True)
    jsonl = args.saida / "ocr.jsonl"
    extras_jsonl = args.saida / "variantes.jsonl"
    feitos = set(ler_resultados(jsonl))
    pendentes = [c for c in itens if c not in feitos]
    print(f"{len(fotos)} fotos x {len(variantes)} variantes = {len(itens)} imagens, "
          f"{len(feitos & set(itens))} já processadas, {len(pendentes)} pendentes. "
          f"Gravando em {jsonl}", flush=True)
    estado = {"recebidos": 0}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _responder(self, corpo: bytes, tipo="application/json", status=200):
            self.send_response(status)
            self.send_header("content-type", tipo)
            self.send_header("content-length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/lista":
                lista = [{"chave": c, "nome": c.replace("/", "_") + ".jpg"} for c in pendentes]
                return self._responder(json.dumps(lista).encode())
            if url.path == "/img":
                c = parse_qs(url.query).get("chave", [""])[0]
                if c not in itens:
                    return self._responder(b"{}", status=404)
                variante, numero = itens[c]
                corpo, extras = gerar(variante, fotos[numero]["arquivo"])
                with extras_jsonl.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"chave": c, "bytes": len(corpo), **extras}) + "\n")
                return self._responder(corpo, "application/octet-stream")
            self._responder(b"{}", status=404)

        def do_POST(self):
            corpo = self.rfile.read(int(self.headers.get("content-length", 0)))
            if self.path == "/resultado":
                registro = json.loads(corpo)
                with jsonl.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(registro, ensure_ascii=False) + "\n")
                estado["recebidos"] += 1
                aviso = f" ERRO: {registro['erro']}" if "erro" in registro else ""
                print(f"[{estado['recebidos']}/{len(pendentes)}] {registro['chave']} "
                      f"{registro['ms']} ms{aviso}", flush=True)
                return self._responder(b"{}")
            if self.path == "/fim":
                self._responder(b"{}")
                servidor.shutdown_pedido = True
                return
            self._responder(b"{}", status=404)

    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Handler)
    servidor.shutdown_pedido = False
    servidor.timeout = 1
    print(f"Servidor em http://127.0.0.1:{args.porta} aguardando o app...", flush=True)
    try:
        while not servidor.shutdown_pedido:
            servidor.handle_request()
    except KeyboardInterrupt:
        print("\nInterrompido; rode de novo para continuar de onde parou.")
    servidor.server_close()
    print(f"Coleta encerrada: {estado['recebidos']} resultados novos.")


def teste_sinais(ganhos: int, perdas: int) -> float:
    n = ganhos + perdas
    if n == 0:
        return 1.0
    k = min(ganhos, perdas)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def relatorio(args):
    fotos = carregar_fotos(args.reais, args.fotos)
    dataset = carregar_dataset(args.dataset)
    resultados = ler_resultados(args.saida / "ocr.jsonl")
    if not resultados:
        sys.exit(f"Nenhum resultado em {args.saida / 'ocr.jsonl'}. Rode a coleta antes.")

    detalhes, por_imagem = [], {}
    for variante in VARIANTES:
        for numero, foto in fotos.items():
            registro = resultados.get(chave(variante, numero))
            if registro is None:
                continue
            gabarito = dataset[f"{foto['tipo']}/png/{foto['id']}"]["gabarito"]
            ocr = registro.get("ocr") or {}
            texto = ocr.get("full_text") or ""
            texto_norm, texto_dig = normalizar(texto), digitos(texto)
            confs = [l["confidence"] for b in ocr.get("blocks", [])
                     for l in b.get("lines") or [] if l.get("confidence") is not None]
            contagem = Counter()
            for nome, caminho, formato in CAMPOS[foto["tipo"]]:
                valor = pegar(gabarito, caminho)
                if valor is None:
                    continue
                status, dist = avaliar_campo(valor, formato, texto_norm, texto_dig)
                contagem[status] += 1
                detalhes.append({"variante": variante, "numero": numero, "tipo": foto["tipo"],
                                 "id": foto["id"], "campo": nome, "esperado": valor,
                                 "status": status, "distancia": "" if dist is None else dist})
            por_imagem[(variante, numero)] = {
                "tipo": foto["tipo"], "campos": sum(contagem.values()),
                "exato": contagem["exato"], "quase": contagem["quase"],
                "perdido": contagem["perdido"], "ms": registro.get("ms"),
                "erro": registro.get("erro"), "vazio": not texto.strip(),
                "conf": statistics.mean(confs) if confs else None,
            }

    variantes = [v for v in VARIANTES if any(k[0] == v for k in por_imagem)]
    numeros = [n for n in fotos if all((v, n) in por_imagem for v in variantes)]
    incompletos = len({n for _, n in por_imagem}) - len(numeros)

    def soma(variante, tipo, campo):
        return sum(por_imagem[(variante, n)][campo] for n in numeros
                   if tipo == "TOTAL" or por_imagem[(variante, n)]["tipo"] == tipo)

    cab1 = ["Variante", *TIPOS, "**Total**"]
    tab1 = [[ROTULO[v], *[pct(soma(v, t, "exato"), soma(v, t, "campos"))
                          for t in (*TIPOS, "TOTAL")]] for v in variantes]

    cab2 = ["Variante", "Exato", "Quase (≤2)", "Perdido", "Imagens 100%", "Vazias/erro",
            "Confiança média", "ms/imagem", "Melhor que original", "Pior", "Empate",
            "p (sinais)"]
    tab2 = []
    for v in variantes:
        imgs = [por_imagem[(v, n)] for n in numeros]
        campos = sum(i["campos"] for i in imgs)
        linha = [ROTULO[v], pct(sum(i["exato"] for i in imgs), campos),
                 pct(sum(i["quase"] for i in imgs), campos),
                 pct(sum(i["perdido"] for i in imgs), campos),
                 sum(1 for i in imgs if i["exato"] == i["campos"]),
                 sum(1 for i in imgs if i["vazio"] or i["erro"]),
                 f"{statistics.mean(c for c in (i['conf'] for i in imgs) if c is not None):.3f}"
                 if any(i["conf"] is not None for i in imgs) else "-",
                 f"{statistics.mean(i['ms'] for i in imgs):.0f}"]
        if v == "original" or "original" not in variantes:
            linha += ["-", "-", "-", "-"]
        else:
            difs = [por_imagem[(v, n)]["exato"] - por_imagem[("original", n)]["exato"]
                    for n in numeros]
            ganhos, perdas = sum(d > 0 for d in difs), sum(d < 0 for d in difs)
            linha += [ganhos, perdas, sum(d == 0 for d in difs),
                      f"{teste_sinais(ganhos, perdas):.3g}"]
        tab2.append(linha)

    angulos = defaultdict(list)
    caminho_extras = args.saida / "variantes.jsonl"
    if caminho_extras.exists():
        ultimo = {}
        for linha in caminho_extras.read_text(encoding="utf-8").splitlines():
            reg = json.loads(linha)
            ultimo[reg["chave"]] = reg
        for c, reg in ultimo.items():
            if "angulo" in reg:
                angulos[c.split("/")[0]].append(abs(reg["angulo"]))
    linhas_ang = [[ROTULO[v], len(a), f"{statistics.median(a):.1f}", f"{max(a):.1f}",
                   sum(1 for x in a if x >= INCLINACAO_MAX)] for v, a in angulos.items()]

    md = [
        "# Pré-processamento com OpenCV antes do ML Kit (fotos reais, câmera comum)",
        "",
        f"Gerado em {datetime.now():%Y-%m-%d %H:%M}. Documentos com todas as variantes: "
        f"{len(numeros)}" + (f" ({incompletos} incompletos ficaram de fora)." if incompletos else "."),
        "",
        "Mesma métrica por campo do benchmark (`avaliar_ocr.py`). Todas as variantes, "
        "inclusive a original, passaram pelo ML Kit na mesma execução e no mesmo aparelho. "
        f"As variantes tratadas são gravadas em JPEG com qualidade {QUALIDADE_JPEG}; "
        "*Recodificada* isola o efeito dessa regravação.",
        "",
        "## Acerto exato por tipo",
        "",
        tabela_md(cab1, tab1),
        "",
        "## Resumo e comparação pareada com a foto original",
        "",
        "Comparação documento a documento pelo número de campos exatos; *p* é o teste dos "
        "sinais bilateral, sem correção para comparações múltiplas.",
        "",
        tabela_md(cab2, tab2),
        "",
    ]
    if linhas_ang:
        md += ["## Correção de inclinação", "",
               tabela_md(["Variante", "Imagens", "Ângulo mediano (°, módulo)", "Máximo (°)",
                          f"No limite de {INCLINACAO_MAX:.0f}°"], linhas_ang), ""]
    (args.saida / "relatorio.md").write_text("\n".join(md), encoding="utf-8")
    with (args.saida / "detalhes.csv").open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(detalhes[0]))
        escritor.writeheader()
        escritor.writerows(detalhes)
    print("\n".join(md))
    print(f"Relatório: {args.saida / 'relatorio.md'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("passo", choices=["coletar", "relatorio"])
    parser.add_argument("--reais", type=Path,
                        default=RAIZ_REPO / "resultados" / "experimento2_fotos_reais",
                        help="pasta com o capturas.jsonl do teste com fotos reais")
    parser.add_argument("--fotos", type=Path, default=RAIZ_REPO / "dados" / "fotos_reais" / "fotos",
                        help="pasta das fotos NNN_comum.jpg")
    parser.add_argument("--dataset", type=Path, default=DATASET_PADRAO)
    parser.add_argument("--saida", type=Path,
                        default=RAIZ_REPO / "resultados" / "experimento3_preprocessamento")
    parser.add_argument("--porta", type=int, default=8767)
    parser.add_argument("--limite", type=int, default=0, help="só as N primeiras fotos")
    parser.add_argument("--variantes", nargs="*", choices=VARIANTES)
    args = parser.parse_args()
    coletar(args) if args.passo == "coletar" else relatorio(args)


if __name__ == "__main__":
    main()
