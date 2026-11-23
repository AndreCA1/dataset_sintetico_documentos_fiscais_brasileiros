<?php
/**
 * Gera boletos sintéticos (HTML) com a biblioteca OpenBoleto e o gabarito JSON.
 * Dados fictícios: CPF/CNPJ com DV válido, contas e convênios inventados.
 *
 * Uso: php gerar_boletos.php <caminho_openboleto> <pasta_saida> [quantidade] [semente]
 */

declare(strict_types=1);

[$_, $libPath, $outDir] = $argv + [null, null, null];
$total = (int) ($argv[3] ?? 50);
$seed  = (int) ($argv[4] ?? 42);

if (!$libPath || !$outDir) {
    fwrite(STDERR, "Uso: php gerar_boletos.php <caminho_openboleto> <pasta_saida> [quantidade] [semente]\n");
    exit(1);
}

require $libPath . '/vendor/autoload.php';

use OpenBoleto\Agente;

mt_srand($seed);

$nomes = ['Ana', 'João', 'Maria', 'José', 'Francisca', 'Antônio', 'Juliana', 'Carlos', 'Patrícia', 'Paulo',
    'Aline', 'Lucas', 'Fernanda', 'Rafael', 'Camila', 'Marcos', 'Beatriz', 'Gustavo', 'Letícia', 'Thiago',
    'Luíza', 'Pedro', 'Gabriela', 'Matheus', 'Vitória', 'Felipe', 'Larissa', 'Rodrigo', 'Débora', 'Sérgio'];
$sobrenomes = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira', 'Lima',
    'Gomes', 'Costa', 'Ribeiro', 'Martins', 'Carvalho', 'Almeida', 'Lopes', 'Soares', 'Fernandes', 'Vieira',
    'Barbosa', 'Rocha', 'Dias', 'Nascimento', 'Andrade', 'Moreira', 'Nunes', 'Marques', 'Machado', 'Mendes', 'Freitas'];
$empresas = [
    ['Distribuidora Horizonte LTDA', 'Material de escritório'],
    ['Escola Pequeno Saber LTDA', 'Mensalidade escolar'],
    ['Condomínio Residencial Ipê Amarelo', 'Taxa condominial'],
    ['Academia Corpo em Movimento ME', 'Plano mensal academia'],
    ['Clínica Odontológica Sorriso LTDA', 'Tratamento odontológico'],
    ['Faculdade Integrada do Planalto', 'Mensalidade graduação'],
    ['Provedor NetRápido Telecom LTDA', 'Internet fibra 500 Mbps'],
    ['Imobiliária Casa Nova LTDA', 'Aluguel residencial'],
    ['Associação dos Moradores do Bairro Jardim', 'Contribuição associativa'],
    ['Loja de Móveis Bom Lar EIRELI', 'Parcela de móveis planejados'],
    ['Auto Peças Estrada Real LTDA', 'Peças automotivas'],
    ['Seguradora Proteção Total S.A.', 'Seguro residencial'],
    ['Contabilidade Exata Serviços LTDA', 'Honorários contábeis'],
    ['Editora Saber Mais LTDA', 'Assinatura de revista'],
    ['Cooperativa Agro Vale Verde', 'Insumos agrícolas'],
];
$cidades = [
    ['Brasília', 'DF', '70'], ['Goiânia', 'GO', '74'], ['São Paulo', 'SP', '01'], ['Campinas', 'SP', '13'],
    ['Rio de Janeiro', 'RJ', '20'], ['Belo Horizonte', 'MG', '30'], ['Uberlândia', 'MG', '38'],
    ['Curitiba', 'PR', '80'], ['Porto Alegre', 'RS', '90'], ['Florianópolis', 'SC', '88'],
    ['Salvador', 'BA', '40'], ['Recife', 'PE', '50'], ['Fortaleza', 'CE', '60'], ['Belém', 'PA', '66'],
    ['Manaus', 'AM', '69'], ['Cuiabá', 'MT', '78'], ['Campo Grande', 'MS', '79'], ['Vitória', 'ES', '29'],
    ['Natal', 'RN', '59'], ['São Luís', 'MA', '65'],
];
$logradouros = ['Rua das Flores', 'Avenida Brasil', 'Rua Sete de Setembro', 'Avenida Getúlio Vargas',
    'Rua Tiradentes', 'Rua São João', 'Avenida Paulista', 'Rua XV de Novembro', 'Quadra 104 Conjunto B',
    'Rua Dom Pedro II', 'Avenida Rio Branco', 'Rua Marechal Deodoro', 'Travessa da Paz', 'Alameda dos Ipês'];
