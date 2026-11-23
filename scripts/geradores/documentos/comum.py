"""Dados fictícios e utilitários comuns aos geradores (CPF e CNPJ com DV válido, inventados).
"""
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

FUSO_BR = timezone(timedelta(hours=-3))

NOMES = ["Ana", "João", "Maria", "José", "Francisca", "Antônio", "Juliana", "Carlos", "Patrícia", "Paulo",
         "Aline", "Lucas", "Fernanda", "Rafael", "Camila", "Marcos", "Beatriz", "Gustavo", "Letícia", "Thiago",
         "Luíza", "Pedro", "Gabriela", "Matheus", "Vitória", "Felipe", "Larissa", "Rodrigo", "Débora", "Sérgio"]
SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima",
              "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes",
              "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques",
              "Machado", "Mendes", "Freitas"]
PREFIXOS_EMPRESA = ["Comercial", "Distribuidora", "Atacadista", "Indústria", "Mercado", "Supermercado",
                    "Papelaria", "Farmácia", "Auto Peças", "Materiais de Construção", "Eletro", "Casa",
                    "Padaria", "Empório", "Agropecuária"]
NUCLEOS_EMPRESA = ["Horizonte", "Bom Preço", "Ipê", "Planalto", "Estrela", "Aurora", "Vale Verde", "Central",
                   "São Jorge", "Primavera", "Boa Vista", "Cerrado", "Litoral", "Serra Azul", "Nova Era"]
SUFIXOS_EMPRESA = ["LTDA", "LTDA", "ME", "EIRELI", "S.A.", "EPP"]
SERVICOS_EMPRESA = [
    ("Consultoria Contábil", "17.19", "171901", "Serviços de contabilidade"),
    ("Tecnologia e Sistemas", "1.07", "010701", "Suporte técnico em informática"),
    ("Publicidade e Marketing", "17.06", "170601", "Propaganda e publicidade"),
    ("Engenharia e Projetos", "7.03", "070301", "Elaboração de projetos de engenharia"),
    ("Limpeza e Conservação", "7.10", "071001", "Limpeza, manutenção e conservação de imóveis"),
    ("Advocacia Associados", "17.14", "171401", "Advocacia"),
    ("Treinamentos Profissionais", "8.02", "080201", "Instrução, treinamento e capacitação"),
    ("Manutenção Predial", "7.05", "070501", "Reparação e manutenção de edifícios"),
    ("Clínica Odontológica", "4.12", "041201", "Odontologia"),
    ("Transportes e Logística", "16.02", "160201", "Transporte municipal de cargas"),
]

# (cidade, UF, código IBGE do município, código IBGE da UF, prefixo de CEP, bairros)
CIDADES = [
    ("Brasília", "DF", "5300108", "53", "70", ["Asa Sul", "Asa Norte", "Lago Sul", "Sudoeste"]),
    ("Goiânia", "GO", "5208707", "52", "74", ["Setor Bueno", "Setor Oeste", "Setor Marista", "Jardim Goiás"]),
    ("São Paulo", "SP", "3550308", "35", "01", ["Bela Vista", "Pinheiros", "Moema", "Tatuapé"]),
    ("Campinas", "SP", "3509502", "35", "13", ["Cambuí", "Taquaral", "Barão Geraldo", "Centro"]),
    ("Rio de Janeiro", "RJ", "3304557", "33", "20", ["Copacabana", "Tijuca", "Botafogo", "Méier"]),
    ("Belo Horizonte", "MG", "3106200", "31", "30", ["Savassi", "Funcionários", "Pampulha", "Lourdes"]),
    ("Uberlândia", "MG", "3170206", "31", "38", ["Santa Mônica", "Centro", "Tibery", "Jardim Karaíba"]),
    ("Curitiba", "PR", "4106902", "41", "80", ["Batel", "Água Verde", "Centro Cívico", "Portão"]),
    ("Porto Alegre", "RS", "4314902", "43", "90", ["Moinhos de Vento", "Menino Deus", "Cidade Baixa", "Petrópolis"]),
    ("Florianópolis", "SC", "4205407", "42", "88", ["Trindade", "Centro", "Itacorubi", "Coqueiros"]),
    ("Salvador", "BA", "2927408", "29", "40", ["Barra", "Pituba", "Rio Vermelho", "Itaigara"]),
    ("Recife", "PE", "2611606", "26", "50", ["Boa Viagem", "Casa Forte", "Graças", "Espinheiro"]),
    ("Fortaleza", "CE", "2304400", "23", "60", ["Aldeota", "Meireles", "Fátima", "Cocó"]),
    ("Belém", "PA", "1501402", "15", "66", ["Nazaré", "Umarizal", "Batista Campos", "Marco"]),
    ("Manaus", "AM", "1302603", "13", "69", ["Adrianópolis", "Centro", "Ponta Negra", "Flores"]),
    ("Cuiabá", "MT", "5103403", "51", "78", ["Goiabeiras", "Duque de Caxias", "Centro Norte", "Jardim Itália"]),
    ("Campo Grande", "MS", "5002704", "50", "79", ["Centro", "Jardim dos Estados", "Santa Fé", "Carandá Bosque"]),
    ("Vitória", "ES", "3205309", "32", "29", ["Praia do Canto", "Jardim Camburi", "Centro", "Bento Ferreira"]),
    ("Natal", "RN", "2408102", "24", "59", ["Petrópolis", "Tirol", "Lagoa Nova", "Capim Macio"]),
    ("São Luís", "MA", "2111300", "21", "65", ["Renascença", "Calhau", "Centro", "Cohama"]),
]
LOGRADOUROS = ["Rua das Flores", "Avenida Brasil", "Rua Sete de Setembro", "Avenida Getúlio Vargas",
               "Rua Tiradentes", "Rua São João", "Avenida Paulista", "Rua XV de Novembro", "Rua Dom Pedro II",
               "Avenida Rio Branco", "Rua Marechal Deodoro", "Travessa da Paz", "Alameda dos Ipês",
               "Rua Santos Dumont", "Avenida Independência", "Rua Barão do Rio Branco"]

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
         "outubro", "novembro", "dezembro"]


