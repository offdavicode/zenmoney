# Integracao Frontend x Backend

Este documento descreve os contratos, procedimentos e padroes usados na integracao entre o frontend e o backend do ZenMoney.

O escopo inclui:

- configuracao dos ambientes
- autenticacao e protecao de rotas
- consumo dos endpoints disponiveis
- padrao de integracao para novas funcionalidades

---

## 1. Objetivo da integracao

Quando frontend e backend estao "em sintonia", isso significa que:

1. os endpoints que o frontend consome ja existem no backend
2. os nomes dos campos enviados e recebidos batem entre os dois lados
3. a forma de autenticacao e a mesma para todo o sistema
4. cada nova feature segue sempre o mesmo fluxo de integracao

As funcionalidades devem ser integradas seguindo os mesmos contratos e padroes descritos neste guia.

---

## 2. O que o backend ja entrega

O backend atual expõe estes endpoints:

- `GET /`
- `GET /health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/settings/profile`
- `PUT /api/settings/profile`
- `PUT /api/settings/password`
- `GET /api/settings/budget`
- `PUT /api/settings/budget`
- `GET /api/settings/budget/alert`
- `POST /api/transactions/`
- `GET /api/transactions/`
- `GET /api/transactions/{id}`
- `PUT /api/transactions/{id}`
- `DELETE /api/transactions/{id}`
- `GET /api/transactions/emotions`
- `POST /api/categories/`
- `GET /api/categories/`
- `PUT /api/categories/{id}`
- `DELETE /api/categories/{id}`
- `GET /api/reports/by-emotion`
- `GET /api/reports/by-category`
- `GET /api/reports/triggers`
- `GET /api/reports/summary`

### Papel de cada endpoint

- `POST /api/auth/register`
  cria um novo usuario

- `POST /api/auth/login`
  autentica o usuario e devolve um token JWT

- `POST /api/auth/logout`
  revoga o token atual

- `GET /api/auth/me`
  devolve os dados do usuario autenticado

- `GET /api/settings/profile`
  devolve o perfil do usuario autenticado

- `PUT /api/settings/profile`
  atualiza nome e/ou e-mail do usuario autenticado

- `PUT /api/settings/password`
  troca a senha do usuario autenticado

- `GET /api/settings/budget`
  consulta os limites mensais configurados e o uso atual do mes

- `PUT /api/settings/budget`
  cria, atualiza ou remove limite mensal global e por categoria

- `GET /api/settings/budget/alert`
  verifica se existe um novo alerta critico de teto de gastos para exibir

- `POST /api/transactions/`
  cria uma nova transacao para o usuario autenticado

- `GET /api/transactions/`
  lista as transacoes do usuario autenticado

- `GET /api/transactions/{id}`
  busca uma transacao especifica do usuario autenticado

- `PUT /api/transactions/{id}`
  atualiza uma transacao existente do usuario autenticado

- `DELETE /api/transactions/{id}`
  remove uma transacao do usuario autenticado

- `GET /api/transactions/emotions`
  lista as emocoes aceitas no cadastro de transacoes

- `POST /api/categories/`
  cria uma categoria propria do usuario autenticado

- `GET /api/categories/`
  lista categorias padrao do sistema e categorias proprias do usuario

- `PUT /api/categories/{id}`
  atualiza uma categoria propria do usuario autenticado

- `DELETE /api/categories/{id}`
  remove uma categoria propria do usuario autenticado

- `GET /api/reports/by-emotion`
  agrupa gastos do usuario autenticado por emocao

- `GET /api/reports/by-category`
  agrupa gastos do usuario autenticado por categoria

- `GET /api/reports/triggers`
  cruza emocao e categoria para identificar possiveis gatilhos de gasto

- `GET /api/reports/summary`
  gera o resumo financeiro geral do usuario autenticado

---

## 3. Premissas para a integracao

Antes da integracao, as seguintes condicoes devem ser atendidas:

1. o backend esta subindo normalmente com `uvicorn`
2. o endpoint `http://127.0.0.1:8000/health` responde `{"status":"ok"}`
3. o endpoint `http://127.0.0.1:8000/docs` abre normalmente
4. o frontend ja tem uma camada de `services` para chamadas HTTP
5. o frontend ja tem ou tera um `AuthContext`

---

## 4. Subindo o backend

Os comandos devem ser executados a partir do diretorio `backend/` do projeto.

