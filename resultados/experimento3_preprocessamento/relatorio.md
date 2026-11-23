# Pré-processamento com OpenCV antes do ML Kit (fotos reais, câmera comum)

Gerado em 2026-11-17 00:41. Documentos com todas as variantes: 145.

Mesma métrica por campo do benchmark (`avaliar_ocr.py`). Todas as variantes, inclusive a original, passaram pelo ML Kit na mesma execução e no mesmo aparelho. As variantes tratadas são gravadas em JPEG com qualidade 95; *Recodificada* isola o efeito dessa regravação.

## Acerto exato por tipo

| Variante | boleto | nfe | nfce | nfse | recibo | **Total** |
|---|---:|---:|---:|---:|---:|---:|
| Original | 99.3% | 78.8% | 95.5% | 88.9% | 92.1% | 91.3% |
| Recodificada | 99.7% | 82.5% | 96.0% | 87.6% | 95.4% | 92.6% |
| Escala de cinza | 99.7% | 80.8% | 96.0% | 88.4% | 95.4% | 92.4% |
| Mediana 3x3 | 99.7% | 72.9% | 95.1% | 88.0% | 93.3% | 90.2% |
| CLAHE | 98.7% | 76.2% | 96.0% | 92.9% | 93.8% | 91.8% |
| Correção de inclinação | 98.0% | 81.2% | 94.6% | 88.0% | 95.4% | 91.8% |
| Limiar adaptativo | 96.3% | 63.8% | 87.1% | 79.1% | 77.5% | 81.4% |
| Limiar de Otsu | 84.0% | 28.3% | 76.3% | 35.6% | 89.6% | 64.0% |
| Pipeline completo | 95.7% | 53.3% | 79.5% | 82.2% | 79.6% | 78.8% |

## Resumo e comparação pareada com a foto original

Comparação documento a documento pelo número de campos exatos; *p* é o teste dos sinais bilateral, sem correção para comparações múltiplas.

| Variante | Exato | Quase (≤2) | Perdido | Imagens 100% | Vazias/erro | Confiança média | ms/imagem | Melhor que original | Pior | Empate | p (sinais) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original | 91.3% | 7.5% | 1.2% | 76 | 0 | 0.769 | 3305 | - | - | - | - |
| Recodificada | 92.6% | 6.3% | 1.1% | 85 | 0 | 0.768 | 3307 | 28 | 17 | 100 | 0.135 |
| Escala de cinza | 92.4% | 6.6% | 1.0% | 85 | 0 | 0.768 | 3296 | 26 | 16 | 103 | 0.164 |
| Mediana 3x3 | 90.2% | 8.2% | 1.5% | 76 | 0 | 0.779 | 3266 | 19 | 30 | 96 | 0.152 |
| CLAHE | 91.8% | 6.8% | 1.5% | 85 | 0 | 0.755 | 3411 | 28 | 26 | 91 | 0.892 |
| Correção de inclinação | 91.8% | 7.2% | 1.0% | 81 | 0 | 0.769 | 3284 | 30 | 28 | 87 | 0.896 |
| Limiar adaptativo | 81.4% | 14.1% | 4.5% | 37 | 0 | 0.694 | 3421 | 14 | 87 | 44 | 4.8e-14 |
| Limiar de Otsu | 64.0% | 21.0% | 15.1% | 25 | 0 | 0.662 | 3119 | 6 | 115 | 24 | 3.05e-27 |
| Pipeline completo | 78.8% | 16.4% | 4.8% | 35 | 0 | 0.708 | 3291 | 11 | 87 | 47 | 8.07e-16 |

## Correção de inclinação

| Variante | Imagens | Ângulo mediano (°, módulo) | Máximo (°) | No limite de 10° |
|---|---:|---:|---:|---:|
| Correção de inclinação | 145 | 0.5 | 3.5 | 0 |
| Pipeline completo | 145 | 0.5 | 3.5 | 0 |
