"""Gera recibos sintéticos (HTML, três estilos) com lançamento contábil e o gabarito.

Uso (em dados/sinteticos/documentos_sinteticos):
  python3 ../../../scripts/geradores/documentos/gerar_recibos.py . [--quantidade 50] [--semente 42]
Requer num2words.
"""
import argparse
import json
import sys
from html import escape
from pathlib import Path

from num2words import num2words

sys.path.insert(0, str(Path(__file__).parent))
from comum import Gerador, data_extenso, dinheiro  # noqa: E402

# (histórico, conta débito, faixa de valor, recebedor é empresa?)
OPERACOES = [
    ("Pagamento de aluguel do imóvel comercial referente a {mes}", ("4.1.2.01", "Aluguéis e Condomínios"), (1200, 9500), False),
    ("Pagamento de honorários contábeis referente a {mes}", ("4.1.2.05", "Serviços Profissionais - PJ"), (450, 3500), True),
    ("Pagamento de serviço de manutenção de ar-condicionado", ("4.1.2.08", "Manutenção e Reparos"), (180, 2400), True),
    ("Pagamento de frete de mercadorias - NF {nf}", ("4.1.3.02", "Fretes e Carretos"), (90, 1800), True),
    ("Adiantamento salarial referente a {mes}", ("1.1.3.01", "Adiantamentos a Empregados"), (300, 2500), False),
    ("Pagamento de serviço de limpeza e conservação referente a {mes}", ("4.1.2.06", "Serviços de Limpeza"), (350, 4200), True),
    ("Pagamento de diária de serviços de pintura", ("4.1.2.08", "Manutenção e Reparos"), (150, 900), False),
    ("Compra de material de escritório", ("4.1.2.10", "Material de Expediente"), (40, 850), True),
    ("Pagamento de serviço de desenvolvimento de website", ("4.1.2.04", "Serviços Profissionais - PF"), (800, 7000), False),
    ("Reembolso de despesas de viagem a serviço", ("4.1.2.12", "Viagens e Representações"), (120, 2200), False),
    ("Pagamento de consultoria em segurança do trabalho", ("4.1.2.05", "Serviços Profissionais - PJ"), (600, 5000), True),
    ("Pagamento de serviço de chaveiro e troca de fechaduras", ("4.1.2.08", "Manutenção e Reparos"), (80, 650), False),
    ("Pagamento de aula de treinamento para equipe de vendas", ("4.1.2.11", "Treinamentos"), (500, 4500), False),
    ("Pagamento de serviço de dedetização", ("4.1.2.06", "Serviços de Limpeza"), (180, 1500), True),
]
BANCOS = [("001", "Banco do Brasil"), ("237", "Bradesco"), ("341", "Itaú"), ("104", "Caixa"),
          ("033", "Santander"), ("756", "Sicoob")]
FORMAS = ["Dinheiro", "PIX", "Transferência bancária (TED)", "Cheque", "Cartão de débito"]