### Passos

1. ativar a `.venv`
2. carregar o `.env` manualmente
3. subir o `uvicorn`

Exemplo no PowerShell:

```powershell
cd caminho\para\zenmoney_v2\backend
.\.venv\Scripts\Activate.ps1
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}
uvicorn main:app --reload
```

Apos a inicializacao, a API fica disponivel em:

`http://127.0.0.1:8000`

---

## 5. Definindo a URL base no frontend

O frontend precisa saber para onde enviar as requisicoes.

### Sugestao

Criar uma variavel de ambiente no frontend:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
```

### Exemplo de uso

```ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
```

O frontend deve utilizar uma unica URL base. Alteracoes de porta ou host ficam centralizadas nessa variavel.

---

## 6. Escolha da estrategia de autenticacao

O backend atual foi implementado para trabalhar com:

- token JWT
- header `Authorization: Bearer <token>`

Isso combina especialmente bem com duas abordagens no frontend:

### Opcao 1. Guardar token em `localStorage`

Vantagens:

- simples
- facil para projeto de faculdade
- combina muito bem com `AuthContext`

Desvantagens:

- menos robusto contra XSS do que cookies HTTP-only

### Opcao 2. Guardar token apenas em memoria

Vantagens:

- mais seguro do que `localStorage`

Desvantagens:

- o usuario perde a sessao ao atualizar a pagina, a menos que exista outra estrategia complementar

### Recomendacao para este projeto

Para o escopo academico do ZenMoney, a opcao recomendada e armazenar o token em `localStorage`.

Motivo:

- mais simples
- integra rapido
- adequado ao escopo atual do sistema
- coerente com o backend que ja esta pronto

---

## 7. Estrutura recomendada no frontend

Uma organizacao recomendada e:

- `services/auth.service.ts`
- `contexts/AuthContext.tsx`
- `utils/http.ts` ou `services/api.ts`
- paginas:
  - `login`
  - `register`
  - area protegida do dashboard

---

## 8. Criando a camada de servicos no frontend

O frontend deve ter funcoes para chamar o backend.

## 8.1 Exemplo de `auth.service.ts`

```ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function registerUser(payload: {
  name: string;
  email: string;
  password: string;
}) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao cadastrar usuario.");
  }

  return response.json();
}

export async function loginUser(payload: {
  email: string;
  password: string;
}) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao fazer login.");
  }

  return response.json();
}

export async function getCurrentUser(token: string) {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao buscar usuario autenticado.");
  }

  return response.json();
}

export async function logoutUser(token: string) {
  const response = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao fazer logout.");
  }

  return response.json();
}
```

### Funcao dessa camada

Ela evita espalhar `fetch()` pelo frontend inteiro.

Em vez de cada componente conhecer URL, header e parse de erro, os componentes chamam funcoes prontas.

---

## 9. Criando o AuthContext

O `AuthContext` e a peca central para o frontend saber:

- se o usuario esta autenticado
- quem e o usuario atual
- qual token usar
- como fazer login e logout
- como manter o perfil local atualizado

## 9.1 Responsabilidades do AuthContext

Ele deve:

1. guardar `token`
2. guardar `user`
3. expor `login()`
4. expor `logout()`
5. carregar sessao salva ao iniciar a app
6. limpar sessao quando token expira ou e revogado

## 9.2 Fluxo recomendado

### Na inicializacao da app

1. ler token do `localStorage`
2. se existir token, chamar `GET /auth/me`
3. se a resposta for `200`, manter sessao
4. se a resposta for `401`, limpar token e tratar como deslogado

### No login

1. chamar `POST /auth/login`
2. guardar `access_token`
3. guardar dados do usuario retornado
4. redirecionar para area protegida

### No logout

1. chamar `POST /auth/logout`
2. remover token do `localStorage`
3. limpar estado do contexto
4. redirecionar para login

---

## 10. Exemplo de estado do AuthContext

Exemplo conceitual:

```ts
type AuthContextType = {
  user: {
    id: number;
    name: string;
    email: string;
  } | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};
