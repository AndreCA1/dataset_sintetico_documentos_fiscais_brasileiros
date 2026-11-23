# Benchmark do OCR (ML Kit) no dataset sintético

Gerado em 2026-11-14 14:58. Imagens avaliadas: 500.

Métrica por campo: **exato** = o valor do gabarito aparece no texto do OCR (sem diferença de caixa/acentos/espaços; só dígitos para CPF, CNPJ, chave, linha digitável e nosso número); **quase** = há um trecho a até 2 edições; **perdido** = nenhum dos dois. *png* é a imagem limpa e *foto* a versão degradada (rotação, perspectiva, ruído, desfoque, JPEG).

## Resumo por tipo

| Tipo | Variante | Imagens | Campos | Exato | Quase (≤2) | Perdido | Imagens 100% | Vazias/erro | Confiança média | ms/imagem |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| boleto | png | 50 | 500 | 100.0% | 0.0% | 0.0% | 50 | 0 | 0.850 | 3059 |
| boleto | foto | 50 | 500 | 96.8% | 3.0% | 0.2% | 44 | 0 | 0.828 | 2847 |
| nfe | png | 50 | 400 | 99.8% | 0.2% | 0.0% | 49 | 0 | 0.794 | 4737 |
| nfe | foto | 50 | 400 | 84.0% | 13.2% | 2.8% | 19 | 0 | 0.684 | 4664 |
| nfce | png | 50 | 369 | 98.9% | 1.1% | 0.0% | 46 | 0 | 0.839 | 2355 |
| nfce | foto | 50 | 369 | 88.9% | 10.3% | 0.8% | 21 | 0 | 0.797 | 2247 |
| nfse | png | 50 | 450 | 98.2% | 1.8% | 0.0% | 42 | 0 | 0.834 | 5251 |
| nfse | foto | 50 | 450 | 94.2% | 4.4% | 1.3% | 33 | 0 | 0.793 | 5045 |
| recibo | png | 50 | 400 | 93.8% | 6.2% | 0.0% | 31 | 0 | 0.866 | 1117 |
| recibo | foto | 50 | 400 | 93.2% | 6.5% | 0.2% | 31 | 0 | 0.862 | 1090 |
| **TOTAL** | png | 250 | 2119 | 98.2% | 1.8% | 0.0% | 218 | 0 | 0.836 | 3304 |
| **TOTAL** | foto | 250 | 2119 | 91.8% | 7.2% | 1.0% | 148 | 0 | 0.793 | 3179 |

## Acerto por campo

| Tipo | Campo | PNG exato | PNG quase | Foto exato | Foto quase |
|---|---:|---:|---:|---:|---:|
| boleto | linha_digitavel | 100.0% | 0.0% | 100.0% | 0.0% |
| boleto | valor_documento | 100.0% | 0.0% | 96.0% | 4.0% |
| boleto | data_vencimento | 100.0% | 0.0% | 92.0% | 8.0% |
| boleto | data_documento | 100.0% | 0.0% | 92.0% | 6.0% |
| boleto | numero_documento | 100.0% | 0.0% | 100.0% | 0.0% |
| boleto | nosso_numero | 100.0% | 0.0% | 96.0% | 4.0% |
| boleto | beneficiario_nome | 100.0% | 0.0% | 96.0% | 4.0% |
| boleto | beneficiario_cnpj | 100.0% | 0.0% | 96.0% | 4.0% |
| boleto | pagador_nome | 100.0% | 0.0% | 100.0% | 0.0% |
| boleto | pagador_cpf | 100.0% | 0.0% | 100.0% | 0.0% |
| nfe | chave_acesso | 100.0% | 0.0% | 82.0% | 6.0% |
| nfe | numero | 100.0% | 0.0% | 98.0% | 2.0% |
| nfe | data_emissao | 100.0% | 0.0% | 86.0% | 14.0% |
| nfe | valor_total | 98.0% | 2.0% | 62.0% | 36.0% |
| nfe | emitente_nome | 100.0% | 0.0% | 96.0% | 0.0% |
| nfe | emitente_documento | 100.0% | 0.0% | 88.0% | 10.0% |
| nfe | destinatario_nome | 100.0% | 0.0% | 90.0% | 10.0% |
| nfe | destinatario_documento | 100.0% | 0.0% | 70.0% | 28.0% |
| nfce | chave_acesso | 100.0% | 0.0% | 56.0% | 38.0% |
| nfce | numero | 100.0% | 0.0% | 92.0% | 8.0% |
| nfce | data_emissao | 100.0% | 0.0% | 92.0% | 8.0% |
| nfce | valor_total | 98.0% | 2.0% | 96.0% | 4.0% |
| nfce | emitente_nome | 96.0% | 4.0% | 90.0% | 10.0% |
| nfce | emitente_documento | 100.0% | 0.0% | 94.0% | 6.0% |
| nfce | destinatario_nome | 100.0% | 0.0% | 100.0% | 0.0% |
| nfce | destinatario_documento | 97.6% | 2.4% | 97.6% | 2.4% |
| nfse | chave_acesso | 98.0% | 2.0% | 88.0% | 8.0% |
| nfse | numero | 100.0% | 0.0% | 98.0% | 2.0% |
| nfse | data_emissao | 100.0% | 0.0% | 90.0% | 10.0% |
| nfse | valor_total | 94.0% | 6.0% | 94.0% | 6.0% |
| nfse | valor_iss | 100.0% | 0.0% | 98.0% | 2.0% |
| nfse | emitente_nome | 98.0% | 2.0% | 92.0% | 4.0% |
| nfse | emitente_documento | 100.0% | 0.0% | 100.0% | 0.0% |
| nfse | destinatario_nome | 94.0% | 6.0% | 88.0% | 8.0% |
| nfse | destinatario_documento | 100.0% | 0.0% | 100.0% | 0.0% |
| recibo | numero | 100.0% | 0.0% | 100.0% | 0.0% |
| recibo | data | 92.0% | 8.0% | 84.0% | 16.0% |
| recibo | valor | 74.0% | 26.0% | 76.0% | 24.0% |
| recibo | historico | 100.0% | 0.0% | 94.0% | 6.0% |
| recibo | pagador_nome | 98.0% | 2.0% | 98.0% | 0.0% |
| recibo | pagador_documento | 98.0% | 2.0% | 98.0% | 2.0% |
| recibo | recebedor_nome | 96.0% | 4.0% | 100.0% | 0.0% |
| recibo | recebedor_documento | 92.0% | 8.0% | 96.0% | 4.0% |

