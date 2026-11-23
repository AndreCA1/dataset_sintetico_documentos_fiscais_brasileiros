# CER por campo do OCR (ML Kit)

CER = distância de edição entre o valor esperado e o trecho mais parecido do texto do OCR, dividida pelo tamanho do valor esperado (limitada a 1). *CER médio* é a média por campo; *CER global* é Σd/Σn. *Mediana nos erros* considera só os campos com CER > 0.

## Por tipo e variante

| Variante | Tipo | Campos | Exato | CER médio | CER global | Mediana nos erros |
|---|---:|---:|---:|---:|---:|---:|
| Sintético PNG | boleto | 500 | 100.0% | 0.0% | 0.0% | 0.0% |
| Sintético PNG | nfe | 400 | 99.8% | 0.0% | 0.0% | 16.7% |
| Sintético PNG | nfce | 369 | 98.9% | 0.1% | 0.1% | 6.8% |
| Sintético PNG | nfse | 450 | 98.2% | 0.1% | 0.1% | 5.6% |
| Sintético PNG | recibo | 400 | 93.8% | 0.7% | 0.4% | 12.5% |
| Sintético PNG | **TOTAL** | 2119 | 98.2% | 0.2% | 0.1% | 10.0% |
| Sintético foto | boleto | 500 | 96.8% | 0.4% | 0.2% | 10.0% |
| Sintético foto | nfe | 400 | 84.0% | 2.1% | 1.8% | 11.1% |
| Sintético foto | nfce | 369 | 88.9% | 0.8% | 1.0% | 4.5% |
| Sintético foto | nfse | 450 | 94.2% | 0.6% | 0.8% | 10.0% |
| Sintético foto | recibo | 400 | 93.2% | 0.8% | 0.5% | 10.0% |
| Sintético foto | **TOTAL** | 2119 | 91.8% | 0.9% | 0.8% | 10.0% |
| Real câmera | boleto | 300 | 99.3% | 0.1% | 0.0% | 10.0% |
| Real câmera | nfe | 240 | 78.3% | 1.6% | 1.5% | 4.8% |
| Real câmera | nfce | 224 | 91.5% | 0.6% | 0.5% | 4.5% |
| Real câmera | nfse | 225 | 89.8% | 1.2% | 2.3% | 6.9% |
| Real câmera | recibo | 240 | 93.3% | 0.7% | 0.4% | 10.0% |
| Real câmera | **TOTAL** | 1229 | 90.9% | 0.8% | 0.9% | 7.1% |
| Real scanner | boleto | 300 | 93.7% | 0.6% | 0.4% | 10.0% |
| Real scanner | nfe | 240 | 71.2% | 2.4% | 3.3% | 7.1% |
| Real scanner | nfce | 224 | 83.9% | 1.2% | 1.3% | 5.1% |
| Real scanner | nfse | 225 | 81.3% | 1.1% | 1.9% | 4.0% |
| Real scanner | recibo | 240 | 91.7% | 1.5% | 1.2% | 14.6% |
| Real scanner | **TOTAL** | 1229 | 84.9% | 1.3% | 1.6% | 7.1% |

## Por campo (CER médio)

| Tipo | Campo | Sintético PNG | Sintético foto | Real câmera | Real scanner |
|---|---:|---:|---:|---:|---:|
| boleto | linha_digitavel | 0.0% | 0.0% | 0.0% | 0.1% |
| boleto | valor_documento | 0.0% | 0.6% | 0.0% | 0.5% |
| boleto | data_vencimento | 0.0% | 0.8% | 0.3% | 2.3% |
| boleto | data_documento | 0.0% | 1.4% | 0.3% | 1.7% |
| boleto | numero_documento | 0.0% | 0.0% | 0.0% | 0.0% |
| boleto | nosso_numero | 0.0% | 0.3% | 0.0% | 0.6% |
| boleto | beneficiario_nome | 0.0% | 0.1% | 0.0% | 0.3% |
| boleto | beneficiario_cnpj | 0.0% | 0.3% | 0.0% | 0.0% |
| boleto | pagador_nome | 0.0% | 0.0% | 0.0% | 0.2% |
| boleto | pagador_cpf | 0.0% | 0.0% | 0.0% | 0.6% |
| nfe | chave_acesso | 0.0% | 2.3% | 1.6% | 6.7% |
| nfe | numero | 0.0% | 0.0% | 0.0% | 0.6% |
| nfe | data_emissao | 0.0% | 1.4% | 0.3% | 0.0% |
| nfe | valor_total | 0.3% | 7.1% | 6.5% | 5.4% |
| nfe | emitente_nome | 0.0% | 0.4% | 1.0% | 0.5% |
| nfe | emitente_documento | 0.0% | 1.4% | 0.0% | 1.2% |
| nfe | destinatario_nome | 0.0% | 0.7% | 1.5% | 3.0% |
| nfe | destinatario_documento | 0.0% | 3.4% | 2.2% | 1.5% |
| nfce | chave_acesso | 0.0% | 1.9% | 0.8% | 1.9% |
| nfce | numero | 0.0% | 1.4% | 1.1% | 1.2% |
| nfce | data_emissao | 0.0% | 1.0% | 0.3% | 1.0% |
| nfce | valor_total | 0.3% | 0.7% | 1.2% | 1.7% |
| nfce | emitente_nome | 0.2% | 0.5% | 0.3% | 1.2% |
| nfce | emitente_documento | 0.0% | 0.4% | 0.5% | 1.4% |
| nfce | destinatario_nome | 0.0% | 0.0% | 0.2% | 0.0% |
| nfce | destinatario_documento | 0.2% | 0.2% | 0.0% | 0.4% |
| nfse | chave_acesso | 0.0% | 0.7% | 3.7% | 3.0% |
| nfse | numero | 0.0% | 0.0% | 0.0% | 0.8% |
| nfse | data_emissao | 0.0% | 1.4% | 0.0% | 0.0% |
| nfse | valor_total | 0.7% | 0.7% | 0.0% | 0.0% |
| nfse | valor_iss | 0.0% | 0.4% | 0.7% | 0.7% |
| nfse | emitente_nome | 0.1% | 1.2% | 2.5% | 2.7% |
| nfse | emitente_documento | 0.0% | 0.0% | 0.0% | 0.3% |
| nfse | destinatario_nome | 0.3% | 1.3% | 4.0% | 2.3% |
| nfse | destinatario_documento | 0.0% | 0.0% | 0.3% | 0.3% |
| recibo | numero | 0.0% | 0.0% | 0.0% | 0.8% |
| recibo | data | 0.8% | 1.6% | 2.0% | 3.7% |
| recibo | valor | 3.7% | 3.5% | 2.5% | 3.1% |
| recibo | historico | 0.0% | 0.2% | 0.1% | 0.7% |
| recibo | pagador_nome | 0.1% | 0.6% | 0.5% | 1.5% |
| recibo | pagador_documento | 0.1% | 0.1% | 0.5% | 1.4% |
| recibo | recebedor_nome | 0.2% | 0.0% | 0.0% | 0.1% |
| recibo | recebedor_documento | 0.6% | 0.3% | 0.3% | 0.5% |
