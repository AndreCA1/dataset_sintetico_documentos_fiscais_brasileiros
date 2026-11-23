"""Benchmark do OCR (ML Kit) no conjunto sintético: métrica por campo e relatório.

Status de cada campo: exato (o valor do gabarito aparece no texto, após normalizar
caixa, acentos e espaços; só dígitos para CPF, CNPJ, chave, linha digitável e
nosso número), quase (trecho a até 2 edições) ou perdido.

  coletar    serve as imagens ao teste de integração do app (não publicado) e grava ocr.jsonl
  relatorio  gera relatorio.md e detalhes.csv a partir do ocr.jsonl

Uso: python3 scripts/avaliar_ocr.py relatorio [--saida DIR] [--piores 25]
"""
import argparse
import csv
import json
import re
import statistics
import sys
import unicodedata
import os
from collections import defaultdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ_REPO = Path(__file__).resolve().parents[1]
DATASET_PADRAO = Path(os.environ.get("OCR_DATASET", RAIZ_REPO / "dados" / "sinteticos"))
VARIANTES = ("png", "foto")
TIPOS = ("boleto", "nfe", "nfce", "nfse", "recibo")
MAX_EDICOES_QUASE = 2

# (nome no relatório, caminho no gabarito, formato)
CAMPOS_NF = [
    ("chave_acesso", "chave_acesso", "digitos"),
    ("numero", "numero", "numero_nf"),
    ("data_emissao", "data_emissao", "data"),
    ("valor_total", "valor_total", "dinheiro"),
    ("emitente_nome", "emitente.nome", "texto"),
    ("emitente_documento", "emitente.documento", "digitos"),
    ("destinatario_nome", "destinatario.nome", "texto"),
    ("destinatario_documento", "destinatario.documento", "digitos"),
]
CAMPOS = {
    "boleto": [
        ("linha_digitavel", "linha_digitavel", "digitos"),
        ("valor_documento", "valor_documento", "dinheiro"),
        ("data_vencimento", "data_vencimento", "data"),
        ("data_documento", "data_documento", "data"),
        ("numero_documento", "numero_documento", "texto"),
        ("nosso_numero", "nosso_numero", "digitos"),
        ("beneficiario_nome", "beneficiario.nome", "texto"),
        ("beneficiario_cnpj", "beneficiario.cnpj", "digitos"),
        ("pagador_nome", "pagador.nome", "texto"),
        ("pagador_cpf", "pagador.cpf", "digitos"),
    ],
    "nfe": CAMPOS_NF,
    "nfce": CAMPOS_NF,
    "nfse": [
        ("chave_acesso", "chave_acesso", "digitos"),
        ("numero", "numero", "texto"),
        ("data_emissao", "data_emissao", "data"),
        ("valor_total", "valor_total", "dinheiro"),
        ("valor_iss", "valor_iss", "dinheiro"),
        ("emitente_nome", "emitente.nome", "texto"),
        ("emitente_documento", "emitente.documento", "digitos"),
        ("destinatario_nome", "destinatario.nome", "texto"),
        ("destinatario_documento", "destinatario.documento", "digitos"),
    ],
    "recibo": [
        ("numero", "numero", "texto"),
        ("data", "data", "data"),
        ("valor", "valor", "dinheiro"),
        ("historico", "historico", "texto"),
        ("pagador_nome", "pagador.nome", "texto"),
        ("pagador_documento", "pagador.documento", "digitos"),
        ("recebedor_nome", "recebedor.nome", "texto"),
        ("recebedor_documento", "recebedor.documento", "digitos"),
    ],
}


