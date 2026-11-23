"""Gera NF-e, NFC-e e NFS-e sintéticas (XML + PDF) e o gabarito de cada tipo.

As notas não são assinadas nem autorizadas; o PDF identifica o documento como sintético.

Uso (em dados/sinteticos/documentos_sinteticos):
  python3 ../../../scripts/geradores/documentos/gerar_notas.py . [--quantidade 50] [--semente 42] [--tipos nfe nfce nfse]
Requer brazilfiscalreport.
"""
import argparse
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).parent))
from comum import (CIDADES, SERVICOS_EMPRESA, Gerador, Pessoa, data_extenso,  # noqa: E402
                   dinheiro, dv_mod11_chave)

AVISO = "DOCUMENTO FICTICIO GERADO PARA PESQUISA ACADEMICA (TCC) - SEM VALOR FISCAL"

PRODUTOS_NFE = [
    ("Resma papel A4 75g 500 folhas", "48025610", "CX", 22.0, 38.0),
    ("Cimento CP-II 50kg", "25232910", "SC", 32.0, 45.0),
    ("Cabo flexível 2,5mm 100m", "85444900", "RL", 180.0, 320.0),
    ("Tinta acrílica fosca 18L branca", "32091010", "LT", 210.0, 420.0),
    ("Notebook 15,6 pol 16GB 512GB SSD", "84713012", "UN", 2800.0, 5200.0),
    ("Monitor LED 24 pol Full HD", "85285200", "UN", 650.0, 1200.0),
    ("Cadeira de escritório ergonômica", "94013090", "UN", 450.0, 1300.0),
    ("Óleo lubrificante 5W30 1L", "27101932", "UN", 28.0, 55.0),
    ("Pneu aro 15 195/60", "40111000", "UN", 320.0, 610.0),
    ("Fertilizante NPK 10-10-10 50kg", "31052000", "SC", 140.0, 260.0),
    ("Ração bovina 40kg", "23099090", "SC", 85.0, 160.0),
    ("Torneira metálica cozinha", "84818019", "UN", 75.0, 230.0),
    ("Lâmpada LED 9W bivolt", "85395000", "UN", 6.0, 15.0),
    ("Caixa organizadora plástica 50L", "39241000", "UN", 35.0, 80.0),
    ("Detergente neutro 5L", "34022000", "GL", 18.0, 35.0),
]
PRODUTOS_NFCE = [
    ("ARROZ TIPO 1 5KG", "10063021", "UN", 22.0, 34.0), ("FEIJAO CARIOCA 1KG", "07133399", "UN", 6.5, 11.0),
    ("ACUCAR CRISTAL 5KG", "17019900", "UN", 17.0, 26.0), ("CAFE TORRADO 500G", "09012100", "UN", 14.0, 29.0),
    ("LEITE INTEGRAL 1L", "04012010", "UN", 4.2, 7.5), ("OLEO DE SOJA 900ML", "15079011", "UN", 6.0, 10.0),
    ("MACARRAO ESPAGUETE 500G", "19021900", "UN", 3.5, 7.0), ("PAO DE FORMA 500G", "19059010", "UN", 7.0, 12.0),
    ("BANANA PRATA KG", "08039000", "KG", 4.0, 8.0), ("TOMATE KG", "07020000", "KG", 5.0, 11.0),
    ("FRANGO CONGELADO KG", "02071200", "KG", 9.0, 16.0), ("CARNE MOIDA KG", "02013000", "KG", 28.0, 45.0),
    ("SABAO EM PO 1KG", "34022000", "UN", 9.0, 19.0), ("PAPEL HIGIENICO 12 ROLOS", "48181000", "UN", 15.0, 28.0),
    ("REFRIGERANTE 2L", "22021000", "UN", 6.0, 11.0), ("CERVEJA LATA 350ML", "22030000", "UN", 3.0, 5.5),
    ("SABONETE 90G", "34011190", "UN", 1.8, 4.5), ("CREME DENTAL 90G", "33061000", "UN", 3.5, 9.0),
    ("IOGURTE NATURAL 170G", "04031000", "UN", 2.5, 5.0), ("QUEIJO MUSSARELA KG", "04061010", "KG", 35.0, 58.0),
]
FORMAS_PAG = [("01", "Dinheiro"), ("03", "Cartão de Crédito"), ("04", "Cartão de Débito"),
              ("15", "Boleto Bancário"), ("17", "PIX")]


