# ZenMoney — Arquitetura do Projeto (v2)

> Sistema de gestão financeira com inteligência emocional, construído seguindo os princípios de **MVC em Camadas** com boas práticas de organização e nomenclatura.

---

## Princípios Fundamentais

1. **Separação de responsabilidades** — Cada camada tem uma única função e não invade a outra.
2. **Fluxo unidirecional** — Uma requisição sempre percorre o caminho: `Router → Service → Model → Banco`.
3. **Simplicidade primeiro** — Nenhuma abstração é criada antes de ser necessária.
4. **Service como centro** — Toda lógica de negócio vive nos services, nunca nos routers ou models.

---

## Backend (FastAPI + Python)

### Estrutura de Pastas

```
backend/
├── main.py                  # Ponto de entrada — registra os routers e inicia o app
├── database.py              # Conexão com o banco e criação das tabelas
│
├── models/                  # Camada de dados — representa as tabelas do banco (SQLAlchemy)
│   ├── user.py
│   ├── transaction.py
│   ├── category.py
│   └── recurrence.py
│
├── schemas/                 # Validação de dados de entrada e saída (Pydantic)
│   ├── user.py
│   ├── transaction.py
│   └── category.py
│
├── routers/                 # Camada de rotas — define os endpoints da API
│   ├── auth.py
│   ├── transactions.py
│   ├── categories.py
│   ├── reports.py
│   └── settings.py
│
├── services/                # Camada de negócio — toda a inteligência do sistema
│   ├── auth_service.py
│   ├── transaction_service.py
│   ├── alert_service.py
│   ├── report_service.py
│   └── prediction_service.py
│
└── utils/                   # Funções auxiliares reutilizáveis
    ├── security.py          # Hash de senha e geração de tokens JWT
    └── date_utils.py        # Fuso horário de Brasília e formatação de datas
```

### Detalhamento das Camadas

#### `models/` — Representação do banco

Contém as classes SQLAlchemy que mapeiam diretamente para as tabelas do banco de dados. Sem lógica de negócio.

| Arquivo | Responsabilidade |
|---|---|
| `user.py` | Tabela de usuários (nome, e-mail, senha hash) |
| `transaction.py` | Tabela de transações (valor, tipo, data, emoção, categoria) |
| `category.py` | Tabela de categorias e subcategorias |
| `recurrence.py` | Tabela de transações recorrentes agendadas |

#### `schemas/` — Validação com Pydantic

Define o formato esperado dos dados que entram e saem da API. O FastAPI usa esses schemas automaticamente para validar e documentar os endpoints.

| Arquivo | Schemas definidos |
|---|---|
| `user.py` | `UserCreate`, `UserLogin`, `UserResponse` |
| `transaction.py` | `TransactionCreate`, `TransactionUpdate`, `TransactionResponse` |
| `category.py` | `CategoryCreate`, `CategoryResponse` |

#### `routers/` — Endpoints da API

Cada arquivo agrupa os endpoints de um domínio. O router apenas recebe a requisição, chama o service correspondente e retorna a resposta. **Nenhuma lógica de negócio aqui.**

