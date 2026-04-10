# ZenMoney — Arquitetura do Projeto

> Sistema de gestão financeira com inteligência emocional, construído seguindo os princípios de **Clean Architecture**.

---

## Princípios Fundamentais

Este projeto segue a **Clean Architecture** (Robert C. Martin), onde:

1. **Regra de Dependência** — Dependências sempre apontam para dentro. Camadas externas dependem das internas, **nunca** o contrário.
2. **Domain** é o centro — Contém regras de negócio puras, sem dependência de framework.
3. **Application** orquestra — Coordena o fluxo entre entidades e infraestrutura via Use Cases.
4. **Infrastructure** implementa — Detalhes técnicos concretos (banco de dados, HTTP, etc.).
5. **Presentation** exibe — Interface com o usuário (API REST no backend, UI no frontend).

---

## Backend (FastAPI + Python)

### Estrutura de Pastas

```
backend/
├── app/
│   ├── domain/                     # Camada de Domínio
│   │   ├── entities/               # Entidades de negócio (classes Python puras)
│   │   ├── repositories/           # Interfaces abstratas (ABCs) dos repositórios
│   │   └── services/               # Serviços de domínio (lógica compartilhada)
│   │
│   ├── application/                # Camada de Aplicação
│   │   ├── use_cases/              # Casos de uso organizados por domínio
│   │   │   ├── transactions/       # CRUD e operações de transações
│   │   │   ├── categories/         # Operações de categorias
│   │   │   ├── budgets/            # Operações de orçamento
│   │   │   └── insights/           # Consultas analíticas
│   │   ├── dtos/                   # Data Transfer Objects (entrada/saída)
│   │   └── interfaces/             # Portas de saída (notificações, email, etc.)
│   │
│   ├── infrastructure/             # Camada de Infraestrutura
│   │   ├── database/
│   │   │   ├── models/             # Modelos ORM (SQLAlchemy)
│   │   │   └── repositories/       # Implementações concretas dos repositórios
│   │   └── services/               # Implementações de serviços externos
│   │
│   └── presentation/               # Camada de Apresentação
│       ├── api/
│       │   └── v1/                 # Endpoints versionados (FastAPI routers)
│       ├── schemas/                # Schemas Pydantic (request/response)
│       └── middleware/             # Middleware HTTP (error handling, logging)
│
└── tests/
    ├── unit/
    │   ├── domain/                 # Testes de entidades e regras de negócio
    │   └── application/            # Testes de use cases
    ├── integration/
    │   └── infrastructure/         # Testes de repositórios com DB real
    └── e2e/                        # Testes end-to-end da API
```

### Detalhamento das Camadas

#### `domain/` — O coração do sistema

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `entities/` | Classes puras que representam conceitos do negócio. Sem dependência de framework. | `Transaction`, `Category`, `Budget`, `User`, `Emotion` |
| `repositories/` | **Interfaces abstratas** (ABCs) que definem o contrato de acesso a dados. Nenhuma implementação aqui. | `TransactionRepository(ABC)` com métodos `create()`, `find_by_id()`, `list()` |
| `services/` | Lógica de negócio que envolve múltiplas entidades ou cálculos complexos. | `BudgetCalculator` — calcular se uma transação excede o orçamento |

#### `application/` — Orquestração

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `use_cases/` | Cada arquivo é um caso de uso com uma única responsabilidade. Recebe DTOs, usa entidades e repositórios. | `CreateTransactionUseCase` — valida dados, cria entidade, persiste via repositório |
| `dtos/` | Objetos simples que transportam dados entre camadas. Desacoplam a API do domínio. | `CreateTransactionDTO(amount, category_id, emotion_id, description)` |
| `interfaces/` | Portas de saída para serviços externos (email, notificação push, etc.). | `NotificationService(ABC)` com método `notify()` |