```

O frontend nao precisa conhecer a estrutura interna do backend. Ele so precisa conhecer o contrato HTTP.

---

## 11. Protegendo rotas no frontend

Depois que o `AuthContext` existir, as paginas protegidas devem verificar se o usuario esta autenticado.

### Fluxo simples

1. pagina abre
2. verifica `isAuthenticated`
3. se for falso, redireciona para `/login`
4. se for verdadeiro, renderiza a tela protegida

### Onde aplicar primeiro

Pelo menos em:

- dashboard principal
- tela de perfil
- futuras telas de transacoes, categorias e relatorios

---

## 12. Fluxo completo de autenticacao

O ciclo completo de integracao entre frontend e backend deve funcionar assim:

1. usuario abre a tela de cadastro
2. frontend envia `POST /api/auth/register`
3. usuario vai para login
4. frontend envia `POST /api/auth/login`
5. backend responde com token e dados do usuario
6. frontend guarda token
7. frontend redireciona para uma tela protegida
8. tela protegida consulta `GET /api/auth/me` se necessario
9. usuario clica em sair
10. frontend chama `POST /api/auth/logout`
11. frontend limpa estado local
12. usuario volta para a tela de login

---

## 13. Formato dos dados da autenticacao

## 13.1 Cadastro

### Request

`POST /api/auth/register`

```json
{
  "name": "Maria Silva",
  "email": "maria@example.com",
  "password": "Senha@123"
}
```

### Response

```json
{
  "id": 1,
  "name": "Maria Silva",
  "email": "maria@example.com"
}
```

## 13.2 Login

### Request

`POST /api/auth/login`

```json
{
  "email": "maria@example.com",
  "password": "Senha@123"
}
```

### Response

```json
{
  "access_token": "TOKEN_AQUI",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "name": "Maria Silva",
    "email": "maria@example.com"
  }
}
```

## 13.3 Usuario autenticado

### Request

`GET /api/auth/me`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

```json
{
  "id": 1,
  "name": "Maria Silva",
  "email": "maria@example.com"
}
```

## 13.4 Logout

### Request

`POST /api/auth/logout`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

```json
{
  "message": "Logout completed successfully."
}
```

## 13.5 Atualizacao de perfil

### Request

`PUT /api/settings/profile`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

Body:

```json
{
  "name": "Maria Clara Silva",
  "email": "maria.clara@example.com"
}
```

### Response

```json
{
  "id": 1,
  "name": "Maria Clara Silva",
  "email": "maria.clara@example.com"
}
```

Observacao:

- e permitido enviar apenas `name`
- e permitido enviar apenas `email`
- pelo menos um dos dois campos deve ser enviado

## 13.6 Troca de senha

### Request

`PUT /api/settings/password`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

Body:

```json
{
  "current_password": "Senha@123",
  "new_password": "NovaSenha@456"
}
```

### Response

```json
{
  "message": "Password updated successfully."
}
```

Observacao:

- a senha atual precisa estar correta
- a nova senha precisa obedecer as mesmas regras de seguranca do cadastro
- a nova senha deve ser diferente da senha atual

---

## 13.7 Teto de gastos

O backend permite configurar limites mensais:

- um limite global para todas as despesas
- limites especificos por categoria de despesa

Sem limite configurado, `alerts_enabled` fica `false`.

### Consultar teto de gastos

Request:

`GET /api/settings/budget?month=2026-06`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

Response:

```json
{
  "month": "2026-06",
  "global_limit": {
    "category_id": null,
    "category_name": "Limite mensal geral",
    "limit_amount": "200.00",
    "spent_amount": "150.00",
    "remaining_amount": "50.00",
    "usage_percentage": 75.0,
    "is_exceeded": false
  },
  "category_limits": [
    {
      "category_id": 1,
      "category_name": "Alimentacao",
      "limit_amount": "120.00",
      "spent_amount": "100.00",
      "remaining_amount": "20.00",
      "usage_percentage": 83.33,
      "is_exceeded": false
    }
  ],
  "alerts_enabled": true
}
```

### Atualizar teto de gastos

Request:

`PUT /api/settings/budget?month=2026-06`

Body:

```json
{
  "global_limit": "200.00",
  "category_limits": [
    {
      "category_id": 1,
      "amount": "120.00"
    }
  ]
}
```

### Remover limites

Enviar `null` remove o limite informado:

```json
{
  "global_limit": null,
  "category_limits": [
    {
      "category_id": 1,
      "amount": null
    }
  ]
}
```

### Regras

- `global_limit` e `amount` precisam ser maiores que zero quando informados
- limite por categoria so aceita categoria de despesa
- o frontend nao envia `user_id`
- receitas nao entram no calculo de gasto
- despesas de outros meses nao entram no calculo quando `month` e informado
- `month` usa o formato `YYYY-MM`

---

## 13.8 Alertas criticos de teto de gastos

O backend monitora limites de 10% em 10%.

Exemplo:

- 10%
- 20%
- 30%
- ...
- 100%

Cada faixa e emitida apenas uma vez por mes e por escopo.

Escopos possiveis:

- limite global
- limite por categoria

Se varias faixas forem cruzadas ao mesmo tempo, o backend retorna apenas o alerta mais alto.

### Verificar alerta

Request:

`GET /api/settings/budget/alert?month=2026-06`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

Response com alerta:

```json
{
  "month": "2026-06",
  "alert": {
    "month": "2026-06",
    "scope": "category",
    "category_id": 1,
    "category_name": "Alimentacao",
    "threshold_percent": 80,
    "limit_amount": "120.00",
    "spent_amount": "100.00",
    "usage_percentage": 83.33,
    "message": "Voce atingiu 80% do limite de Alimentacao."
  }
}
```

Response sem alerta novo:

```json
{
  "month": "2026-06",
  "alert": null
}
```

### Quando o frontend deve chamar

Recomendacao:

1. depois de criar uma transacao de despesa
2. depois de editar uma transacao de despesa
3. ao abrir o dashboard
4. depois de alterar um limite de gastos

### Regras

- sem limite configurado, nao ha alerta
- receitas nao geram alerta
- alertas usam apenas despesas do mes informado
- alertas de faixas ja emitidas nao aparecem novamente
- se o limite for alterado, o historico daquele limite e recalculado

---

## 14. Tratamento de erros no frontend

O frontend deve estar preparado para respostas como:

- `400`
- `401`
- `409`
- `423`

### Exemplos importantes

- `401 Unauthorized`
  credencial invalida, token invalido ou expirado

- `409 Conflict`
  e-mail ja cadastrado

- `423 Locked`
  conta bloqueada temporariamente por muitas tentativas invalidas

- `400 Bad Request`
  tentativa de trocar para a mesma senha ou payload invalido de atualizacao

### Comportamento recomendado

- se for erro de login ou cadastro: mostrar mensagem amigavel na tela
- se for `401` em rota protegida: limpar sessao e redirecionar para login
- se for `423`: informar ao usuario que ele precisa aguardar

---

## 15. Como testar a integracao manualmente

### Teste 1. Backend isolado

1. abrir `/docs`
2. testar `register`
3. testar `login`
4. copiar token
5. testar `me`
6. testar `logout`

### Teste 2. Frontend + backend

1. abrir tela de cadastro
2. criar usuario
3. abrir tela de login
4. fazer login
5. verificar se foi para area protegida
6. recarregar a pagina e ver se a sessao permanece
7. sair da conta
8. tentar abrir rota protegida novamente

### Teste 3. Atualizacao de perfil

1. fazer login
2. abrir tela de perfil
3. alterar nome ou e-mail
4. enviar `PUT /api/settings/profile`
5. conferir se a UI mostra os dados atualizados

### Teste 4. Troca de senha

1. fazer login
2. abrir tela de seguranca ou perfil
3. informar senha atual
4. informar nova senha
5. enviar `PUT /api/settings/password`
6. testar login com a senha nova

---

## 16. Padrao para integrar novas funcionalidades

Cada nova funcionalidade deve seguir o mesmo fluxo de integracao.

### Passo 1. Confirmar contrato do backend

Definir:

- endpoint
- metodo HTTP
- request
- response
- regras de negocio

### Passo 2. Criar servico no frontend

Exemplo:

- `transaction.service.ts`
- `category.service.ts`
- `report.service.ts`

### Passo 3. Criar tipos da feature

Exemplo:

- `Transaction`
- `Category`
- `ReportSummary`

### Passo 4. Ligar ao estado da UI

Pode ser com:

- `useState`
- `useEffect`
- `Context`
- ou outra abordagem usada pelo time

### Passo 5. Testar manualmente

Sempre testar:

- caso de sucesso
- erro de validacao
- estado sem dados
- comportamento autenticado

---

## 17. Ordem sugerida de integracao

A ordem recomendada considera as dependencias entre os modulos:

1. autenticacao e perfil
2. transacoes
3. categorias e categorizacao emocional
4. teto de gastos e alertas
5. relatorios e analises

Depois desses modulos, novas funcionalidades podem ser integradas conforme as prioridades do projeto.

Essa sequencia permite que cada modulo utilize contratos que ja foram integrados e validados anteriormente.

---

## 20. Integrando RF02 no frontend

O backend de transacoes foi implementado assumindo que:

- o usuario ja esta autenticado
- o token JWT vai no header `Authorization`
- o `user_id` nao e enviado pelo frontend

Isso e importante: o backend descobre o usuario pelo token.

### Request de criacao

`POST /api/transactions/`

Header:

```http
Authorization: Bearer TOKEN_AQUI
Content-Type: application/json
```

Body:

```json
{
  "category_id": null,
  "type": "expense",
  "amount": "59.90",
  "date": "2026-05-24",
  "description": "Mercado da semana",
  "emotion": "ansiedade"
}
```

### Response

```json
{
  "id": 1,
  "user_id": 1,
  "category_id": null,
  "recurrence_id": null,
  "type": "expense",
  "amount": "59.90",
  "date": "2026-05-24",
  "description": "Mercado da semana",
  "emotion": "ansiedade"
}
```

### Regras importantes

- `amount` precisa ser maior que zero
- `type` so pode ser `income` ou `expense`
- `category_id` e opcional
- quando `category_id` for enviado, ele precisa vir de `GET /api/categories/`
- a categoria precisa ter o mesmo `type` da transacao
- `description` e opcional
- `emotion` e opcional; se vier vazia, vira `not_specified`
- `emotion` so aceita valores da lista retornada por `GET /api/transactions/emotions`
- somente despesas armazenam uma emocao selecionada
- receitas sempre sao salvas com `emotion: "not_specified"`, mesmo que outro valor seja enviado
- ao transformar uma despesa em receita, sua emocao e redefinida para `not_specified`
- o frontend nao manda `user_id`

### Emocoes permitidas

`GET /api/transactions/emotions`

Response:

```json
[
  {
    "value": "not_specified",
    "label": "Nao especificada"
  },
  {
    "value": "calma",
    "label": "Calma"
  },
  {
    "value": "ansiedade",
    "label": "Ansiedade"
  }
]
```

Valores atuais:

- `not_specified`
- `calma`
- `felicidade`
- `raiva`
- `frustracao`
- `empolgacao`
- `ansiedade`
- `estresse`
- `indiferenca`
- `satisfacao`
- `tedio`

O frontend deve exibir o seletor de emocao apenas quando `type` for `expense`.

## 20.1 Servico de transacoes no frontend

Exemplo de funcoes que o frontend deve criar:

- `createTransaction(payload, token)`
- `listTransactions(token)`
- `getTransaction(id, token)`
- `updateTransaction(id, payload, token)`
- `deleteTransaction(id, token)`

Exemplo conceitual:

```ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function listTransactions(token: string) {
  const response = await fetch(`${API_BASE_URL}/transactions/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao listar transacoes.");
  }

  return response.json();
}
```

## 20.2 Fluxo recomendado no frontend

1. usuario faz login
2. frontend salva token
3. tela de transacoes chama `GET /api/transactions/`
4. tela ou formulario carrega categorias com `GET /api/categories/`
5. tela ou formulario carrega emocoes com `GET /api/transactions/emotions`
6. formulario envia `POST /api/transactions/`
7. edicao usa `PUT /api/transactions/{id}`
8. exclusao usa `DELETE /api/transactions/{id}`

## 20.3 Teste manual de RF02

1. fazer login
2. abrir tela de transacoes
3. carregar categorias disponiveis
4. carregar emocoes disponiveis
5. criar uma transacao com ou sem categoria e com uma emocao valida
6. confirmar que ela aparece na listagem
7. editar a transacao
8. confirmar a alteracao na lista
9. excluir a transacao
10. confirmar que ela sumiu

---

## 21. Integrando RF03 Categorias no frontend

O backend de categorias foi implementado assumindo que:

- o usuario ja esta autenticado
- o token JWT vai no header `Authorization`
- categorias padrao pertencem ao sistema
- categorias criadas manualmente pertencem ao usuario logado
- categorias padrao nao podem ser editadas nem excluidas
- as categorias padrao incluem todas as categorias previstas no RF03
- `parent_id` transforma uma categoria personalizada em subcategoria
- categoria e subcategoria precisam possuir o mesmo tipo (`income` ou `expense`)
- uma categoria pode possuir varios niveis de subcategorias
- hierarquias circulares sao rejeitadas

### Categorias padrao do RF03

Despesas:

- `Moradia`
- `Contas Residenciais`
- `Saude`
- `Educacao`
- `Alimentacao`
- `Transporte`
- `Cuidados Pessoais`
- `Hobbies`
- `Roupas`
- `Compras`
- `Lazer`
- `Investimentos`
- `Dividas`
- `Reserva de emergencia`
- `Nao especificado`

Receitas:

- `Salario`
- `Aposentadoria`
- `Pensao`
- `Aluguel`
- `Pro-labore`
- `Comissao/bonus`
- `Freelance`
- `Dividendos e juros`
- `Venda de itens`
- `Nao especificado`

O backend tambem preserva algumas categorias extras de versoes anteriores para manter compatibilidade.

### Listar categorias

`GET /api/categories/`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

Response:

```json
[
  {
    "id": 1,
    "name": "Alimentacao",
    "type": "expense",
    "is_default": true,
    "is_essential": true,
    "parent_id": null
  }
]
```

### Criar categoria

`POST /api/categories/`

Header:

```http
Authorization: Bearer TOKEN_AQUI
Content-Type: application/json
```

Body:

```json
{
  "name": "Pet shop",
  "type": "expense",
  "is_essential": false,
  "parent_id": null
}
```

Response:

```json
{
  "id": 15,
  "name": "Pet shop",
  "type": "expense",
  "is_default": false,
  "is_essential": false,
  "parent_id": null
}
```

### Atualizar categoria

`PUT /api/categories/{id}`

Body:

```json
{
  "name": "Pets",
  "is_essential": true
}
```

Observacoes:

- `name`, `parent_id` e `is_essential` sao opcionais
- nao e permitido atualizar categoria padrao
- nao e permitido usar nome duplicado no mesmo tipo
- `parent_id`, quando enviado, precisa apontar para categoria do mesmo tipo
- `parent_id: null` transforma uma subcategoria novamente em categoria raiz
- nao e permitido definir a propria categoria ou uma descendente como pai

### Excluir categoria

`DELETE /api/categories/{id}`

Observacoes:

- apenas categorias proprias do usuario podem ser excluidas
- categorias padrao nao podem ser excluidas
- existem duas categorias padrao chamadas `Nao especificado`: uma para receitas e outra para despesas
- ao excluir uma categoria personalizada, suas transacoes e recorrencias sao transferidas para `Nao especificado` do mesmo tipo
- limites e historicos de alerta ligados diretamente a uma categoria personalizada sao removidos junto com ela
- subcategorias da categoria excluida permanecem existentes e passam a ser categorias raiz com `parent_id: null`
- `category_id` ainda aceita `null` quando o usuario deseja registrar uma transacao sem selecionar categoria

### Servico de categorias no frontend

Funcoes recomendadas:

- `listCategories(token)`
- `createCategory(payload, token)`
- `updateCategory(id, payload, token)`
- `deleteCategory(id, token)`

---

## 22. Integrando resumo financeiro no frontend

O endpoint de resumo financeiro alimenta os cards principais do dashboard.

Ele considera:

- receitas e despesas do usuario autenticado
- todas as transacoes registradas ate o momento
- separacao entre despesa essencial, nao essencial e sem categoria

### Request

`GET /api/reports/summary`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

```json
{
  "transaction_count": 4,
  "income_count": 1,
  "expense_count": 3,
  "total_income": "1000.00",
  "total_expense": "175.00",
  "balance": "825.00",
  "average_expense": "58.33",
  "essential_expense": "100.00",
  "essential_expense_percentage": 57.14,
  "non_essential_expense": "75.00",
  "non_essential_expense_percentage": 42.86,
  "uncategorized_expense": "25.00"
}
```

### Uso recomendado no frontend

Esse retorno pode alimentar:

- card de saldo atual
- card de receitas totais
- card de despesas totais
- card de gasto medio
- indicador de gastos essenciais x nao essenciais
- alerta visual para transacoes sem categoria

---

## 23. Integrando relatorio por emocao no frontend

O endpoint de relatorio por emocao usa apenas dados do usuario autenticado.

Ele considera:

- apenas transacoes do tipo `expense`
- apenas transacoes do usuario do token
- todas as emocoes validas, mesmo quando o total for zero

### Request

`GET /api/reports/by-emotion`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

```json
[
  {
    "emotion": "ansiedade",
    "label": "Ansiedade",
    "transaction_count": 2,
    "total_amount": "150.00",
    "percentage": 62.5
  },
  {
    "emotion": "felicidade",
    "label": "Felicidade",
    "transaction_count": 1,
    "total_amount": "90.00",
    "percentage": 37.5
  }
]
```

### Campos

- `emotion`: valor interno usado pelo backend
- `label`: texto pronto para exibicao na interface
- `transaction_count`: quantidade de despesas naquela emocao
- `total_amount`: soma das despesas naquela emocao
- `percentage`: porcentagem daquela emocao dentro do total de despesas

### Uso recomendado no frontend

Criar uma funcao como:

```ts
export async function getEmotionReport(token: string) {
  const response = await fetch(`${API_BASE_URL}/reports/by-emotion`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao buscar relatorio por emocao.");
  }

  return response.json();
}
```

Esse retorno pode alimentar:

- grafico de pizza
- grafico de barras
- cards de resumo emocional
- alertas futuros de gatilho de gasto

---

## 24. Integrando relatorio por categoria no frontend

O endpoint de relatorio por categoria mostra onde o usuario gastou mais.

Ele considera:

- apenas transacoes do tipo `expense`
- apenas transacoes do usuario autenticado
- categorias padrao e categorias proprias do usuario
- uma linha especial chamada `Sem categoria`

### Request

`GET /api/reports/by-category`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

```json
[
  {
    "category_id": 1,
    "category_name": "Alimentacao",
    "is_default": true,
    "is_essential": true,
    "transaction_count": 3,
    "total_amount": "450.00",
    "percentage": 60.0
  },
  {
    "category_id": null,
    "category_name": "Sem categoria",
    "is_default": false,
    "is_essential": false,
    "transaction_count": 1,
    "total_amount": "50.00",
    "percentage": 6.67
  }
]
```

### Graficos recomendados

- grafico de barras por categoria
- grafico de pizza de distribuicao de gastos
- lista de maiores categorias de gasto
- cards separando gasto essencial e nao essencial

---

## 25. Integrando gatilhos de gasto no frontend

O endpoint de gatilhos cruza categoria e emocao.

Esse cruzamento permite analisar perguntas como:

- em qual categoria ocorrem mais gastos associados a `ansiedade`?
- qual emocao aparece junto aos maiores gastos em `Lazer`?
- quais combinacoes emocao + categoria merecem atencao?

### Request

`GET /api/reports/triggers`

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

```json
[
  {
    "emotion": "ansiedade",
    "emotion_label": "Ansiedade",
    "category_id": 1,
    "category_name": "Alimentacao",
    "transaction_count": 2,
    "total_amount": "150.00",
    "average_amount": "75.00",
    "percentage": 66.67
  }
]
```

### Campos

- `emotion`: valor interno da emocao
- `emotion_label`: texto para exibir na interface
- `category_id`: identificador da categoria, ou `null` quando nao houver categoria
- `category_name`: nome da categoria
- `transaction_count`: quantidade de despesas nessa combinacao
- `total_amount`: total gasto nessa combinacao
- `average_amount`: gasto medio por transacao nessa combinacao
- `percentage`: participacao dessa combinacao no total de despesas

### Graficos recomendados

- ranking de gatilhos por `total_amount`
- mapa de calor emocao x categoria
- tabela de padroes de gasto
- cards de alerta, por exemplo: `Ansiedade + Alimentacao = R$ 150,00`

---

## 18. Observacao importante sobre CORS

Se o frontend e o backend rodarem em origens diferentes, o navegador pode bloquear as requisicoes sem configuracao de CORS.

Exemplo:

- frontend em `http://localhost:3000`
- backend em `http://127.0.0.1:8000`

Nesse caso, o backend precisa liberar a origem utilizada pelo frontend. A configuracao deve ser realizada quando os dois ambientes forem executados em origens diferentes.

---

## 19. Resumo final

Fluxo recomendado para a integracao:

1. iniciar o backend
2. definir a URL base da API no frontend
3. criar `auth.service.ts`
4. implementar `AuthContext`
5. persistir o token no frontend
6. proteger as rotas do dashboard
7. testar `register -> login -> me -> logout`
8. aplicar o mesmo padrao nas demais funcionalidades