def carregar_dataset(raiz: Path):
    bases = {"boleto": (raiz / "boletos_sinteticos", "imagens", "boletos",
                        lambda b: b / "gabarito.json")}
    for tipo in ("nfe", "nfce", "nfse", "recibo"):
        bases[tipo] = (raiz / "documentos_sinteticos", tipo, "documentos",
                       lambda b, t=tipo: b / t / "gabarito.json")
    meta_docs = json.loads((raiz / "documentos_sinteticos/imagens/metadados.json")
                           .read_text(encoding="utf-8"))
    meta_bol = json.loads((raiz / "boletos_sinteticos/imagens/metadados.json")
                          .read_text(encoding="utf-8"))
    itens = {}
    for tipo, (base, chave_meta, chave_gab, caminho_gab) in bases.items():
        gabarito = json.loads(caminho_gab(base).read_text(encoding="utf-8"))
        por_id = {doc["id"]: doc for doc in gabarito[chave_gab]}
        metas = meta_bol["imagens"] if tipo == "boleto" else meta_docs[chave_meta]
        for meta in metas:
            for variante in VARIANTES:
                arquivo = base / meta[variante]
                itens[f"{tipo}/{variante}/{meta['id']}"] = {
                    "tipo": tipo, "variante": variante, "id": meta["id"],
                    "arquivo": arquivo, "gabarito": por_id[meta["id"]],
                    "degradacao": meta.get("foto_degradacao") if variante == "foto" else None,
                }
    return itens


def ler_resultados(caminho: Path):
    resultados = {}
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                registro = json.loads(linha)
                resultados[registro["chave"]] = registro
    return resultados


def coletar(args):
    itens = carregar_dataset(args.dataset)
    if args.limite:
        itens = dict(list(itens.items())[: args.limite])
    args.saida.mkdir(parents=True, exist_ok=True)
    jsonl = args.saida / "ocr.jsonl"
    feitos = set(ler_resultados(jsonl))
    pendentes = [c for c in itens if c not in feitos]
    print(f"{len(itens)} imagens, {len(feitos & set(itens))} já processadas, "
          f"{len(pendentes)} pendentes. Gravando em {jsonl}", flush=True)
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
                lista = [{"chave": c, "nome": c.replace("/", "_") + itens[c]["arquivo"].suffix}
                         for c in pendentes]
                return self._responder(json.dumps(lista).encode())
            if url.path == "/img":
                chave = parse_qs(url.query).get("chave", [""])[0]
                if chave not in itens:
                    return self._responder(b"{}", status=404)
                return self._responder(itens[chave]["arquivo"].read_bytes(),
                                       "application/octet-stream")
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


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


def digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def pegar(doc, caminho):
    for parte in caminho.split("."):
        if doc is None:
            return None
        doc = doc.get(parte)
    return doc


def formatar_dinheiro(valor: float) -> list[str]:
    inteiro, centavos = f"{valor:.2f}".split(".")
    com_milhar = f"{int(inteiro):,}".replace(",", ".")
    return list(dict.fromkeys([f"{com_milhar},{centavos}", f"{inteiro},{centavos}"]))


def esperados(valor, formato) -> list[str]:
    if formato == "dinheiro":
        return formatar_dinheiro(float(valor))
    if formato == "numero_nf":
        n = f"{int(valor):09d}"
        return [f"{n[:3]}.{n[3:6]}.{n[6:]}", str(int(valor))]
    if formato == "data":
        ano, mes, dia = str(valor).split("-")
        return [f"{dia}/{mes}/{ano}"]
    if formato == "digitos":
        return [digitos(str(valor))]
    return [normalizar(str(valor))]


def contem(texto: str, alvo: str) -> bool:
    return re.search(r"(?<![\w,.])" + re.escape(alvo) + r"(?![\w]|[,.]\d)", texto) is not None


def menor_distancia(alvo: str, texto: str) -> int:
    anterior = [0] * (len(texto) + 1)
    for i, ca in enumerate(alvo, 1):
        atual = [i] + [0] * len(texto)
        for j, ct in enumerate(texto, 1):
            atual[j] = min(anterior[j] + 1, atual[j - 1] + 1,
                           anterior[j - 1] + (ca != ct))
        anterior = atual
    return min(anterior)


