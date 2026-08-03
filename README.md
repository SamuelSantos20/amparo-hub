# Call Data ETL Pipeline

Pipeline demonstrativo em Python para extrair registros de chamadas de uma API, normalizar a resposta e carregar os dados em PostgreSQL ou Supabase.

> Este repositório é uma versão de portfólio. Endereços, credenciais, nomes e dados reais foram removidos. O modo mock usa somente informações fictícias.

## Funcionalidades

- consulta registros por data;
- processa automaticamente o dia anterior;
- permite reprocessar um intervalo;
- normaliza o JSON recebido;
- executa carga em lote no PostgreSQL;
- usa `ON CONFLICT ... DO UPDATE` para evitar duplicidades;
- oferece modo mock sem chamada à API externa;
- permite execução manual pelo GitHub Actions.

## Tecnologias

- Python 3.11+
- Requests
- PostgreSQL / Supabase
- psycopg2
- python-dotenv
- Pytest
- uv
- GitHub Actions

## Estrutura

```text
.
├── .github/workflows/extrato_diario.yml
├── sql/schema_chamadas_v2.sql
├── src/etl/
│   ├── extrato_supabase.py
│   └── extrato_supabase_mock.py
├── tests/test_extrato.py
├── pyproject.toml
└── requirements.txt
```

## Configuração

Crie um arquivo `.env` local na raiz do projeto e preencha apenas com credenciais próprias e autorizadas:

```env
API_URL=https://api.exemplo.com/extrato
API_USER=seu_usuario
API_PWD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha_local
DB_NAME=postgres
```

O arquivo `.env` é ignorado pelo Git e nunca deve ser versionado.

## Banco de dados

Aplique o schema antes da primeira carga:

```bash
psql "$DATABASE_URL" -f sql/schema_chamadas_v2.sql
```

O schema cria a tabela `chamadas` e índices para data, protocolo, telefone, agente, fila e evento.

## Instalação

Com `uv`:

```bash
uv sync
```

Ou com `pip`:

```bash
python -m venv .venv
pip install -r requirements.txt
```

## Execução

Modo real, processando o dia anterior:

```bash
uv run python src/etl/extrato_supabase.py
```

Reprocessamento a partir de uma data:

```bash
uv run python src/etl/extrato_supabase.py 2026-07-01
```

Modo demonstrativo com dados fictícios:

```bash
uv run python src/etl/extrato_supabase_mock.py
```

## Testes

```bash
uv run pytest
```

## GitHub Actions

O workflow pode ser iniciado manualmente em modo `mock` ou `real`. O agendamento automático permanece desativado na versão de portfólio para evitar chamadas e inserções não intencionais.

No modo real, configure as credenciais exclusivamente em **GitHub Actions Secrets**.

## Segurança

- nenhuma credencial real deve ser incluída no código;
- o endpoint deve ser informado por variável de ambiente;
- o modo mock não acessa a API externa;
- os dados fictícios não representam pessoas ou clientes reais;
- credenciais usadas em ambientes anteriores devem ser revogadas antes de publicar o projeto.

## Licença

MIT.
