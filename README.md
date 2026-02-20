# Filmow → Letterboxd CSV (2026)

Converte sua lista de filmes “já vi” do Filmow em arquivos CSV compatíveis com importação no Letterboxd.

> Script baseado em: https://github.com/yanari/filmow_to_letterboxd

## Como funciona

O script [parser_filmow.py](parser_filmow.py) usa a classe [`Parser`](parser_filmow.py) para:

- Ler todas as páginas de filmes já vistos do usuário no Filmow
- Extrair:
  - **Title**
  - **Directors**
  - **Year**
  - **Rating**
- Gerar arquivos CSV no formato de importação do Letterboxd:
  - delimitador `,` (vírgula)
  - codificação UTF-8
  - escaping de aspas com `\` dentro de campos com texto
  - divisão automática em múltiplos arquivos para respeitar o limite de **1MB por arquivo**
  - Exemplo: [1johndoe.csv](1johndoe.csv)

## Requisitos

- Python **3.10**, **3.11** ou **3.12**
- Dependências em [requirements.txt](requirements.txt):
  - beautifulsoup4
  - requests
  - pandas
  - regex

## Instalação rápida (Linux)

Use o script [init.sh](init.sh):

```bash
cd Downloads
git clone https://github.com/geraldohomero/filmow2letterboxd
cd filmow2letterboxd
chmod +x init.sh
./init.sh
```

Esse script:

1. Instala Python/pip (apt ou dnf)
2. Cria ambiente virtual `.venv`
3. Instala dependências
4. Executa o parser

## Execução manual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python parser_filmow.py
```

Ao executar, informe seu usuário do Filmow quando solicitado.

## Saída

Os CSVs serão gerados na raiz do projeto, com nomes no formato:

- `1<usuario>.csv`
- `2<usuario>.csv`
- ...

## Importar no Letterboxd

1. Acesse: https://letterboxd.com/import/
2. Clique em **SELECT A FILE**
3. Selecione o CSV gerado
4. Conclua a importação

## Observações

- O projeto depende da estrutura HTML atual do Filmow; mudanças no site podem exigir ajustes no parser.
- O arquivo [.gitignore](.gitignore) ignora `*.csv` e `.venv/`.