#### `infrastructure/` — Detalhes técnicos

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `database/models/` | Modelos ORM que mapeiam para tabelas do banco. | `TransactionModel(Base)` com colunas SQLAlchemy |
| `database/repositories/` | **Implementações concretas** das interfaces definidas em `domain/repositories/`. | `SQLAlchemyTransactionRepo` implementa `TransactionRepository` usando o ORM |
| `services/` | Implementações de serviços externos (email, SMS, etc.). | `EmailNotificationService` implementa `NotificationService` |

#### `presentation/` — Interface HTTP

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `api/v1/` | Routers FastAPI com os endpoints versionados. Cada arquivo agrupa endpoints de um domínio. | `transactions.py` com `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |
| `schemas/` | Schemas Pydantic para serialização/validação de requests e responses HTTP. | `TransactionCreateSchema`, `TransactionResponseSchema` |
| `middleware/` | Middleware global (tratamento de erros, CORS, logging). | `error_handler.py` — converte exceções de domínio em HTTP responses |

---

## Frontend (Next.js + TypeScript)

### Estrutura de Pastas

```
frontend/src/
├── app/                            # Next.js App Router (páginas e rotas)
│
├── domain/                         # Camada de Domínio
│   ├── entities/                   # Interfaces/tipos TypeScript das entidades
│   ├── repositories/               # Interfaces (contratos) dos repositórios
│   └── value-objects/              # Value Objects (Money, DateRange, etc.)
│
├── application/                    # Camada de Aplicação
│   ├── use-cases/                  # Casos de uso organizados por feature
│   │   ├── transactions/
│   │   ├── categories/
│   │   ├── budgets/
│   │   └── insights/
│   ├── dtos/                       # DTOs de comunicação entre camadas
│   └── mappers/                    # Conversão DTO ↔ Entity
│
├── infrastructure/                 # Camada de Infraestrutura
│   ├── http/                       # Cliente HTTP configurado (Axios/Fetch)
│   ├── repositories/               # Implementações concretas dos repositórios
│   └── storage/                    # Persistência local (localStorage, cookies)
│
├── presentation/                   # Camada de Apresentação (UI)
│   ├── components/
│   │   ├── ui/                     # Componentes genéricos reutilizáveis
│   │   ├── layout/                 # Componentes estruturais (Sidebar, Header)
│   │   └── features/               # Componentes específicos por feature
│   │       ├── transactions/
│   │       ├── budgets/
│   │       └── insights/
│   ├── hooks/                      # Custom hooks (conectam UI aos Use Cases)
│   ├── contexts/                   # React Contexts (Auth, Theme)
│   └── providers/                  # Providers de composição
│
├── shared/                         # Utilitários compartilhados
│   ├── utils/                      # Funções helper (formatCurrency, formatDate)
│   ├── constants/                  # Constantes globais
│   └── types/                      # Tipos TypeScript compartilhados
│
└── di/                             # Container de Injeção de Dependência
```

### Detalhamento das Camadas

#### `domain/` — Núcleo do negócio

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `entities/` | Interfaces TypeScript que definem a forma das entidades de negócio. | `Transaction { id, amount, type, category, emotion, date }` |
| `repositories/` | Interfaces que definem o contrato de acesso a dados. | `ITransactionRepository { create(), findById(), list(), delete() }` |
| `value-objects/` | Objetos imutáveis que encapsulam regras de formatação/validação. | `Money { amount, currency, format() }`, `DateRange { start, end }` |

#### `application/` — Lógica de aplicação

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `use-cases/` | Cada arquivo é um caso de uso. Recebe dados, aplica regras, chama repositório. | `CreateTransactionUseCase.execute(dto) → Transaction` |
| `dtos/` | Objetos de transporte de dados entre a UI e os use cases. | `CreateTransactionDTO { amount, categoryId, emotionId }` |
| `mappers/` | Funções de conversão entre DTOs (da API) e Entities (do domínio). | `TransactionMapper.toDomain(dto)`, `TransactionMapper.toDTO(entity)` |

#### `infrastructure/` — Comunicação externa

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `http/` | Configuração do cliente HTTP (base URL, interceptors, headers). | `api-client.ts` com Axios configurado, `interceptors.ts` para auth |
| `repositories/` | Implementações que chamam a API REST do backend. | `HttpTransactionRepository` implementa `ITransactionRepository` usando fetch/axios |
| `storage/` | Acesso a persistência local do navegador. | `local-storage.ts` — salvar preferências, tokens, cache |

#### `presentation/` — Interface do Usuário

| Pasta | Responsabilidade | Exemplo |
|-------|-----------------|---------|
| `components/ui/` | Componentes genéricos e reutilizáveis (design system). | `Button`, `Card`, `Modal`, `Input`, `Select`, `Badge`, `Skeleton` |
| `components/layout/` | Componentes de estrutura da página. | `Sidebar`, `Header`, `PageContainer` |
| `components/features/` | Componentes específicos de cada funcionalidade. | `TransactionList`, `TransactionForm`, `BudgetCard`, `EmotionBreakdown` |
| `hooks/` | Custom hooks que conectam os componentes aos use cases. | `useTransactions()` — chama `ListTransactionsUseCase`, gerencia state |
| `contexts/` | React Contexts para estado global. | `AuthContext` (autenticação), `ThemeContext` (dark/light mode) |
| `providers/` | Componentes que agrupam providers e injeção de dependência. | `AppProviders` — wrapa a app com todos os contexts e providers |

---

## Fluxo de uma Feature Completa

### Backend: Criar uma Transação

```
1. POST /api/v1/transactions
   └── presentation/api/v1/transactions.py        (recebe request)
       └── presentation/schemas/transaction.py     (valida com Pydantic)
           └── application/use_cases/create.py     (executa lógica)
               └── domain/entities/transaction.py  (cria entidade)
                   └── domain/repositories/        (interface abstrata)
                       └── infrastructure/database/repositories/  (persiste)