$instrucoesPossiveis = [
    'Após o vencimento cobrar multa de 2%%.',
    'Após o vencimento cobrar juros de 0,033%% ao dia.',
    'Não receber após %s.',
    'Conceder desconto de R$ %s até o vencimento.',
    'Sr. Caixa, não receber em cheque.',
    'Em caso de dúvidas, entre em contato com o beneficiário.',
    'Protestar após 10 dias corridos do vencimento.',
];

function pick(array $a) { return $a[mt_rand(0, count($a) - 1)]; }
function digits(int $n): string { $s = ''; for ($i = 0; $i < $n; $i++) $s .= mt_rand(0, 9); return $s; }

function cpf(): string {
    $n = array_map('intval', str_split(digits(9)));
    for ($t = 9; $t < 11; $t++) {
        $s = 0;
        for ($i = 0; $i < $t; $i++) $s += $n[$i] * (($t + 1) - $i);
        $n[$t] = ((10 * $s) % 11) % 10;
    }
    $c = implode('', $n);
    return substr($c, 0, 3) . '.' . substr($c, 3, 3) . '.' . substr($c, 6, 3) . '-' . substr($c, 9, 2);
}

function cnpj(): string {
    $n = array_map('intval', str_split(digits(8) . '0001'));
    foreach ([[5,4,3,2,9,8,7,6,5,4,3,2], [6,5,4,3,2,9,8,7,6,5,4,3,2]] as $pesos) {
        $s = 0;
        foreach ($pesos as $i => $p) $s += $n[$i] * $p;
        $r = $s % 11;
        $n[] = $r < 2 ? 0 : 11 - $r;
    }
    $c = implode('', $n);
    return substr($c, 0, 2) . '.' . substr($c, 2, 3) . '.' . substr($c, 5, 3) . '/' . substr($c, 8, 4) . '-' . substr($c, 12, 2);
}

function endereco(array $logradouros, array $cidades): array {
    [$cidade, $uf, $cepPrefixo] = pick($cidades);
    $end = pick($logradouros) . ', ' . mt_rand(10, 2999);
    if (mt_rand(0, 2) === 0) $end .= ' - Apto ' . mt_rand(101, 1504);
    $cep = $cepPrefixo . digits(3) . '-' . digits(3);
    return [$end, $cep, $cidade, $uf];
}

function dinheiro(float $v): string { return number_format($v, 2, ',', '.'); }

$bancos = [
    'BancoDoBrasil' => fn() => ['agencia' => mt_rand(1000, 9999), 'agenciaDv' => mt_rand(0, 9), 'carteira' => 18,
        'conta' => (int) digits(8), 'contaDv' => mt_rand(0, 9), 'convenio' => (int) ('1' . digits(6)), 'sequencial' => (int) digits(7)],
    'Bradesco' => fn() => ['agencia' => mt_rand(1000, 9999), 'agenciaDv' => mt_rand(0, 9), 'carteira' => pick([6, 9]),
        'conta' => mt_rand(100000, 9999999), 'contaDv' => mt_rand(0, 9), 'sequencial' => (int) digits(9)],
    'Itau' => fn() => ['agencia' => mt_rand(1000, 9999), 'carteira' => 109, 'conta' => mt_rand(10000, 99999),
        'contaDv' => mt_rand(0, 9), 'sequencial' => mt_rand(10000000, 99999999)],
    'Caixa' => fn() => ['agencia' => (string) mt_rand(1000, 9999), 'carteira' => 'RG',
        'conta' => (string) mt_rand(100000, 999999), 'contaDv' => mt_rand(0, 9), 'sequencial' => (int) digits(7)],
    'Santander' => fn() => ['agencia' => mt_rand(1000, 9999), 'carteira' => 101, 'conta' => mt_rand(1000000, 9999999),
        'ios' => '0', 'sequencial' => (int) digits(10)],
    'Sicoob' => fn() => ['agencia' => mt_rand(1000, 9999), 'carteira' => '1', 'modalidade' => '01',
        'conta' => mt_rand(10000, 999999), 'convenio' => mt_rand(10000, 99999), 'sequencial' => (string) mt_rand(1000, 999999)],
];
$codigosBanco = ['BancoDoBrasil' => '001', 'Bradesco' => '237', 'Itau' => '341', 'Caixa' => '104', 'Santander' => '033', 'Sicoob' => '756'];
$nomesBanco = ['BancoDoBrasil' => 'Banco do Brasil', 'Bradesco' => 'Bradesco', 'Itau' => 'Itaú', 'Caixa' => 'Caixa Econômica Federal', 'Santander' => 'Santander', 'Sicoob' => 'Sicoob'];

@mkdir($outDir . '/html', 0775, true);
$gabarito = [];
$chavesBanco = array_keys($bancos);