@dataclass
class Endereco:
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    uf: str
    cod_municipio: str
    cod_uf: str
    cep: str

    @property
    def cep_formatado(self) -> str:
        return f"{self.cep[:5]}-{self.cep[5:]}"


@dataclass
class Pessoa:
    nome: str
    documento: str
    endereco: Endereco
    ie: str | None = None
    fone: str = ""
    email: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def eh_cnpj(self) -> bool:
        return len(self.documento) == 14

    @property
    def documento_formatado(self) -> str:
        return formatar_cnpj(self.documento) if self.eh_cnpj else formatar_cpf(self.documento)

    def gabarito(self) -> dict:
        return {
            "nome": self.nome,
            "tipo_documento": "CNPJ" if self.eh_cnpj else "CPF",
            "documento": self.documento_formatado,
            "documento_numeros": self.documento,
            "endereco": f"{self.endereco.logradouro}, {self.endereco.numero}",
            "bairro": self.endereco.bairro,
            "cidade": self.endereco.cidade,
            "uf": self.endereco.uf,
            "cep": self.endereco.cep_formatado,
        }


class Gerador:

    def __init__(self, semente: int):
        self.rng = random.Random(semente)

    def escolher(self, seq):
        return self.rng.choice(seq)

    def digitos(self, n: int) -> str:
        return "".join(str(self.rng.randint(0, 9)) for _ in range(n))

    def cpf(self) -> str:
        n = [self.rng.randint(0, 9) for _ in range(9)]
        for t in (9, 10):
            s = sum(n[i] * (t + 1 - i) for i in range(t))
            n.append((s * 10 % 11) % 10)
        return "".join(map(str, n))

    def cnpj(self) -> str:
        n = [self.rng.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
        for pesos in ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]):
            r = sum(a * b for a, b in zip(n, pesos)) % 11
            n.append(0 if r < 2 else 11 - r)
        return "".join(map(str, n))

    def endereco(self, cidade=None) -> Endereco:
        c = cidade or self.escolher(CIDADES)
        return Endereco(
            logradouro=self.escolher(LOGRADOUROS),
            numero=str(self.rng.randint(10, 2999)),
            bairro=self.escolher(c[5]),
            cidade=c[0], uf=c[1], cod_municipio=c[2], cod_uf=c[3],
            cep=c[4] + self.digitos(6),
        )

    def nome_pessoa(self) -> str:
        return f"{self.escolher(NOMES)} {self.escolher(SOBRENOMES)} {self.escolher(SOBRENOMES)}"

    def nome_empresa(self, nucleo_servico: str | None = None) -> str:
        if nucleo_servico:
            return f"{self.escolher(SOBRENOMES)} {nucleo_servico} {self.escolher(SUFIXOS_EMPRESA)}"
        return f"{self.escolher(PREFIXOS_EMPRESA)} {self.escolher(NUCLEOS_EMPRESA)} {self.escolher(SUFIXOS_EMPRESA)}"

    def fone(self, endereco: Endereco) -> str:
        return str(self.rng.randint(11, 99)) + "9" + self.digitos(8)

    def email(self, nome: str) -> str:
        base = "".join(ch for ch in nome.lower().split()[0] if ch.isascii() and ch.isalpha()) or "contato"
        return f"{base}{self.rng.randint(1, 99)}@exemplo.com.br"

    def empresa(self, cidade=None, nucleo_servico=None) -> Pessoa:
        nome = self.nome_empresa(nucleo_servico)
        end = self.endereco(cidade)
        return Pessoa(nome, self.cnpj(), end, ie=self.digitos(9), fone=self.fone(end),
                      email=self.email(nome.split()[0]))

    def pessoa_fisica(self, cidade=None) -> Pessoa:
        nome = self.nome_pessoa()
        end = self.endereco(cidade)
        return Pessoa(nome, self.cpf(), end, fone=self.fone(end), email=self.email(nome))

    def pessoa_ou_empresa(self, prob_empresa=0.5, cidade=None) -> Pessoa:
        return self.empresa(cidade) if self.rng.random() < prob_empresa else self.pessoa_fisica(cidade)

    def data_hora(self, inicio="2024-06-01", dias=900) -> datetime:
        base = datetime.fromisoformat(inicio).replace(tzinfo=FUSO_BR)
        return base + timedelta(days=self.rng.randint(0, dias), hours=self.rng.randint(8, 19),
                                minutes=self.rng.randint(0, 59), seconds=self.rng.randint(0, 59))


def formatar_cpf(d: str) -> str:
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def formatar_cnpj(d: str) -> str:
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def dinheiro(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_extenso(d) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def dv_mod11_chave(numeros: str) -> int:
    soma, peso = 0, 2
    for d in reversed(numeros):
        soma += int(d) * peso
        peso = 2 if peso == 9 else peso + 1
    r = soma % 11
    return 0 if r < 2 else 11 - r