CSS = """
* { box-sizing: border-box; }
body { margin: 0; padding: 24px; background: #fff; color: #111; }
.recibo { width: 746px; margin: 0 auto; position: relative; }
.linha { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; }
.extenso { font-style: italic; }
.assinatura { margin-top: 46px; text-align: center; }
.assinatura .traco { border-top: 1px solid #111; width: 360px; margin: 0 auto 4px; }
.contabil table { width: 100%; border-collapse: collapse; }
.contabil td, .contabil th { border: 1px solid #555; padding: 5px 8px; text-align: left; font-size: 12.5px; }
.contabil th { background: #eee; width: 26%; }
.aviso { font-size: 9px; color: #777; text-align: center; margin-top: 10px; }

/* estilo clássico */
.classico { font-family: Georgia, 'DejaVu Serif', serif; border: 3px double #222; padding: 26px 30px; }
.classico h1 { font-size: 30px; letter-spacing: 6px; margin: 0; }
.classico .valor { border: 2px solid #222; padding: 6px 14px; font-size: 20px; font-weight: bold; }
.classico .corpo { font-size: 15.5px; line-height: 1.9; margin: 22px 0; text-align: justify; }

/* estilo moderno */
.moderno { font-family: 'Helvetica Neue', Arial, 'Liberation Sans', sans-serif; border: 1px solid #c8c8c8; }
.moderno .topo { background: #1f3b5a; color: #fff; padding: 16px 26px; }
.moderno h1 { font-size: 24px; margin: 0; font-weight: 600; }
.moderno .valor { background: #fff; color: #1f3b5a; padding: 6px 12px; font-size: 20px; font-weight: 700; border-radius: 4px; }
.moderno .miolo { padding: 18px 26px 22px; }
.moderno .corpo { font-size: 14.5px; line-height: 1.75; margin: 4px 0 18px; }
.moderno .contabil th { background: #e7eef6; }

/* estilo talão (formulário pré-impresso) */
.talao { font-family: 'Courier New', 'Liberation Mono', monospace; border: 2px solid #333; padding: 18px 22px; background: #fbfaf3; }
.talao h1 { font-family: Arial, 'Liberation Sans', sans-serif; font-size: 26px; margin: 0; }
.talao .valor { font-size: 19px; font-weight: bold; border-bottom: 2px solid #333; padding: 0 8px; }
.talao .campo { border-bottom: 1px dotted #555; padding: 7px 0 3px; font-size: 14px; }
.talao .campo b { font-family: Arial, 'Liberation Sans', sans-serif; font-size: 11px; text-transform: uppercase; color: #444; margin-right: 8px; }
.talao .contabil { margin-top: 12px; }
"""


def conta_credito(g: Gerador, forma: str, banco, conta_banco: str):
    if forma == "Dinheiro":
        return ("1.1.1.01", "Caixa Geral")
    cod, nome = banco
    return (f"1.1.1.02.00{BANCOS.index(banco) + 1}", f"{nome} - C/C {conta_banco}")


def bloco_contabil(dados) -> str:
    return f"""<div class="contabil"><table>
<tr><th>Conta débito</th><td>{escape(dados['conta_debito']['codigo'])} - {escape(dados['conta_debito']['nome'])}</td></tr>
<tr><th>Conta crédito</th><td>{escape(dados['conta_credito']['codigo'])} - {escape(dados['conta_credito']['nome'])}</td></tr>
<tr><th>Histórico</th><td>{escape(dados['historico'])}</td></tr>
<tr><th>Forma de pagamento</th><td>{escape(dados['forma_pagamento_detalhe'])}</td></tr>
</table></div>"""


def html_recibo(d, estilo: str) -> str:
    pag, rec = d["pagador"], d["recebedor"]
    texto = (f"Recebi(emos) de <b>{escape(pag['nome'])}</b>, inscrito(a) no {pag['tipo_documento']} sob o nº "
             f"<b>{pag['documento']}</b>, a importância de <b>R$ {d['valor_formatado']}</b> "
             f"<span class=\"extenso\">({escape(d['valor_extenso'])})</span>, referente a "
             f"{escape(d['historico'][0].lower() + d['historico'][1:])}.")
    local_data = f"{escape(d['cidade'])}, {d['data_extenso']}."
    assinatura = (f"<div class=\"assinatura\"><div class=\"traco\"></div>{escape(rec['nome'])}<br>"
                  f"{rec['tipo_documento']}: {rec['documento']}</div>")
    aviso = '<div class="aviso">Documento fictício gerado para pesquisa acadêmica (TCC).</div>'

    if estilo == "classico":
        corpo = f"""<div class="recibo classico">
<div class="linha"><h1>RECIBO</h1><span>Nº {d['numero']}</span><span class="valor">R$ {d['valor_formatado']}</span></div>
<p class="corpo">{texto}</p>
<p>Data do pagamento: <b>{d['data_formatada']}</b></p>
{bloco_contabil(d)}
<p style="text-align:right;margin-top:22px">{local_data}</p>{assinatura}{aviso}</div>"""
    elif estilo == "moderno":
        corpo = f"""<div class="recibo moderno">
<div class="topo linha"><div><h1>Recibo de Pagamento</h1><small>Nº {d['numero']} &nbsp;·&nbsp; Data: {d['data_formatada']}</small></div>
<span class="valor">R$ {d['valor_formatado']}</span></div>
<div class="miolo"><p class="corpo">{texto}</p>{bloco_contabil(d)}
<p style="margin-top:18px">{local_data}</p>{assinatura}{aviso}</div></div>"""
    else:
        corpo = f"""<div class="recibo talao">
<div class="linha"><h1>RECIBO</h1><span>Nº {d['numero']}</span><span>VALOR <span class="valor">R$ {d['valor_formatado']}</span></span></div>
<div class="campo"><b>Recebi(emos) de</b>{escape(pag['nome'])} &nbsp; {pag['tipo_documento']}: {pag['documento']}</div>
<div class="campo"><b>A quantia de</b>{escape(d['valor_extenso'])}</div>
<div class="campo"><b>Referente a</b>{escape(d['historico'])}</div>
<div class="campo"><b>Data</b>{d['data_formatada']}</div>
{bloco_contabil(d)}
<p style="margin-top:16px">{local_data}</p>{assinatura}{aviso}</div>"""
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Recibo {d["numero"]}</title>'
            f"<style>{CSS}</style></head><body>{corpo}</body></html>")


