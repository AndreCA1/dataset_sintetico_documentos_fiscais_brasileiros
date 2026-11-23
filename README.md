# Conjunto sintético de documentos fiscais brasileiros para avaliação de OCR

Dados, resultados e scripts da avaliação do reconhecimento de texto (OCR) do Google ML Kit em documentos fiscais brasileiros fictícios. O material acompanha a monografia *Extração automática de dados a partir de fotos de documentos fiscais utilizando OCR* (André Carvalho Araújo, Bacharelado em Ciência da Computação, IFMG Campus Formiga, 2026).

O repositório traz:

- **250 documentos sintéticos**, 50 de cada modelo: boleto, NF-e (DANFE), NFC-e (DANFCe), NFS-e (DANFSe) e recibo. Cada documento vem como imagem limpa e como foto simulada, com gabarito por campo e os parâmetros de degradação de cada foto.
- **290 fotos reais** de 145 desses documentos, impressos e fotografados duas vezes com um celular: uma pela câmera comum e outra pelo scanner de documentos do ML Kit.
- **O texto reconhecido pelo ML Kit** em todas as imagens dos três experimentos (texto completo, blocos e linhas) e o resultado por campo. Com isso, todas as tabelas da monografia podem ser recalculadas sem rodar o OCR.
- **Os scripts** de geração do conjunto, de sorteio da amostra impressa, de pré-processamento e de análise.

