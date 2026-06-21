# ZenMoney

ZenMoney é uma aplicação web de controle financeiro pessoal. O sistema permite registrar receitas e despesas, acompanhar saldo, organizar transações por categoria, associar emoções aos lançamentos, configurar limites de gastos, criar recorrências e consultar relatórios financeiros.

## Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT
- Pytest

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Recharts

## Estrutura

```text
zenmoney/
├── backend/   # API, banco de dados, regras de negócio e testes
├── frontend/  # interface web
├── .gitignore
└── README.md
```

## Pré-requisitos

- Python 3.11 ou superior
- Node.js 20 ou superior
- npm
- Git

## Configuração do backend

Entre na pasta do backend:

```bash
cd backend
```

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o arquivo de variáveis de ambiente:

```bash
copy .env.example .env
```

Inicie a API:

```bash
uvicorn main:app --reload
```

Endereços principais:

- API: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`
- Documentação da API: `http://127.0.0.1:8000/docs`

## Configuração do frontend

Em outro terminal, entre na pasta do frontend:

```bash
cd frontend
```

Instale as dependências:

```bash
npm install
```

Crie ou confira o arquivo `.env.local` com a URL da API:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
```

Inicie a interface web:

```bash
npm run dev
```

A aplicação ficará disponível em:

```text
http://localhost:3000
```

## Testes

Execute os testes do backend dentro da pasta `backend`, com o ambiente virtual ativo:

```bash
pytest
```

Para verificar o frontend:

```bash
npm run lint
```

## Funcionalidades

- Cadastro, login e logout
- Proteção de rotas autenticadas
- Bloqueio temporário após tentativas inválidas de login
- Registro de receitas e despesas
- Categorias financeiras
- Emoções associadas às transações
- Limites de gastos por categoria
- Alertas financeiros
- Transações recorrentes
- Relatórios e gráficos
- Previsão de saldo por período
- Configurações do usuário
- Exclusão definitiva da conta

## Variáveis de ambiente

O backend usa as variáveis definidas em `backend/.env.example`:

```text
APP_NAME=ZenMoney API
APP_VERSION=2.0.0
API_PREFIX=/api
DATABASE_URL=sqlite:///./zenmoney_v2.db
SECRET_KEY=change-me-in-development
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_MINUTES=15
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

O frontend usa a variável `NEXT_PUBLIC_API_BASE_URL` no arquivo `.env.local`.

## Banco de dados

O projeto utiliza SQLite. Em ambiente local, o banco é criado automaticamente pelo backend quando a API é iniciada.

O arquivo `.db` criado localmente não deve ser versionado.

## Observações

- Inicie o backend antes do frontend.
- Mantenha arquivos `.env`, `.env.local`, `.venv`, `node_modules`, `.next` e bancos `.db` fora do Git.
- Em produção, substitua `SECRET_KEY` por uma chave segura.

## Licença

Projeto desenvolvido para fins acadêmicos.