def x(v) -> str:
    return escape(str(v))


def tag_documento(p: Pessoa) -> str:
    return f"<CNPJ>{p.documento}</CNPJ>" if p.eh_cnpj else f"<CPF>{p.documento}</CPF>"


def endereco_nfe(p: Pessoa, tag: str) -> str:
    e = p.endereco
    return (f"<{tag}><xLgr>{x(e.logradouro)}</xLgr><nro>{e.numero}</nro><xBairro>{x(e.bairro)}</xBairro>"
            f"<cMun>{e.cod_municipio}</cMun><xMun>{x(e.cidade)}</xMun><UF>{e.uf}</UF><CEP>{e.cep}</CEP>"
            f"<cPais>1058</cPais><xPais>Brasil</xPais><fone>{p.fone}</fone></{tag}>")


def montar_itens(g: Gerador, catalogo, qtd_itens, aliq_icms):
    dets, itens, total = [], [], 0.0
    for n, (desc, ncm, un, pmin, pmax) in enumerate(g.rng.sample(catalogo, qtd_itens), start=1):
        if un == "KG":
            qtd = round(g.rng.uniform(0.3, 3.0), 3)
        else:
            qtd = g.rng.randint(1, 4 if pmax < 100 else 3) * (g.rng.choice([1, 1, 1, 2, 3]) if pmax < 60 else 1)
        vun = round(g.rng.uniform(pmin, pmax), 2)
        vprod = round(qtd * vun, 2)
        total += vprod
        cprod = f"{g.rng.randint(1000, 99999):05d}"
        vicms = round(vprod * aliq_icms / 100, 2)
        icms = (f"<ICMS00><orig>0</orig><CST>00</CST><modBC>3</modBC><vBC>{vprod:.2f}</vBC>"
                f"<pICMS>{aliq_icms:.4f}</pICMS><vICMS>{vicms:.2f}</vICMS></ICMS00>")
        dets.append(
            f'<det nItem="{n}"><prod><cProd>{cprod}</cProd><cEAN>SEM GTIN</cEAN><xProd>{x(desc)}</xProd>'
            f"<NCM>{ncm}</NCM><CFOP>5102</CFOP><uCom>{un}</uCom><qCom>{qtd:.4f}</qCom>"
            f"<vUnCom>{vun:.10f}</vUnCom><vProd>{vprod:.2f}</vProd><cEANTrib>SEM GTIN</cEANTrib>"
            f"<uTrib>{un}</uTrib><qTrib>{qtd:.4f}</qTrib><vUnTrib>{vun:.10f}</vUnTrib><indTot>1</indTot></prod>"
            f"<imposto><vTotTrib>{round(vprod * 0.25, 2):.2f}</vTotTrib><ICMS>{icms}</ICMS>"
            f"<PIS><PISAliq><CST>01</CST><vBC>{vprod:.2f}</vBC><pPIS>0.6500</pPIS>"
            f"<vPIS>{round(vprod * 0.0065, 2):.2f}</vPIS></PISAliq></PIS>"
            f"<COFINS><COFINSAliq><CST>01</CST><vBC>{vprod:.2f}</vBC><pCOFINS>3.0000</pCOFINS>"
            f"<vCOFINS>{round(vprod * 0.03, 2):.2f}</vCOFINS></COFINSAliq></COFINS></imposto></det>")
        itens.append({"descricao": desc, "quantidade": qtd, "unidade": un, "valor_unitario": vun,
                      "valor_total": vprod})
    return "".join(dets), itens, round(total, 2), round(total * aliq_icms / 100, 2)