def gerar_recibo(g: Gerador):
    historico_tpl, debito, (vmin, vmax), recebedor_empresa = g.escolher(OPERACOES)
    pagador = g.empresa()
    recebedor = g.empresa() if recebedor_empresa else g.pessoa_fisica()
    dh = g.data_hora()
    valor = round(g.rng.uniform(vmin, vmax), 2)
    if g.rng.random() < 0.3:
        valor = float(round(valor, -1))

    forma = g.escolher(FORMAS)
    banco = g.escolher(BANCOS)
    conta_banco = f"{g.rng.randint(10000, 99999)}-{g.rng.randint(0, 9)}"
    credito = conta_credito(g, forma, banco, conta_banco)
    detalhe = forma
    if forma == "Cheque":
        detalhe = f"Cheque nº {g.rng.randint(100000, 999999)} - {banco[1]}"
    elif forma in ("PIX", "Transferência bancária (TED)"):
        detalhe = f"{forma} - {banco[1]}"

    historico = historico_tpl.format(mes=f"{dh:%m/%Y}", nf=g.rng.randint(1000, 99999))
    return {
        "numero": f"{g.rng.randint(1, 9999):04d}",
        "data": dh.date().isoformat(),
        "data_formatada": dh.strftime("%d/%m/%Y"),
        "data_extenso": data_extenso(dh),
        "cidade": pagador.endereco.cidade,
        "valor": valor,
        "valor_formatado": dinheiro(valor),
        "valor_extenso": num2words(valor, lang="pt_BR", to="currency"),
        "conta_debito": {"codigo": debito[0], "nome": debito[1]},
        "conta_credito": {"codigo": credito[0], "nome": credito[1]},
        "historico": historico,
        "forma_pagamento": forma,
        "forma_pagamento_detalhe": detalhe,
        "pagador": pagador.gabarito(),
        "recebedor": recebedor.gabarito(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", type=Path)
    ap.add_argument("--quantidade", type=int, default=50)
    ap.add_argument("--semente", type=int, default=42)
    args = ap.parse_args()

    g = Gerador(args.semente + 4000)
    pasta = args.base / "recibo"
    (pasta / "html").mkdir(parents=True, exist_ok=True)
    estilos = ["classico", "moderno", "talao"]
    docs = []
    for i in range(1, args.quantidade + 1):
        doc_id = f"recibo_{i:03d}"
        dados = gerar_recibo(g)
        estilo = estilos[(i - 1) % len(estilos)]
        (pasta / "html" / f"{doc_id}.html").write_text(html_recibo(dados, estilo), encoding="utf-8")
        docs.append({"id": doc_id, "arquivo_html": f"html/{doc_id}.html", "estilo": estilo, **dados})
    (pasta / "gabarito.json").write_text(json.dumps({
        "descricao": "Recibos de pagamento sintéticos (dados fictícios) para teste de OCR/PLN",
        "semente": args.semente, "quantidade": len(docs), "documentos": docs,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"recibo: {len(docs)} documentos em {pasta}")


if __name__ == "__main__":
    main()