for ($i = 1; $i <= $total; $i++) {
    $bancoClasse = $chavesBanco[($i - 1) % count($chavesBanco)];
    $classe = 'OpenBoleto\\Banco\\' . $bancoClasse;

    $pagNome = pick($nomes) . ' ' . pick($sobrenomes) . ' ' . pick($sobrenomes);
    $pagDoc = cpf();
    [$pagEnd, $pagCep, $pagCid, $pagUf] = endereco($logradouros, $cidades);

    [$benNome, $descricao] = pick($empresas);
    $benDoc = cnpj();
    [$benEnd, $benCep, $benCid, $benUf] = endereco($logradouros, $cidades);

    $valor = round(mt_rand(1500, 450000) / 100, 2);
    $dataDoc = (new DateTime('2024-06-01'))->modify('+' . mt_rand(0, 900) . ' days');
    $dataVenc = (clone $dataDoc)->modify('+' . mt_rand(5, 45) . ' days');
    $numeroDoc = (string) mt_rand(100000, 9999999);

    $desconto = mt_rand(1, 10) <= 6 ? round($valor * mt_rand(2, 15) / 100, 2) : 0.0;
    $valorCobrado = round($valor - $desconto, 2);

    $instrucoes = [];
    foreach ((array) array_rand($instrucoesPossiveis, mt_rand(2, 4)) as $k) {
        $tpl = $instrucoesPossiveis[$k];
        $instrucoes[] = str_contains($tpl, 'Não receber')
            ? sprintf($tpl, (clone $dataVenc)->modify('+30 days')->format('d/m/Y'))
            : (str_contains($tpl, 'desconto') ? sprintf($tpl, dinheiro(round($valor * 0.05, 2))) : sprintf($tpl));
    }
    $demonstrativo = [$descricao . ' - ref. ' . $dataDoc->format('m/Y'), 'Documento nº ' . $numeroDoc];

    $params = array_merge($bancos[$bancoClasse](), [
        'dataVencimento' => $dataVenc,
        'dataDocumento' => $dataDoc,
        'dataProcessamento' => $dataDoc,
        'valor' => $valor,
        'descontosAbatimentos' => $desconto,
        'valorCobrado' => $valorCobrado,
        'numeroDocumento' => $numeroDoc,
        'sacado' => new Agente($pagNome, $pagDoc, $pagEnd, $pagCep, $pagCid, $pagUf),
        'cedente' => new Agente($benNome, $benDoc, $benEnd, $benCep, $benCid, $benUf),
        'descricaoDemonstrativo' => $demonstrativo,
        'instrucoes' => $instrucoes,
    ]);

    $boleto = new $classe($params);
    $id = sprintf('boleto_%03d', $i);
    file_put_contents("$outDir/html/$id.html", $boleto->getOutput());

    $gabarito[] = [
        'id' => $id,
        'arquivo_html' => "html/$id.html",
        'banco' => ['nome' => $nomesBanco[$bancoClasse], 'codigo' => $codigosBanco[$bancoClasse]],
        'linha_digitavel' => $boleto->getLinhaDigitavel(),
        'linha_digitavel_numeros' => preg_replace('/\D/', '', $boleto->getLinhaDigitavel()),
        'codigo_barras' => $boleto->getNumeroFebraban(),
        'valor_documento' => $valor,
        'valor_documento_formatado' => 'R$ ' . dinheiro($valor),
        'desconto_abatimento' => $desconto,
        'desconto_abatimento_impresso' => $desconto > 0 ? dinheiro($desconto) : null,
        'valor_cobrado' => $valorCobrado,
        'valor_cobrado_formatado' => 'R$ ' . dinheiro($valorCobrado),
        'data_vencimento' => $dataVenc->format('Y-m-d'),
        'data_documento' => $dataDoc->format('Y-m-d'),
        'numero_documento' => $numeroDoc,
        'nosso_numero' => $boleto->getNossoNumero(),
        'agencia_codigo_beneficiario' => $boleto->getAgenciaCodigoCedente(),
        'beneficiario' => ['nome' => $benNome, 'cnpj' => $benDoc, 'endereco' => $benEnd, 'cep' => $benCep, 'cidade' => $benCid, 'uf' => $benUf],
        'pagador' => ['nome' => $pagNome, 'cpf' => $pagDoc, 'endereco' => $pagEnd, 'cep' => $pagCep, 'cidade' => $pagCid, 'uf' => $pagUf],
        'demonstrativo' => $demonstrativo,
        'instrucoes' => $instrucoes,
    ];
}

file_put_contents("$outDir/gabarito.json", json_encode([
    'descricao' => 'Boletos sintéticos (dados fictícios) gerados com OpenBoleto para teste de OCR/PLN',
    'semente' => $seed,
    'quantidade' => $total,
    'boletos' => $gabarito,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));

echo "Gerados $total boletos em $outDir\n";