As imagens ficam fora do git, em três arquivos zip anexados ao [release v1.0](https://github.com/AndreCA1/dataset_sintetico_documentos_fiscais_brasileiros/releases/tag/v1.0) (veja [Download das imagens](#download-das-imagens)). O código do sistema descrito na monografia (aplicativo, API, sistema web) não faz parte deste repositório.

> [!WARNING]
> **Todos os documentos são fictícios.** Nomes, endereços, CPFs, CNPJs, chaves de acesso, linhas digitáveis e códigos de barras foram gerados aleatoriamente. Os números têm dígitos verificadores válidos, para que o conjunto se pareça com documentos reais, mas **não têm valor fiscal nem de pagamento**: as notas não foram autorizadas por nenhuma SEFAZ ou prefeitura, e os boletos não foram registrados em nenhum banco. Os documentos trazem a indicação de que são fictícios. Qualquer coincidência com pessoas, empresas, contas ou documentos reais é acidental.

## Os três experimentos

| | Imagens | Captura | OCR |
|---|---:|---|---|
| **1. Sintético** | 500 (250 PNG limpos + 250 fotos simuladas) | Imagens geradas por script; a foto simulada aplica perspectiva, rotação de até ±4°, iluminação desigual, ruído, desfoque e compressão JPEG | Emulador do Android Studio (perfil Medium Phone, Android 15, x86_64 com Google Play) |
| **2. Fotos reais** | 290 (145 documentos × 2 modos) | Documentos impressos e fotografados num Xiaomi Redmi Note 13 Pro 5G, pela câmera comum e pelo scanner de documentos do ML Kit (modo completo) | No próprio celular |
| **3. Pré-processamento** | 1.305 (145 fotos da câmera comum × 9 variantes) | Fotos da câmera comum tratadas com OpenCV antes do OCR | No celular |

Os 145 documentos do experimento 2 saíram de um sorteio de 30 por modelo, feito com a semente **20261115** (`scripts/montar_impressao.py`). O sorteio deu 150 documentos. Cinco deles, as NFS-e nº 044 a 048 (`nfse_026` a `nfse_030`), foram sorteados mas não foram impressos, e por isso ficaram fora da amostra.

As 9 variantes do experimento 3 são estas (detalhes em `scripts/preprocessamento.py`):

- original;
- recodificada em JPEG;
- escala de cinza;
- mediana 3×3;
- CLAHE;
- correção de inclinação;
- limiar adaptativo;
- limiar de Otsu;
- pipeline completo (cinza, mediana, inclinação e limiar adaptativo).

Em todos os experimentos, o OCR foi feito pelo pacote Flutter `google_mlkit_text_recognition` 0.17.1, executado por um teste de integração do aplicativo. Esse teste faz parte do sistema e não é publicado aqui. Os scripts `avaliar_ocr.py`, `fotos_reais.py` e `preprocessamento.py` mantêm o passo `coletar`, que servia as imagens a esse teste, só para documentar o processo. Para reproduzir os números, basta o passo `relatorio`, que parte dos textos já reconhecidos em `resultados/`.

## Download das imagens

As 790 imagens estão no [release v1.0](https://github.com/AndreCA1/dataset_sintetico_documentos_fiscais_brasileiros/releases/tag/v1.0), divididas em três zips. Descompacte cada um na raiz do repositório: os arquivos vão para as pastas indicadas em [Estrutura](#estrutura).

| Arquivo | Conteúdo | Tamanho | SHA-256 |
|---|---|---:|---|
| [`sinteticos_png.zip`](https://github.com/AndreCA1/dataset_sintetico_documentos_fiscais_brasileiros/releases/download/v1.0/sinteticos_png.zip) | 250 imagens limpas (PNG) | 60 MB | `1a25870cc20253edc4a802ad56c8e6d115edf93feeec048ac1c392031ed18294` |
| [`sinteticos_fotos_simuladas.zip`](https://github.com/AndreCA1/dataset_sintetico_documentos_fiscais_brasileiros/releases/download/v1.0/sinteticos_fotos_simuladas.zip) | 250 fotos simuladas (JPEG) | 66 MB | `feaef885b2728090769d5b5abf3343ec770b29aacdd51d580584d546bebac8e9` |
| [`fotos_reais.zip`](https://github.com/AndreCA1/dataset_sintetico_documentos_fiscais_brasileiros/releases/download/v1.0/fotos_reais.zip) | 290 fotos reais (JPEG) | 726 MB | `578cf8c107a3a53634a19baf0eb427c2fe353d8e8ec3c5ddfcc4488e780dbb6e` |

```bash
for z in sinteticos_png sinteticos_fotos_simuladas fotos_reais; do
  curl -LO https://github.com/AndreCA1/dataset_sintetico_documentos_fiscais_brasileiros/releases/download/v1.0/$z.zip && unzip -q $z.zip
done
```

Para reproduzir as tabelas, as imagens não são necessárias: os relatórios e as análises partem dos gabaritos, dos metadados e dos textos reconhecidos, que estão no git. Elas só são usadas para rodar o OCR de novo, gerar as variantes do experimento 3, montar o PDF de impressão e validar os códigos de barras.

## Estrutura

```
dados/
  sinteticos/
    boletos_sinteticos/
      gabarito.json              gabarito dos 50 boletos
      html/                      boletos de origem (HTML gerado com o OpenBoleto)
      imagens/
        png/boleto_NNN.png       imagem limpa (sinteticos_png.zip)
        foto/boleto_NNN.jpg      foto simulada (sinteticos_fotos_simuladas.zip)
        metadados.json           caminhos e parâmetros de degradação de cada imagem
    documentos_sinteticos/
      nfe/  nfce/  nfse/         gabarito.json, xml/ e pdf/ de cada nota
      recibo/                    gabarito.json e html/
      imagens/
        <tipo>/png/<id>.png      imagem limpa (sinteticos_png.zip)
        <tipo>/foto/<id>.jpg     foto simulada (sinteticos_fotos_simuladas.zip)
        metadados.json           caminhos e parâmetros de degradação de cada imagem
  fotos_reais/
    lista.csv                    os 145 documentos fotografados
    fotos/NNN_comum.jpg          câmera comum (fotos_reais.zip)
    fotos/NNN_scanner.jpg        scanner de documentos do ML Kit (fotos_reais.zip)
resultados/
  experimento1_sintetico/        ocr.jsonl, detalhes.csv, relatorio.md
  experimento2_fotos_reais/      capturas.jsonl, detalhes.csv, relatorio.md
  experimento3_preprocessamento/ ocr.jsonl, variantes.jsonl, detalhes.csv, relatorio.md
  cer/                           cer_campos.csv, cer.md
  analises/                      CSVs de Spearman, confiança e bootstrap
scripts/
  avaliar_ocr.py                 métrica por campo e relatório do experimento 1
  fotos_reais.py                 relatório do experimento 2
  preprocessamento.py            variantes OpenCV e relatório do experimento 3
  montar_impressao.py            sorteio (semente 20261115) e PDF de impressão
  cer_campos.py                  CER por campo (experimentos 1 e 2)
  spearman_degradacao.py         Spearman entre acerto e degradação (experimento 1)
  confianca_acerto.py            confiança do ML Kit × acerto (experimento 1)
  bootstrap_captura.py           câmera comum × scanner, bootstrap e teste dos sinais
  geradores/boletos/             geração e validação dos boletos (PHP + Python)
  geradores/documentos/          geração e validação das notas, recibos e fotos simuladas
```

A pasta `dados/sinteticos` mantém a estrutura de pastas usada na geração. Os scripts a recebem como `--dataset`, que já é o valor padrão.

## Formato dos dados

### Gabarito

Há um `gabarito.json` por modelo, com os campos `descricao`, `semente`, `quantidade` e a lista de documentos: `boletos` no arquivo dos boletos e `documentos` nos demais. Cada documento traz o `id` (por exemplo, `nfe_001`) e os valores dos campos, além de formas auxiliares (texto formatado, só dígitos, valor por extenso). Exemplo resumido de uma NF-e:

```json
{
  "id": "nfe_001", "modelo": 55,
  "chave_acesso": "52250152874015000182550020002230711445968658", "numero": 223071,
  "data_emissao": "2025-01-17", "valor_total": 1147.67,
  "emitente":     {"nome": "Indústria Ipê ME", "tipo_documento": "CNPJ", "documento": "52.874.015/0001-82", "documento_numeros": "52874015000182", "...": "..."},
  "destinatario": {"nome": "Aline Freitas Vieira", "tipo_documento": "CPF", "documento": "730.839.584-71", "...": "..."}
}
```

Datas estão em ISO (`AAAA-MM-DD`) e valores em número decimal. A NFC-e pode não ter destinatário, e nesse caso o campo fica de fora da avaliação. A lista de campos avaliados de cada modelo está em `CAMPOS`, em `scripts/avaliar_ocr.py`: são 10 no boleto, 8 na NF-e, na NFC-e e no recibo, e 9 na NFS-e.

### Parâmetros de degradação

Cada item de `imagens/metadados.json` traz `id`, `png`, `foto`, `png_tamanho_px` e `foto_degradacao`:

```json
{"largura_px": 1623, "altura_px": 1967, "rotacao_graus": -2.24, "deslocamento_perspectiva_px": 22.2,
 "intensidade_iluminacao": 0.352, "ruido_sigma": 5.49, "desfoque_raio": 1.24, "contraste": 0.889,
 "qualidade_jpeg": 76}
```

A semente da degradação (42) e a escala de captura também estão no arquivo.

### Texto reconhecido (`ocr.jsonl` e `capturas.jsonl`)

Cada linha é um JSON com o resultado de uma imagem:

```json
{"chave": "boleto/png/boleto_001", "ms": 4293,
 "ocr": {"engine": "Google ML Kit Text Recognition", "engine_version": "0.17.1",
         "full_text": "…",
         "blocks": [{"text": "…", "box": {"x": 28.0, "y": 134.0, "width": 150.0, "height": 22.0},
                     "confidence": null, "languages": ["und"],
                     "lines": [{"text": "…", "box": {…}, "confidence": 0.87, "angle": 0.0, "languages": ["und"]}]}]}}
```

- **`chave`:** `tipo/variante/id` no experimento 1 (`variante` é `png` ou `foto`) e `variante/NNN` no experimento 3.
- **`confidence`:** o ML Kit só a informa nas linhas; nos blocos, ela vem nula. A confiança de uma imagem, usada nas análises, é a média simples da confiança das linhas.
- **`ms`:** tempo do OCR no aparelho, em milissegundos.

O `capturas.jsonl` do experimento 2 tem, além do `ocr`, os campos `numero`, `modo` (`comum` ou `scanner`), `arquivo`, `largura`, `altura`, `brilho`, `nitidez` (variância do laplaciano), `confianca`, `avisos_imagem`, `avisos_texto` e `quando`. O arquivo tem 312 linhas porque algumas capturas foram refeitas. Vale a última de cada par (`numero`, `modo`), como fazem os scripts, e isso resulta nas 290 fotos de `dados/fotos_reais/fotos`.

O `variantes.jsonl` do experimento 3 registra o tamanho em bytes de cada variante gerada e, nas variantes com correção de inclinação, o ângulo aplicado.

### Resultado por campo (`detalhes.csv` e `cer_campos.csv`)

Há uma linha por campo avaliado, com `campo`, `esperado`, `status` e `distancia`, mais as colunas que identificam a imagem em cada experimento. O `status` segue esta regra:

- **`exato`:** o valor do gabarito aparece no texto do OCR, depois de normalizar caixa, acentos e espaços. CPF, CNPJ, chave de acesso, linha digitável e nosso número são comparados só pelos dígitos.
- **`quase`:** o valor não aparece, mas há um trecho do texto a até 2 edições de distância.
- **`perdido`:** nenhum dos dois.

O `cer_campos.csv` acrescenta `d`, a menor distância de edição até um trecho do texto, e `n`, o tamanho do valor esperado. O CER do campo é `cer = min(d/n, 1)`. O CER médio é a média desses valores por campo, e o CER global é Σd/Σn.

### Fotos reais

O `lista.csv` tem as colunas `numero`, `tipo`, `modelo`, `id`, `folha`, `escala`, `foto_comum` e `foto_scanner`:

- **`numero`:** o número impresso ao lado de cada documento.
- **`id`:** liga a foto ao gabarito do conjunto sintético.
- **`folha`:** a folha do PDF de impressão em que o documento saiu.
- **`escala`:** NF-e e NFS-e foram impressas a 95% para caber na área imprimível; os demais modelos, em tamanho real.

As fotos da câmera comum têm 3060×4080 px e trazem no EXIF só dados técnicos da câmera (marca, modelo, data e hora, exposição). As do scanner têm tamanho variável, por causa do recorte automático, e não têm EXIF. Nenhuma foto tem localização.

## Como reproduzir

Os comandos abaixo são executados na raiz do repositório. Os scripts de relatório usam só a biblioteca padrão do Python (testado com Python 3.13). As análises estatísticas precisam de `scipy` e `numpy`, e as variantes de pré-processamento, de `opencv-python-headless`. As versões estão em `scripts/requirements.txt`.

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
```

| Resultado na monografia | Comando | Saída |
|---|---|---|
| Experimento 1: acerto por modelo, PNG × foto simulada, acerto por campo | `python3 scripts/avaliar_ocr.py relatorio --piores 25` | `resultados/experimento1_sintetico/` |
| CER médio e global por modelo (experimentos 1 e 2) | `python3 scripts/cer_campos.py` | `resultados/cer/` |
| Spearman entre acerto e cada parâmetro de degradação | `.venv/bin/python scripts/spearman_degradacao.py` | `resultados/analises/spearman_degradacao.csv` |
| Confiança do ML Kit × acerto e varredura de limiares | `.venv/bin/python scripts/confianca_acerto.py` | `resultados/analises/confianca_*.csv` |
| Experimento 2: câmera comum × scanner | `python3 scripts/fotos_reais.py relatorio` | `resultados/experimento2_fotos_reais/` |
| Diferença entre os modos (bootstrap, 5.000 reamostragens, semente 20261115) e teste dos sinais | `.venv/bin/python scripts/bootstrap_captura.py` | `resultados/analises/bootstrap_captura.csv` |
| Experimento 3: acerto por variante e comparação pareada | `python3 scripts/preprocessamento.py relatorio` | `resultados/experimento3_preprocessamento/` |
| Sorteio dos documentos impressos | `python3 scripts/montar_impressao.py --saida /tmp/impressao` (requer Pillow e as imagens PNG) | `lista.csv` com os 150 sorteados e `impressao.pdf` |

Os comandos regravam os arquivos de `resultados/`. Com os dados deste repositório, `git diff` deve mostrar diferença apenas na linha "Gerado em" dos `relatorio.md`. Os números principais são estes:

| Medida | Valor |
|---|---:|
| Experimento 1, acerto exato: PNG / foto simulada | 98,2% / 91,8% |
| Spearman entre o raio do desfoque e o acerto (250 fotos simuladas) | −0,33 |
| Spearman entre a confiança e o acerto (500 imagens) | 0,29 |
| Experimento 2, acerto exato: câmera comum / scanner | 90,9% / 84,9% |
| Experimento 2, CER médio da câmera comum | 0,8% |
| Experimento 3, acerto exato: original / limiar adaptativo / pipeline completo / Otsu | 91,3% / 81,4% / 78,8% / 64,0% |

### Gerar o conjunto sintético de novo

Os geradores ficam em `scripts/geradores/` e devem ser executados de dentro da pasta do conjunto, passando `.` como argumento. Eles usam a semente 42 por padrão.

- **Boletos:** `php gerar_boletos.php <caminho_do_openboleto> <pasta_saida>` gera os HTML e o gabarito, com a biblioteca [OpenBoleto](https://github.com/openboleto/openboleto) (MIT). Depois, `gerar_imagens.py` gera o PNG e a foto simulada (Playwright/Chromium, Pillow, NumPy). `validar.py` confere os dígitos verificadores e o fator de vencimento, e `validar_barras.py` lê os códigos de barras (pyzbar e libzbar).
- **Notas e recibos:** `gerar_notas.py` monta o XML no leiaute oficial e gera o PDF com a biblioteca [BrazilFiscalReport](https://github.com/Engenere/BrazilFiscalReport) 1.4.0 (LGPL-3.0). `gerar_recibos.py` gera o HTML dos recibos (num2words). `gerar_imagens.py` rasteriza os PDFs a 200 dpi (PyMuPDF), captura os HTML (Playwright) e aplica a mesma degradação dos boletos (`degradacao.py`). `validar.py` confere os campos, os totais e os códigos de barras.

Exemplo para os documentos:

```bash
cd dados/sinteticos/documentos_sinteticos
python3 ../../../scripts/geradores/documentos/gerar_notas.py .
python3 ../../../scripts/geradores/documentos/gerar_recibos.py .
python3 ../../../scripts/geradores/documentos/gerar_imagens.py .
```

As bibliotecas OpenBoleto e BrazilFiscalReport não são redistribuídas aqui; instale-as a partir dos repositórios originais. Os logotipos de bancos que aparecem nos boletos vêm do OpenBoleto e pertencem aos respectivos bancos.

## Versões

| Componente | Versão |
|---|---|
| Reconhecimento de texto | Google ML Kit, pacote Flutter `google_mlkit_text_recognition` 0.17.1 |
| Aparelho (experimentos 2 e 3) | Xiaomi Redmi Note 13 Pro 5G (2312DRA50G) |
| Emulador (experimento 1) | Android Studio, perfil Medium Phone, Android 15, x86_64 com Google Play |
| Python | 3.13 (relatórios e pré-processamento); 3.12 (análises estatísticas) |
| OpenCV | 5.0.0 (`opencv-python-headless` 5.0.0.93), NumPy 2.5 |
| SciPy / NumPy (análises) | 1.16.0 / 2.2.3 |
| Geradores | Pillow 13.0.0, Playwright 1.65.2, PyMuPDF 2.1, num2words 0.5.14, pyzbar 0.1.9, BrazilFiscalReport 1.4.0 |
| Semente do sorteio e do bootstrap | 20261115 |
| Semente da geração e da degradação | 42 |

## Dados de terceiros

A calibração da degradação citada na monografia usou as 813 fotos do conjunto de Cruz e Castelli (2022), que **não** são redistribuídas aqui. Para obtê-las:

> CRUZ, F.; CASTELLI, M. *Dataset of invoices and receipts including annotation of relevant fields*. Zenodo, 2022. DOI: [10.5281/zenodo.6371710](https://doi.org/10.5281/zenodo.6371710).

## Licença

- **Dados**, ou seja, tudo em `dados/` e `resultados/`: [Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.pt-br). Veja `LICENSE-DADOS.md`.
- **Scripts**, em `scripts/`: [licença MIT](LICENSE).

## Como citar

Para citar este conjunto de dados:

> ARAÚJO, André Carvalho. **Conjunto sintético de documentos fiscais brasileiros para avaliação de OCR**. Versão v1.0. 2026. Disponível em: https://github.com/AndreCA1/dataset_sintetico_documentos_fiscais_brasileiros.

Para citar a monografia:

> ARAÚJO, André Carvalho. **Extração automática de dados a partir de fotos de documentos fiscais utilizando OCR**. 2026. Monografia (Bacharelado em Ciência da Computação) – Instituto Federal de Educação, Ciência e Tecnologia de Minas Gerais, Campus Formiga, Formiga, 2026.

Os metadados de citação também estão em `CITATION.cff`.