```

### Frontend: Listar Transações

```
1. Usuário acessa /dashboard/transactions
   └── app/(dashboard)/transactions/page.tsx         (página Next.js)
       └── presentation/hooks/useTransactions.ts     (custom hook)
           └── application/use-cases/list.ts         (use case)
               └── domain/repositories/ITransaction  (interface)
                   └── infrastructure/repositories/  (HTTP request)
                       └── infrastructure/http/      (axios/fetch)
```

---

## Regras de Código

### Permitido

- `domain/` pode ser importado por **qualquer** camada
- `application/` pode importar de `domain/`
- `infrastructure/` pode importar de `domain/` e `application/`
- `presentation/` pode importar de **qualquer** camada
- `shared/` pode ser importado por **qualquer** camada

### Proibido

- `domain/` **NUNCA** importa de `application/`, `infrastructure/` ou `presentation/`
- `application/` **NUNCA** importa de `infrastructure/` ou `presentation/`
- `infrastructure/` **NUNCA** importa de `presentation/`

### Convenções de Nomenclatura

| Item | Backend (Python) | Frontend (TypeScript) |
|------|-----------------|----------------------|
| Arquivos | `snake_case.py` | `PascalCase.ts` (entidades), `camelCase.ts` (utils) |
| Classes | `PascalCase` | `PascalCase` |
| Funções | `snake_case` | `camelCase` |
| Interfaces | `TransactionRepository` (ABC) | `ITransactionRepository` (prefixo I) |
| Use Cases | `create_transaction.py` | `CreateTransactionUseCase.ts` |
| DTOs | `transaction_dto.py` | `TransactionDTO.ts` |
| Pastas | `snake_case` | `kebab-case` |

---

## Estratégia de Testes

| Camada | Tipo de Teste | O que testar |
|--------|--------------|-------------|
| `domain/` | Unitário | Regras de negócio, validações de entidades |
| `application/` | Unitário | Use cases com repositórios mockados |
| `infrastructure/` | Integração | Repositórios com banco de dados real |
| `presentation/` | E2E | Endpoints da API / Renderização de componentes |

---

Sempre comece de dentro para fora (Domain → Application → Infrastructure → Presentation).