| Arquivo | Endpoints |
|---|---|
| `auth.py` | `POST /register`, `POST /login`, `POST /logout` |
| `transactions.py` | `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |
| `categories.py` | `POST /`, `GET /`, `PUT /{id}`, `DELETE /{id}` |
| `reports.py` | `GET /summary`, `GET /by-emotion`, `GET /by-category` |
| `settings.py` | `GET /budget`, `PUT /budget`, `GET /profile`, `PUT /profile` |

#### `services/` — Regras de negócio

O coração do sistema. Cada service concentra a inteligência de um domínio, recebendo dados validados dos routers e interagindo com os models.

| Arquivo | Responsabilidade |
|---|---|
| `auth_service.py` | Login, cadastro, bloqueio por tentativas, expiração de sessão |
| `transaction_service.py` | CRUD de transações, recálculo de saldo, recorrências |
| `alert_service.py` | Monitoramento do teto de gastos, disparo de alertas, modo sobrevivência |
| `report_service.py` | Geração de dados para gráficos, cruzamento emoção x gasto, gatilhos |
| `prediction_service.py` | Previsão de saldo baseada na média dos últimos 3 meses |

#### `utils/` — Auxiliares

| Arquivo | Responsabilidade |
|---|---|
| `security.py` | Hash bcrypt de senhas, geração e validação de tokens JWT |
| `date_utils.py` | Conversão para fuso de Brasília, formatação `DD/MM/AAAA` |

---

## Frontend (Next.js + TypeScript)

### Estrutura de Pastas

```
frontend/src/
├── app/                        # Next.js App Router — páginas e rotas
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   └── (dashboard)/
│       ├── transactions/
│       ├── reports/
│       └── settings/
│
├── components/                 # Componentes React reutilizáveis
│   ├── ui/                     # Elementos genéricos (botão, input, card, modal)
│   ├── layout/                 # Estrutura de página (sidebar, header, menu)
│   └── features/               # Componentes específicos de cada tela
│       ├── transactions/
│       ├── reports/
│       └── settings/
│
├── contexts/                   # React Contexts para estado global
│   └── AuthContext.tsx         # Token JWT, usuário logado, proteção de rotas
│
├── services/                   # Chamadas à API do backend (fetch/axios)
│   ├── auth.service.ts
│   ├── transaction.service.ts
│   ├── category.service.ts
│   └── report.service.ts
│
├── types/                      # Interfaces e tipos TypeScript
│   ├── transaction.ts
│   ├── category.ts
│   └── user.ts
│
└── utils/                      # Funções auxiliares
    ├── formatCurrency.ts       # Formatação em R$ com pontos e vírgulas (RNF05)
    └── formatDate.ts           # Formatação DD/MM/AAAA no fuso de Brasília (RNF09)
```

---

## Fluxo de uma Requisição

### Backend: Registrar uma Transação

```
1. POST /api/transactions
   └── routers/transactions.py             (recebe e valida com schema)
       └── services/transaction_service.py (aplica regras de negócio)
           └── services/alert_service.py   (verifica teto de gastos)
               └── models/transaction.py   (persiste no banco)
```

### Frontend: Exibir lista de transações

```
1. Usuário acessa /dashboard/transactions
   └── app/(dashboard)/transactions/page.tsx    (página Next.js)
       └── components/features/transactions/    (componente de lista)
           └── services/transaction.service.ts  (chama a API)
               └── GET /api/transactions        (backend responde)
```

---

## Regras de Código

### Permitido

- `routers/` importa de `schemas/` e chama `services/`
- `services/` importa de `models/` e `utils/`
- `models/` importa apenas de `database.py`
- `utils/` não importa nenhuma outra camada do projeto

### Proibido

- `routers/` **NUNCA** importa de `models/` diretamente
- `models/` **NUNCA** importa de `services/`
- `utils/` **NUNCA** importa de `routers/`, `services/` ou `models/`

---

## Convenções de Nomenclatura

| Item | Backend (Python) | Frontend (TypeScript) |
|---|---|---|
| Arquivos | `snake_case.py` | `PascalCase.tsx` (componentes), `camelCase.ts` (utils/services) |
| Classes | `PascalCase` | `PascalCase` |
| Funções | `snake_case` | `camelCase` |
| Interfaces TypeScript | — | `PascalCase` (ex: `Transaction`, `Category`) |
| Pastas | `snake_case` | `kebab-case` |

---

## Banco de Dados

- **Desenvolvimento:** SQLite (sem instalação, arquivo local)
- **ORM:** SQLAlchemy
- **Criação de tabelas:** `Base.metadata.create_all(bind=engine)` no `database.py`

---

## Bibliotecas Essenciais

| Finalidade | Biblioteca |
|---|---|
| API | `fastapi`, `uvicorn` |
| Banco de dados | `sqlalchemy` |
| Validação | `pydantic` |
| Autenticação | `python-jose`, `passlib[bcrypt]` |
| Datas | `zoneinfo` (stdlib Python 3.9+) |