def avaliar_campo(valor, formato, texto_norm, texto_dig):
    alvos = esperados(valor, formato)
    if formato == "digitos":
        if any(a and a in texto_dig for a in alvos):
            return "exato", 0
        base = texto_dig
    else:
        if any(contem(texto_norm, a) for a in alvos):
            return "exato", 0
        base = texto_norm
    if not base:
        return "perdido", None
    dist = min(menor_distancia(a, base) for a in alvos)
    return ("quase" if dist <= MAX_EDICOES_QUASE else "perdido"), dist


def pct(parte, total):
    return f"{100 * parte / total:.1f}%" if total else "-"


def media(valores, fmt="{:.0f}"):
    valores = [v for v in valores if v is not None]
    return fmt.format(statistics.mean(valores)) if valores else "-"


def tabela_md(cabecalho, linhas):
    saida = ["| " + " | ".join(cabecalho) + " |",
             "|" + "|".join("---" if i == 0 else "---:" for i in range(len(cabecalho))) + "|"]
    saida += ["| " + " | ".join(str(c) for c in linha) + " |" for linha in linhas]
    return "\n".join(saida)


def relatorio(args):
    itens = carregar_dataset(args.dataset)
    resultados = ler_resultados(args.saida / "ocr.jsonl")
    if not resultados:
        sys.exit(f"Nenhum resultado em {args.saida / 'ocr.jsonl'}. Rode a coleta antes.")

    detalhes, por_imagem = [], []
    for chave, item in itens.items():
        registro = resultados.get(chave)
        if registro is None:
            continue
        ocr = registro.get("ocr") or {}
        texto = ocr.get("full_text") or ""
        texto_norm, texto_dig = normalizar(texto), digitos(texto)
        confs = [linha["confidence"] for bloco in ocr.get("blocks", [])
                 for linha in bloco.get("lines") or [] if linha.get("confidence") is not None]
        contagem = defaultdict(int)
        for nome, caminho, formato in CAMPOS[item["tipo"]]:
            valor = pegar(item["gabarito"], caminho)
            if valor is None:
                continue
            status, dist = avaliar_campo(valor, formato, texto_norm, texto_dig)
            contagem[status] += 1
            detalhes.append({"chave": chave, "tipo": item["tipo"], "variante": item["variante"],
                             "id": item["id"], "campo": nome, "esperado": valor,
                             "status": status, "distancia": "" if dist is None else dist})
        total = sum(contagem.values())
        por_imagem.append({"chave": chave, **{k: item[k] for k in ("tipo", "variante", "id")},
                           "campos": total, "exato": contagem["exato"], "quase": contagem["quase"],
                           "perdido": contagem["perdido"], "acerto": contagem["exato"] / total,
                           "ms": registro.get("ms"), "erro": registro.get("erro"),
                           "vazio": not texto.strip(),
                           "conf_media": statistics.mean(confs) if confs else None,
                           "degradacao": item["degradacao"]})

    grupos = defaultdict(list)
    for img in por_imagem:
        grupos[(img["tipo"], img["variante"])].append(img)
        grupos[("TOTAL", img["variante"])].append(img)
    linhas_resumo = []
    for tipo in (*TIPOS, "TOTAL"):
        for variante in VARIANTES:
            imgs = grupos.get((tipo, variante), [])
            if not imgs:
                continue
            campos = sum(i["campos"] for i in imgs)
            linhas_resumo.append([
                f"**{tipo}**" if tipo == "TOTAL" else tipo, variante, len(imgs), campos,
                pct(sum(i["exato"] for i in imgs), campos),
                pct(sum(i["quase"] for i in imgs), campos),
                pct(sum(i["perdido"] for i in imgs), campos),
                sum(1 for i in imgs if i["exato"] == i["campos"]),
                sum(1 for i in imgs if i["vazio"] or i["erro"]),
                media([i["conf_media"] for i in imgs], "{:.3f}"),
                media([i["ms"] for i in imgs]),
            ])
    cab_resumo = ["Tipo", "Variante", "Imagens", "Campos", "Exato", "Quase (≤2)", "Perdido",
                  "Imagens 100%", "Vazias/erro", "Confiança média", "ms/imagem"]

    por_campo = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    for d in detalhes:
        contador = por_campo[(d["tipo"], d["campo"])][d["variante"]]
        contador[0] += d["status"] == "exato"
        contador[1] += d["status"] == "quase"
        contador[2] += 1
    linhas_campo = []
    for tipo in TIPOS:
        for nome, _, _ in CAMPOS[tipo]:
            if (tipo, nome) not in por_campo:
                continue
            c = por_campo[(tipo, nome)]
            linha = [tipo, nome]
            for variante in VARIANTES:
                e, q, t = c[variante]
                linha += [pct(e, t), pct(q, t)]
            linhas_campo.append(linha)
    cab_campo = ["Tipo", "Campo", "PNG exato", "PNG quase", "Foto exato", "Foto quase"]

    piores = sorted(por_imagem, key=lambda i: (i["acerto"], i["chave"]))[: args.piores]
    linhas_piores = []
    for i in piores:
        deg = i["degradacao"] or {}
        linhas_piores.append([
            i["chave"], f"{i['exato']}/{i['campos']}", media([i["conf_media"]], "{:.3f}"),
            deg.get("rotacao_graus", "-"), deg.get("desfoque_raio", "-"),
            deg.get("ruido_sigma", "-"), deg.get("qualidade_jpeg", "-"),
            "erro" if i["erro"] else ("vazio" if i["vazio"] else ""),
        ])
    cab_piores = ["Imagem", "Campos exatos", "Confiança média", "Rotação (°)", "Desfoque",
                  "Ruído", "JPEG", "Obs."]

    faltando = len(itens) - len(por_imagem)
    md = [
        "# Benchmark do OCR (ML Kit) no dataset sintético",
        "",
        f"Gerado em {datetime.now():%Y-%m-%d %H:%M}. Imagens avaliadas: {len(por_imagem)}"
        + (f" ({faltando} sem resultado de OCR)." if faltando else "."),
        "",
        "Métrica por campo: **exato** = o valor do gabarito aparece no texto do OCR "
        "(sem diferença de caixa/acentos/espaços; só dígitos para CPF, CNPJ, chave, "
        f"linha digitável e nosso número); **quase** = há um trecho a até {MAX_EDICOES_QUASE} "
        "edições; **perdido** = nenhum dos dois. *png* é a imagem limpa e *foto* a versão "
        "degradada (rotação, perspectiva, ruído, desfoque, JPEG).",
        "",
        "## Resumo por tipo",
        "",
        tabela_md(cab_resumo, linhas_resumo),
        "",
        "## Acerto por campo",
        "",
        tabela_md(cab_campo, linhas_campo),
        "",
        f"## {len(piores)} piores imagens",
        "",
        tabela_md(cab_piores, linhas_piores),
        "",
    ]
    (args.saida / "relatorio.md").write_text("\n".join(md), encoding="utf-8")
    with (args.saida / "detalhes.csv").open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(detalhes[0]))
        escritor.writeheader()
        escritor.writerows(detalhes)

    print(tabela_md(cab_resumo, linhas_resumo))
    print(f"\nRelatório: {args.saida / 'relatorio.md'}")
    print(f"Detalhes:  {args.saida / 'detalhes.csv'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("passo", choices=["coletar", "relatorio"])
    parser.add_argument("--dataset", type=Path, default=DATASET_PADRAO,
                        help=f"pasta com boletos_sinteticos/ e documentos_sinteticos/ "
                             f"(padrão: {DATASET_PADRAO})")
    parser.add_argument("--saida", type=Path,
                        default=RAIZ_REPO / "resultados" / "experimento1_sintetico",
                        help="pasta do ocr.jsonl e do relatório")
    parser.add_argument("--porta", type=int, default=8765)
    parser.add_argument("--limite", type=int, default=0,
                        help="coletar só as N primeiras imagens (teste rápido)")
    parser.add_argument("--piores", type=int, default=15)
    args = parser.parse_args()
    coletar(args) if args.passo == "coletar" else relatorio(args)


if __name__ == "__main__":
    main()
