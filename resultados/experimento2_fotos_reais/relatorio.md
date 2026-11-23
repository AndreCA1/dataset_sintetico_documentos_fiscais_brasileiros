# OCR com fotos reais: câmera comum × scanner

Gerado em 2026-11-15 23:43. Capturas: 290; documentos com as duas capturas: 145.

Documentos sintéticos impressos (amostra de `impressao/lista.csv`; NF-e e NFS-e reduzidas a 95% para caber na área imprimível) e fotografados com o celular. Mesma métrica por campo do benchmark sintético (`avaliar_ocr.py`). *Confiança < 0,74* conta as capturas que o aviso de leitura incerta (retirado do app em 2026-11-15) teria avisado; *aviso imagem* = resolução baixa, escura ou desfocada.

## Resumo

| Tipo | Modo | Imagens | Campos | Exato | Quase | Imagens 100% | Confiança média | Confiança < 0,74 | Aviso imagem | Menor lado (px, mediana) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| boleto | câmera comum | 30 | 300 | 99.3% | 0.7% | 28 | 0.821 | 0 | 0 | 3060 |
| boleto | scanner | 30 | 300 | 93.7% | 6.3% | 14 | 0.773 | 2 | 0 | 2569 |
| nfe | câmera comum | 30 | 240 | 78.3% | 20.4% | 2 | 0.661 | 30 | 0 | 3060 |
| nfe | scanner | 30 | 240 | 71.2% | 21.7% | 0 | 0.607 | 30 | 0 | 2435 |
| nfce | câmera comum | 30 | 224 | 91.5% | 8.5% | 16 | 0.782 | 0 | 0 | 3060 |
| nfce | scanner | 30 | 224 | 83.9% | 14.7% | 7 | 0.738 | 11 | 0 | 1290 |
| nfse | câmera comum | 25 | 225 | 89.8% | 6.7% | 7 | 0.743 | 10 | 0 | 3060 |
| nfse | scanner | 25 | 225 | 81.3% | 16.0% | 6 | 0.669 | 25 | 0 | 2469 |
| recibo | câmera comum | 30 | 240 | 93.3% | 6.7% | 18 | 0.834 | 0 | 0 | 3060 |
| recibo | scanner | 30 | 240 | 91.7% | 6.2% | 17 | 0.806 | 1 | 0 | 1736 |
| **TOTAL** | câmera comum | 145 | 1229 | 90.9% | 8.2% | 71 | 0.769 | 40 | 0 | 3060 |
| **TOTAL** | scanner | 145 | 1229 | 84.9% | 12.6% | 44 | 0.720 | 69 | 0 | 2341 |

## Comparação pareada

Em 145 documentos com as duas capturas, o scanner acertou mais campos em 20, a câmera comum em 68 e houve empate em 57.

## Sintético × real (mesmos documentos, acerto exato)

| Tipo | Documentos | PNG | Foto sintética | Câmera comum | Scanner |
|---|---:|---:|---:|---:|---:|
| boleto | 30 | 100.0% | 96.3% | 99.3% | 93.7% |
| nfe | 30 | 99.6% | 86.2% | 78.3% | 71.2% |
| nfce | 30 | 98.7% | 89.7% | 91.5% | 83.9% |
| nfse | 25 | 97.8% | 94.2% | 89.8% | 81.3% |
| recibo | 30 | 95.0% | 93.3% | 93.3% | 91.7% |
| **TOTAL** | 145 | 98.3% | 92.2% | 90.9% | 84.9% |

## Por condição de captura

| Condição | Modo | Imagens | Campos | Exato | Quase | Imagens 100% | Confiança média | Confiança < 0,74 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| normal | câmera comum | 145 | 1229 | 90.9% | 8.2% | 71 | 0.769 | 40 |
| normal | scanner | 145 | 1229 | 84.9% | 12.6% | 44 | 0.720 | 69 |

## Limiar de confiança nas fotos reais

Captura ruim = menos de 75% dos campos certos, como na varredura sintética.

| Limiar | Avisos | Capturas ruins avisadas | Avisos sem erro | Acerto das avisadas | Acerto das demais |
|---|---:|---:|---:|---:|---:|
| 0.70 | 89 | 21/26 | 8 | 76.0% | 93.0% |
| 0.72 | 91 | 21/26 | 8 | 76.2% | 93.0% |
| **0.74** | 109 | 23/26 | 13 | 78.2% | 93.5% |
| 0.76 | 144 | 25/26 | 21 | 80.7% | 94.7% |
| 0.78 | 171 | 25/26 | 30 | 82.3% | 95.7% |
| 0.80 | 204 | 25/26 | 51 | 84.2% | 96.3% |

## Piores capturas

| Nº | Documento | Modo | Condição | Campos exatos | Confiança | Avisos |
|---|---:|---:|---:|---:|---:|---:|
| #125 | recibo_006 | scanner | normal | 2/8 | 0.477 | leituraIncerta |
| #116 | nfce_043 | scanner | normal | 2/7 | 0.616 | leituraIncerta |
| #013 | nfe_020 | scanner | normal | 3/8 | 0.588 | leituraIncerta |
| #035 | nfse_006 | scanner | normal | 4/9 | 0.646 | leituraIncerta |
| #006 | nfe_010 | scanner | normal | 4/8 | 0.598 | leituraIncerta |
| #025 | nfe_041 | scanner | normal | 4/8 | 0.594 | leituraIncerta |
| #030 | nfe_047 | câmera comum | normal | 4/8 | 0.654 | leituraIncerta |
| #036 | nfse_012 | câmera comum | normal | 5/9 | 0.755 |  |
| #054 | nfse_040 | scanner | normal | 5/9 | 0.663 | leituraIncerta |
| #002 | nfe_003 | câmera comum | normal | 5/8 | 0.661 | leituraIncerta |
| #003 | nfe_005 | scanner | normal | 5/8 | 0.627 | leituraIncerta |
| #007 | nfe_011 | scanner | normal | 5/8 | 0.589 | leituraIncerta |
| #008 | nfe_012 | scanner | normal | 5/8 | 0.613 | leituraIncerta |
| #011 | nfe_017 | câmera comum | normal | 5/8 | 0.666 | leituraIncerta |
| #018 | nfe_029 | scanner | normal | 5/8 | 0.578 | leituraIncerta |