def chave_acesso(emit: Pessoa, dh, modelo: int, serie: int, numero: int, cnf: str) -> str:
    base = (f"{emit.endereco.cod_uf}{dh:%y%m}{emit.documento}{modelo:02d}{serie:03d}{numero:09d}1{cnf}")
    return base + str(dv_mod11_chave(base))


def gerar_nfe_ou_nfce(g: Gerador, modelo: int):
    eh_nfce = modelo == 65
    emit = g.empresa()
    if eh_nfce:
        r = g.rng.random()
        dest = (g.pessoa_fisica(next(c for c in CIDADES if c[0] == emit.endereco.cidade)) if r < 0.75 else None)
        dest_sem_nome = dest is not None and r >= 0.5
    else:
        dest = g.pessoa_ou_empresa(prob_empresa=0.6)
        dest_sem_nome = False

    dh = g.data_hora()
    serie = g.rng.randint(1, 3)
    numero = g.rng.randint(1, 250000)
    cnf = g.digitos(8)
    chave = chave_acesso(emit, dh, modelo, serie, numero, cnf)

    catalogo = PRODUTOS_NFCE if eh_nfce else PRODUTOS_NFE
    qtd_itens = g.rng.randint(2, 12) if eh_nfce else g.rng.randint(1, 6)
    dets, itens, v_prod, v_icms = montar_itens(g, catalogo, qtd_itens, 18.0 if not eh_nfce else 17.0)
    v_frete = 0.0 if eh_nfce or g.rng.random() < 0.6 else round(g.rng.uniform(25, 180), 2)
    v_desc = round(v_prod * g.rng.choice([0, 0, 0, 0.03, 0.05, 0.10]), 2)
    v_nf = round(v_prod + v_frete - v_desc, 2)
    tpag, forma = g.escolher(FORMAS_PAG[:3] + FORMAS_PAG[4:] if eh_nfce else FORMAS_PAG)
    v_pago = v_nf
    troco = 0.0
    if tpag == "01":
        v_pago = float(int(v_nf // 10 + 1) * 10) if g.rng.random() < 0.7 else v_nf
        troco = round(v_pago - v_nf, 2)

    dh_iso = dh.isoformat(timespec="seconds")
    dest_xml = ""
    if dest is not None:
        nome = "" if dest_sem_nome else f"<xNome>{x(dest.nome)}</xNome>"
        ender = "" if eh_nfce else endereco_nfe(dest, "enderDest")
        ind_ie = f"<indIEDest>1</indIEDest><IE>{dest.ie}</IE>" if dest.eh_cnpj else "<indIEDest>9</indIEDest>"
        dest_xml = f"<dest>{tag_documento(dest)}{nome}{ender}{ind_ie}</dest>"

    supl = ""
    if eh_nfce:
        url = f"https://www.sefaz.{emit.endereco.uf.lower()}.gov.br/nfce/qrcode"
        supl = (f"<infNFeSupl><qrCode><![CDATA[{url}?p={chave}|2|1|1|{g.digitos(40)}]]></qrCode>"
                f"<urlChave>www.sefaz.{emit.endereco.uf.lower()}.gov.br/nfce/consulta</urlChave></infNFeSupl>")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe versao="4.00" Id="NFe{chave}">
<ide><cUF>{emit.endereco.cod_uf}</cUF><cNF>{cnf}</cNF><natOp>Venda de mercadoria</natOp><mod>{modelo}</mod>
<serie>{serie}</serie><nNF>{numero}</nNF><dhEmi>{dh_iso}</dhEmi>{'' if eh_nfce else f'<dhSaiEnt>{dh_iso}</dhSaiEnt>'}
<tpNF>1</tpNF><idDest>1</idDest><cMunFG>{emit.endereco.cod_municipio}</cMunFG><tpImp>{4 if eh_nfce else 1}</tpImp>
<tpEmis>1</tpEmis><cDV>{chave[-1]}</cDV><tpAmb>1</tpAmb><finNFe>1</finNFe><indFinal>1</indFinal>
<indPres>1</indPres><procEmi>0</procEmi><verProc>GeradorSintetico 1.0</verProc></ide>
<emit>{tag_documento(emit)}<xNome>{x(emit.nome)}</xNome><xFant>{x(emit.nome.rsplit(' ', 1)[0])}</xFant>
{endereco_nfe(emit, 'enderEmit')}<IE>{emit.ie}</IE><CRT>3</CRT></emit>
{dest_xml}{dets}
<total><ICMSTot><vBC>{v_prod:.2f}</vBC><vICMS>{v_icms:.2f}</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP>
<vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet><vProd>{v_prod:.2f}</vProd>
<vFrete>{v_frete:.2f}</vFrete><vSeg>0.00</vSeg><vDesc>{v_desc:.2f}</vDesc><vII>0.00</vII><vIPI>0.00</vIPI>
<vIPIDevol>0.00</vIPIDevol><vPIS>{round(v_prod * 0.0065, 2):.2f}</vPIS><vCOFINS>{round(v_prod * 0.03, 2):.2f}</vCOFINS>
<vOutro>0.00</vOutro><vNF>{v_nf:.2f}</vNF><vTotTrib>{round(v_prod * 0.25, 2):.2f}</vTotTrib></ICMSTot></total>
<transp><modFrete>{9 if v_frete == 0 else 0}</modFrete></transp>
<pag><detPag><indPag>0</indPag><tPag>{tpag}</tPag><vPag>{v_pago:.2f}</vPag></detPag>{f'<vTroco>{troco:.2f}</vTroco>' if eh_nfce else ''}</pag>
<infAdic><infCpl>{AVISO}</infCpl></infAdic>
</infNFe>{supl}</NFe>
<protNFe versao="4.00"><infProt><tpAmb>1</tpAmb><verAplic>SINTETICO</verAplic><chNFe>{chave}</chNFe>
<dhRecbto>{dh_iso}</dhRecbto><nProt>{emit.endereco.cod_uf}{g.digitos(13)}</nProt><digVal>AAAA</digVal>
<cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe></nfeProc>
"""
    gab = {
        "modelo": modelo,
        "emitente": emit.gabarito(),
        "destinatario": None if dest is None else {**dest.gabarito(), **({"nome": None} if dest_sem_nome else {})},
        "numero": numero,
        "numero_formatado": f"{numero:09d}"[:3] + "." + f"{numero:09d}"[3:6] + "." + f"{numero:09d}"[6:],
        "serie": serie,
        "chave_acesso": chave,
        "chave_acesso_formatada": " ".join(chave[i:i + 4] for i in range(0, 44, 4)),
        "data_emissao": dh.date().isoformat(),
        "data_emissao_formatada": dh.strftime("%d/%m/%Y"),
        "hora_emissao": dh.strftime("%H:%M:%S"),
        "valor_produtos": v_prod,
        "valor_frete": v_frete,
        "valor_desconto": v_desc,
        "valor_total": v_nf,
        "valor_total_formatado": dinheiro(v_nf),
        "forma_pagamento": forma,
        "itens": itens,
    }
    if eh_nfce:
        gab["valor_pago"] = v_pago
        gab["troco"] = troco
    return xml, gab


def gerar_nfse(g: Gerador):
    nucleo, item_lista, ctrib, desc_serv = g.escolher(SERVICOS_EMPRESA)
    cidade = g.escolher(CIDADES)
    prest = g.empresa(cidade, nucleo_servico=nucleo)
    toma = g.pessoa_ou_empresa(prob_empresa=0.65)

    dh = g.data_hora()
    numero = g.rng.randint(1, 99999)
    n_dps = g.rng.randint(1, 99999)
    v_serv = round(g.rng.uniform(150, 25000), 2)
    aliq = g.escolher([2.0, 2.5, 3.0, 5.0])
    v_iss = round(v_serv * aliq / 100, 2)
    reter_federais = toma.eh_cnpj and v_serv > 5000 and g.rng.random() < 0.5
    v_irrf = round(v_serv * 0.015, 2) if reter_federais else 0.0
    v_csll = round(v_serv * 0.0465, 2) if reter_federais else 0.0
    v_ret = round(v_irrf + v_csll, 2)
    v_liq = round(v_serv - v_ret, 2)
    descricao = f"{desc_serv} - competência {dh:%m/%Y}"

    id_nfse = ("NFS" + cidade[2] + "2" + "2" + prest.documento + f"{numero:013d}" + f"{dh:%y%m}" + g.digitos(9))
    id_nfse += str(dv_mod11_chave(id_nfse[3:]))
    dh_iso = dh.isoformat(timespec="seconds")
    toma_end = toma.endereco
    trib_fed = ""
    if reter_federais:
        trib_fed = (f"<tribFed><vRetIRRF>{v_irrf:.2f}</vRetIRRF><vRetCSLL>{v_csll:.2f}</vRetCSLL>"
                    f"<tpRetPisCofins>3</tpRetPisCofins><piscofins><CST>00</CST></piscofins></tribFed>")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse"><infNFSe versao="1.01" Id="{id_nfse}">
<xLocEmi>{x(cidade[0])}</xLocEmi><xLocPrestacao>{x(cidade[0])}</xLocPrestacao><nNFSe>{numero}</nNFSe>
<cLocIncid>{cidade[2]}</cLocIncid><xLocIncid>{x(cidade[0])}</xLocIncid><xTribNac>{x(desc_serv)}</xTribNac>
<verAplic>SINTETICO_1.0</verAplic><ambGer>2</ambGer><tpEmis>1</tpEmis><procEmi>1</procEmi><cStat>100</cStat>
<dhProc>{dh_iso}</dhProc><nDFSe>{g.rng.randint(100000, 999999)}</nDFSe>
<emit>{tag_documento(prest)}<xNome>{x(prest.nome)}</xNome><enderNac><xLgr>{x(prest.endereco.logradouro)}</xLgr>
<nro>{prest.endereco.numero}</nro><xBairro>{x(prest.endereco.bairro)}</xBairro><cMun>{cidade[2]}</cMun>
<UF>{cidade[1]}</UF><CEP>{prest.endereco.cep}</CEP></enderNac><fone>{prest.fone}</fone><email>{prest.email}</email></emit>
<valores><vBC>{v_serv:.2f}</vBC><pAliqAplic>{aliq:.2f}</pAliqAplic><vISSQN>{v_iss:.2f}</vISSQN>
<vTotalRet>{v_ret:.2f}</vTotalRet><vLiq>{v_liq:.2f}</vLiq></valores>
<DPS versao="1.00"><infDPS Id="DPS{n_dps}"><tpAmb>1</tpAmb><dhEmi>{dh_iso}</dhEmi><nDPS>{n_dps}</nDPS>
<serie>1</serie><dCompet>{dh.date().isoformat()}</dCompet><tpEmit>1</tpEmit>
<prest>{tag_documento(prest)}<xNome>{x(prest.nome)}</xNome><end><xLgr>{x(prest.endereco.logradouro)}</xLgr>
<nro>{prest.endereco.numero}</nro><xBairro>{x(prest.endereco.bairro)}</xBairro><cMun>{cidade[2]}</cMun>
<xMun>{x(cidade[0])}</xMun><UF>{cidade[1]}</UF><CEP>{prest.endereco.cep}</CEP></end>
<regTrib><opSimpNac>1</opSimpNac><regEspTrib>0</regEspTrib></regTrib></prest>
<toma>{tag_documento(toma)}<xNome>{x(toma.nome)}</xNome><end><endNac><cMun>{toma_end.cod_municipio}</cMun>
<CEP>{toma_end.cep}</CEP></endNac><xLgr>{x(toma_end.logradouro)}</xLgr><nro>{toma_end.numero}</nro>
<xBairro>{x(toma_end.bairro)}</xBairro></end><fone>{toma.fone}</fone><email>{toma.email}</email></toma>
<serv><cServ><cTribNac>{ctrib}</cTribNac><xDescServ>{x(descricao)}</xDescServ></cServ></serv>
<valores><vServPrest><vServ>{v_serv:.2f}</vServ></vServPrest><trib><tribMun><tribISSQN>1</tribISSQN>
<tpRetISSQN>1</tpRetISSQN><pAliq>{aliq:.2f}</pAliq></tribMun>{trib_fed}</trib></valores>
<infCompl><xInfComp>{AVISO}</xInfComp></infCompl>
</infDPS></DPS></infNFSe></NFSe>
"""
    gab = {
        "emitente": prest.gabarito(),
        "destinatario": toma.gabarito(),
        "numero": numero,
        "numero_dps": n_dps,
        "chave_acesso": id_nfse[3:],
        "data_emissao": dh.date().isoformat(),
        "data_emissao_formatada": dh.strftime("%d/%m/%Y"),
        "hora_emissao": dh.strftime("%H:%M:%S"),
        "valor_total": v_serv,
        "valor_total_formatado": dinheiro(v_serv),
        "valor_liquido": v_liq,
        "valor_iss": v_iss,
        "aliquota_iss": aliq,
        "retencoes_federais": v_ret,
        "servico": descricao,
    }
    return xml, gab


def gerar_pdf(tipo: str, xml: str, destino: Path):
    if tipo == "nfe":
        from brazilfiscalreport.danfe import Danfe as Classe
    elif tipo == "nfce":
        from brazilfiscalreport.danfce import Danfce as Classe
    else:
        from brazilfiscalreport.danfse import Danfse as Classe
    Classe(xml=xml).output(str(destino))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", type=Path)
    ap.add_argument("--quantidade", type=int, default=50)
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--tipos", nargs="+", default=["nfe", "nfce", "nfse"], choices=["nfe", "nfce", "nfse"])
    args = ap.parse_args()

    for i_tipo, tipo in enumerate(args.tipos):
        g = Gerador(args.semente + 1000 * (["nfe", "nfce", "nfse"].index(tipo) + 1))
        pasta = args.base / tipo
        (pasta / "xml").mkdir(parents=True, exist_ok=True)
        (pasta / "pdf").mkdir(parents=True, exist_ok=True)
        docs = []
        for i in range(1, args.quantidade + 1):
            doc_id = f"{tipo}_{i:03d}"
            xml, gab = gerar_nfse(g) if tipo == "nfse" else gerar_nfe_ou_nfce(g, 65 if tipo == "nfce" else 55)
            (pasta / "xml" / f"{doc_id}.xml").write_text(xml, encoding="utf-8")
            gerar_pdf(tipo, xml, pasta / "pdf" / f"{doc_id}.pdf")
            docs.append({"id": doc_id, "arquivo_xml": f"xml/{doc_id}.xml", "arquivo_pdf": f"pdf/{doc_id}.pdf", **gab})
        (pasta / "gabarito.json").write_text(json.dumps({
            "descricao": f"Documentos {tipo.upper()} sintéticos (dados fictícios) para teste de OCR/PLN",
            "semente": args.semente, "quantidade": len(docs), "documentos": docs,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{tipo}: {len(docs)} documentos em {pasta}")


if __name__ == "__main__":
    main()