## 25 piores imagens

| Imagem | Campos exatos | Confiança média | Rotação (°) | Desfoque | Ruído | JPEG | Obs. |
|---|---:|---:|---:|---:|---:|---:|---:|
| nfe/foto/nfe_008 | 2/8 | 0.488 | 3.41 | 1.28 | 4.01 | 71 |  |
| nfe/foto/nfe_001 | 3/8 | 0.573 | -2.24 | 1.24 | 5.49 | 76 |  |
| nfe/foto/nfe_006 | 3/8 | 0.541 | 3.2 | 0.92 | 4.77 | 58 |  |
| nfe/foto/nfe_015 | 3/8 | 0.498 | 0.09 | 1.24 | 3.42 | 70 |  |
| nfse/foto/nfse_047 | 4/9 | 0.690 | 3.91 | 1.23 | 6.32 | 61 |  |
| boleto/foto/boleto_019 | 5/10 | 0.716 | -1.82 | 1.27 | 5.62 | 56 |  |
| nfe/foto/nfe_013 | 4/8 | 0.501 | 1.13 | 1.25 | 2.58 | 71 |  |
| nfe/foto/nfe_033 | 4/8 | 0.664 | -2.1 | 0.74 | 6.89 | 58 |  |
| nfe/foto/nfe_035 | 4/8 | 0.489 | 2.33 | 1.22 | 5.36 | 61 |  |
| nfce/foto/nfce_015 | 4/7 | 0.710 | -1.21 | 1.24 | 5.38 | 64 |  |
| boleto/foto/boleto_033 | 6/10 | 0.733 | -2.14 | 1.23 | 4.33 | 74 |  |
| boleto/foto/boleto_038 | 6/10 | 0.711 | 2.64 | 1.28 | 5.87 | 63 |  |
| nfce/foto/nfce_009 | 5/8 | 0.739 | 1.21 | 1.05 | 5.14 | 80 |  |
| nfe/foto/nfe_007 | 5/8 | 0.540 | -1.17 | 1.04 | 5.23 | 61 |  |
| recibo/png/recibo_042 | 5/8 | 0.854 | - | - | - | - |  |
| nfce/foto/nfce_004 | 4/6 | 0.776 | -0.56 | 0.93 | 3.64 | 65 |  |
| nfce/foto/nfce_007 | 4/6 | 0.808 | -1.11 | 0.93 | 6.42 | 85 |  |
| nfse/foto/nfse_035 | 6/9 | 0.723 | -3.08 | 1.04 | 3.22 | 62 |  |
| nfce/foto/nfce_021 | 5/7 | 0.717 | -1.0 | 1.29 | 2.4 | 80 |  |
| nfce/foto/nfce_010 | 6/8 | 0.683 | -2.07 | 1.17 | 6.73 | 75 |  |
| nfce/foto/nfce_023 | 6/8 | 0.828 | -0.69 | 0.06 | 2.88 | 77 |  |
| nfce/foto/nfce_026 | 6/8 | 0.817 | -0.96 | 0.83 | 3.29 | 86 |  |
| nfce/foto/nfce_036 | 6/8 | 0.767 | 1.78 | 0.96 | 2.11 | 88 |  |
| nfce/foto/nfce_042 | 6/8 | 0.707 | 1.85 | 1.08 | 4.67 | 76 |  |
| nfe/foto/nfe_003 | 6/8 | 0.736 | -1.86 | 0.32 | 5.28 | 71 |  |
