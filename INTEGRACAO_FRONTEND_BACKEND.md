# Integracao Frontend x Backend

Este documento descreve os contratos, procedimentos e padroes usados na integracao entre o frontend e o backend do ZenMoney.

O escopo inclui:

- configuracao dos ambientes
- autenticacao e protecao de rotas
- consumo dos endpoints disponiveis
- padrao de integracao para novas funcionalidades

### Estado atual e limitacoes conhecidas

- todos os endpoints documentados neste guia existem no backend
- autenticacao, transacoes, recorrencias, categorias, emocoes, teto de gastos, alertas e agregacoes de relatorio possuem contratos utilizaveis
- limites de gastos sao configuracoes recorrentes; o parametro `month` seleciona apenas o mes usado para calcular gastos e alertas
- o RF08 possui filtros por mes ou intervalo de datas e um endpoint visual preparado para graficos; subcategorias ainda sao contabilizadas separadamente
- o RF09 possui matriz emocao x categoria e analise completa de gatilhos emocionais
- limites e relatorios por categoria contabilizam cada categoria separadamente; gastos de subcategorias ainda nao sao somados automaticamente ao pai
- CORS permite por padrao `http://localhost:3000` e `http://127.0.0.1:3000`;
  outras origens devem ser adicionadas a `FRONTEND_ORIGINS`
- previsao de saldo do mes atual possui contrato utilizavel
- exclusao definitiva da conta e horario de registro das transacoes possuem
  contratos utilizaveis

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
- `DELETE /api/settings/account`
- `GET /api/settings/budget`
- `PUT /api/settings/budget`
- `GET /api/settings/budget/alert`
- `GET /api/settings/survival-mode`
- `PUT /api/settings/survival-mode`
- `POST /api/transactions/`
- `GET /api/transactions/`
- `GET /api/transactions/{id}`
- `PUT /api/transactions/{id}`
- `DELETE /api/transactions/{id}`
- `GET /api/transactions/emotions`
- `POST /api/recurrences/`
- `GET /api/recurrences/`
- `GET /api/recurrences/{id}`
- `PUT /api/recurrences/{id}`
- `PATCH /api/recurrences/{id}/pause`
- `PATCH /api/recurrences/{id}/resume`
- `DELETE /api/recurrences/{id}`
- `POST /api/recurrences/run-due`
- `POST /api/categories/`
- `GET /api/categories/`
- `PUT /api/categories/{id}`
- `DELETE /api/categories/{id}`
- `GET /api/reports/by-emotion`
- `GET /api/reports/by-category`
- `GET /api/reports/visual`
- `GET /api/reports/triggers`
- `GET /api/reports/emotion-spending-analysis`
- `GET /api/reports/summary`
- `GET /api/reports/survival-mode`
- `GET /api/reports/balance-prediction`

### Papel de cada endpoint

Rotas de negocio exigem `Authorization: Bearer <token>`. As excecoes publicas atuais sao:

- `GET /`
- `GET /health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/transactions/emotions`

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

- `DELETE /api/settings/account`
  exclui definitivamente a conta autenticada e seus registros apos confirmar a senha

- `GET /api/settings/budget`
  consulta os limites mensais configurados e o uso atual do mes

- `PUT /api/settings/budget`
  cria, atualiza ou remove limite mensal global e por categoria

- `GET /api/settings/budget/alert`
  verifica se existe um novo alerta critico de teto de gastos para exibir

- `GET /api/settings/survival-mode`
  consulta a porcentagem configurada para ativar o modo sobrevivencia

- `PUT /api/settings/survival-mode`
  atualiza a porcentagem de ativacao entre 50% e 90%

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

- `POST /api/recurrences/`
  salva um novo agendamento mensal sem criar uma transacao imediatamente

- `GET /api/recurrences/`
  lista os agendamentos do usuario autenticado

- `GET /api/recurrences/{id}`
  busca um agendamento especifico do usuario autenticado

- `PUT /api/recurrences/{id}`
  edita apenas o agendamento e suas geracoes futuras

- `PATCH /api/recurrences/{id}/pause`
  pausa novas geracoes sem alterar transacoes existentes

- `PATCH /api/recurrences/{id}/resume`
  retoma o agendamento a partir da proxima data valida, sem preencher o periodo pausado

- `DELETE /api/recurrences/{id}`
  cancela o agendamento e preserva transacoes ja geradas

- `POST /api/recurrences/run-due`
  gera as ocorrencias vencidas ate a data atual sem duplicar registros

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

- `GET /api/reports/visual`
  prepara distribuicoes para pizza, barras e listas textuais conforme as regras do RF08

- `GET /api/reports/triggers`
  cruza emocao e categoria para fornecer a matriz usada em graficos

- `GET /api/reports/emotion-spending-analysis`
  classifica gatilhos gerais e por categoria e retorna maiores gastos por emocao

- `GET /api/reports/summary`
  gera o resumo financeiro geral do usuario autenticado

- `GET /api/reports/survival-mode`
  avalia o modo sobrevivencia no mes e retorna recomendacoes e destaques

- `GET /api/reports/balance-prediction`
  calcula o saldo liquido projetado para o final do mes atual

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

## 13.7 Exclusao definitiva da conta

### Request

`DELETE /api/settings/account`

Header:

```http
Authorization: Bearer TOKEN_AQUI
Content-Type: application/json
```

Body:

```json
{
  "current_password": "Senha@123"
}
```

### Response

```json
{
  "message": "Account and all associated data were permanently deleted."
}
```

Observacoes:

- a senha atual precisa estar correta
- a operacao remove definitivamente os dados pertencentes ao usuario
- categorias padrao globais e dados de outros usuarios sao preservados
- apos o sucesso, o frontend deve apagar o token local e redirecionar para a tela publica
- a interface deve pedir confirmacao clara antes de enviar a requisicao

---

## 13.8 Teto de gastos

O backend permite configurar limites mensais:

- um limite global para todas as despesas
- limites especificos por categoria de despesa

Sem limite configurado, `alerts_enabled` fica `false`.

Os valores configurados sao recorrentes e valem para qualquer mes consultado. O parametro `month=YYYY-MM` nao cria um limite exclusivo para aquele mes; ele define apenas quais despesas serao usadas no calculo de `spent_amount`, `remaining_amount`, `usage_percentage` e alertas.

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
- limite por categoria considera apenas despesas atribuidas diretamente aquela categoria; subcategorias sao calculadas separadamente
- o frontend nao envia `user_id`
- receitas nao entram no calculo de gasto
- despesas de outros meses nao entram no calculo quando `month` e informado
- `month` usa o formato `YYYY-MM`
- omitir `global_limit` preserva o limite global atual
- omitir uma categoria de `category_limits` preserva o limite atual daquela categoria
- enviar `null` remove apenas o limite explicitamente informado
- limites por categoria podem existir sem limite global
- remover o limite global preserva os limites por categoria
- quando existe limite global, a soma dos limites por categoria nao pode ultrapassa-lo
- reduzir o limite global abaixo da soma final das categorias retorna erro `400`
- alteracoes enviadas juntas sao validadas pelo estado final; portanto, e possivel reduzir o global e remover ou reduzir categorias na mesma requisicao
- uma requisicao rejeitada nao aplica alteracoes parciais

Exemplo de erro por configuracao incoerente:

```json
{
  "detail": "The sum of category limits cannot exceed the global limit."
}
```

---

## 13.9 Alertas criticos de teto de gastos

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
- alterar ou remover um limite apaga o historico de alertas daquele escopo em todos os meses

---

## 13.10 Modo sobrevivencia

O modo sobrevivencia orienta o usuario quando o limite global ou qualquer limite
por categoria atinge a porcentagem configurada. O valor padrao e 80%, podendo ser
alterado para qualquer inteiro entre 50% e 90%.

O backend nunca bloqueia transacoes. Ele retorna recomendacoes, uma sugestao de
bloqueio visual e IDs de despesas que o frontend pode destacar.

### Consultar configuracao

`GET /api/settings/survival-mode`

Resposta antes de uma configuracao explicita:

```json
{
  "activation_percentage": 80,
  "is_default": true
}
```

### Atualizar configuracao

`PUT /api/settings/survival-mode`

```json
{
  "activation_percentage": 70
}
```

Valores abaixo de 50 ou acima de 90 retornam erro `422`.

### Avaliar o mes

`GET /api/reports/survival-mode?month=2026-06`

Exemplo de resposta ativa:

```json
{
  "month": "2026-06",
  "activation_percentage": 80,
  "is_active": true,
  "activation_reason": "category_limit",
  "trigger": {
    "scope": "category",
    "category_id": 10,
    "category_name": "Lazer",
    "limit_amount": "300.00",
    "spent_amount": "330.00",
    "usage_percentage": 110.0
  },
  "recommendations": [
    {
      "category_id": 10,
      "category_name": "Lazer",
      "spent_amount": "330.00",
      "limit_amount": "300.00",
      "exceeded_amount": "30.00",
      "usage_percentage": 110.0,
      "suggest_block_new_transactions": true,
      "message": "Considere reduzir gastos em Lazer e evitar novos lancamentos nao essenciais nesta categoria."
    }
  ],
  "highlighted_transaction_ids": [18, 12]
}
```

Valores possiveis de `activation_reason`:

- `no_limits`: nenhum limite configurado
- `below_threshold`: existem limites, mas nenhum atingiu a porcentagem
- `global_limit`: limite global ativou o modo
- `category_limit`: limite de uma categoria ativou o modo

### Regras para o frontend

- consultar a avaliacao ao abrir ou atualizar o dashboard
- destacar as despesas presentes em `highlighted_transaction_ids`
- exibir recomendacoes na ordem enviada pelo backend
- tratar `suggest_block_new_transactions` apenas como orientacao visual
- continuar permitindo novos lancamentos
- categorias essenciais podem ativar o modo, mas nao aparecem nas recomendacoes
- recomendacoes consideram somente despesas do mes informado

---

## 14. Tratamento de erros no frontend

O frontend deve estar preparado para respostas como:

- `400`
- `401`
- `403`
- `404`
- `409`
- `422`
- `423`

### Exemplos importantes

- `401 Unauthorized`
  credencial invalida, token invalido ou expirado

- `409 Conflict`
  e-mail ja cadastrado

- `403 Forbidden`
  tentativa de editar ou excluir uma categoria padrao

- `404 Not Found`
  recurso inexistente, pertencente a outro usuario ou categoria incompativel

- `422 Unprocessable Entity`
  payload rejeitado pelas validacoes de schema, como valor negativo, e-mail invalido ou emocao desconhecida

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

## 18. Integrando RF02 no frontend

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
  "registered_at": "2026-06-11T14:30:00-03:00",
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
  "is_recurring": false,
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
- `recurrence_id` e `is_recurring` sao definidos pelo backend e nao devem ser
  enviados pelo frontend
- transacoes manuais possuem `is_recurring: false`
- transacoes geradas por agendamento possuem `is_recurring: true`
- `date` e a data financeira escolhida pelo usuario
- `registered_at` e definido pelo backend e informa a data e hora reais do
  cadastro em Brasilia
- o frontend deve exibir datas no formato nacional `DD/MM/AAAA`
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

## 18.1 Servico de transacoes no frontend

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

## 18.2 Fluxo recomendado no frontend

1. usuario faz login
2. frontend salva token
3. tela de transacoes chama `GET /api/transactions/`
4. tela ou formulario carrega categorias com `GET /api/categories/`
5. tela ou formulario carrega emocoes com `GET /api/transactions/emotions`
6. formulario envia `POST /api/transactions/`
7. edicao usa `PUT /api/transactions/{id}`
8. exclusao usa `DELETE /api/transactions/{id}`

## 18.3 Teste manual de RF02

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

## 19. Integrando RF03 Categorias no frontend

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
- `category_id: null` representa `Sem categoria` e e diferente da categoria padrao `Nao especificado`

### Servico de categorias no frontend

Funcoes recomendadas:

- `listCategories(token)`
- `createCategory(payload, token)`
- `updateCategory(id, payload, token)`
- `deleteCategory(id, token)`

---

## 20. Integrando resumo financeiro no frontend

O endpoint de resumo financeiro alimenta os cards principais do dashboard.

Ele considera:

- receitas e despesas do usuario autenticado
- todas as transacoes registradas ou somente o periodo filtrado
- separacao entre despesa essencial, nao essencial e sem categoria

### Request

`GET /api/reports/summary`

Filtros opcionais:

- `month=YYYY-MM`
- `start_date=YYYY-MM-DD`
- `end_date=YYYY-MM-DD`

`month` nao pode ser combinado com `start_date` ou `end_date`. A data final e inclusiva.

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

## 21. Integrando relatorio por emocao no frontend

O endpoint de relatorio por emocao usa apenas dados do usuario autenticado.

Ele considera:

- apenas transacoes do tipo `expense`
- apenas transacoes do usuario do token
- todas as emocoes validas, mesmo quando o total for zero
- todo o historico ou somente o periodo e categoria filtrados
- uma emocao so fica apta a gerar insight apos cinco despesas em uma consulta delimitada dentro de um unico mes

### Request

`GET /api/reports/by-emotion`

Filtros opcionais: `month`, `start_date`, `end_date` e `category_id`.

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

O exemplo abaixo esta abreviado. A resposta real inclui todas as emocoes validas, inclusive aquelas com valores zerados.

```json
[
  {
    "emotion": "ansiedade",
    "label": "Ansiedade",
    "transaction_count": 2,
    "total_amount": "150.00",
    "average_amount": "75.00",
    "percentage": 62.5,
    "insight_eligible": false
  },
  {
    "emotion": "felicidade",
    "label": "Felicidade",
    "transaction_count": 1,
    "total_amount": "90.00",
    "average_amount": "90.00",
    "percentage": 37.5,
    "insight_eligible": false
  }
]
```

### Campos

- `emotion`: valor interno usado pelo backend
- `label`: texto pronto para exibicao na interface
- `transaction_count`: quantidade de despesas naquela emocao
- `total_amount`: soma das despesas naquela emocao
- `average_amount`: media das despesas naquela emocao
- `percentage`: porcentagem daquela emocao dentro do total de despesas
- `insight_eligible`: indica se existem ao menos cinco despesas especificadas em uma consulta delimitada dentro de um unico mes

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
- cards emocionais e analises futuras

---

## 22. Integrando relatorio por categoria no frontend

O endpoint de relatorio por categoria mostra onde o usuario gastou mais.

Ele considera:

- apenas transacoes do tipo `expense`
- apenas transacoes do usuario autenticado
- categorias padrao e categorias proprias do usuario
- uma linha especial chamada `Sem categoria`
- todo o historico ou somente o periodo e categoria filtrados
- categorias acessiveis sem despesas, retornadas com valores zerados
- cada subcategoria aparece separadamente da categoria pai
- `Sem categoria` representa apenas `category_id: null`; `Nao especificado` aparece como uma categoria padrao normal

### Request

`GET /api/reports/by-category`

Filtros opcionais: `month`, `start_date`, `end_date` e `category_id`.

Header:

```http
Authorization: Bearer TOKEN_AQUI
```

### Response

O exemplo abaixo esta abreviado. A resposta real tambem inclui categorias acessiveis que ainda nao possuem despesas.

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

## 22.1 Integrando o relatorio visual do RF08

`GET /api/reports/visual` entrega dados ja preparados para o dashboard. Ele aceita os filtros opcionais `month`, `start_date`, `end_date` e `category_id`.

Regras aplicadas pelo backend:

- pizza: itens inferiores a 1% e excedentes sao consolidados como `Outros`
- barras: no maximo as dez maiores categorias ou emocoes
- texto: itens que ficaram fora das barras continuam disponiveis
- insight emocional: somente emocoes especificadas com ao menos cinco despesas em uma consulta delimitada dentro de um unico mes

Cada distribuicao possui:

- `pie_items`: itens prontos para grafico de pizza
- `bar_items`: itens prontos para grafico de barras
- `textual_items`: dados menores que devem ser apresentados em texto

O frontend deve usar essas listas diretamente para manter as mesmas regras em todas as telas.

---

## 23. Integrando cruzamentos de emocao e categoria no frontend

O endpoint `/api/reports/triggers` cruza categoria e emocao e retorna apenas combinacoes que possuem despesas registradas.

Esse endpoint fornece a matriz usada em graficos. As conclusoes automaticas do RF09
sao retornadas por `/api/reports/emotion-spending-analysis`.

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

- ranking de combinacoes por `total_amount`
- mapa de calor emocao x categoria
- tabela de padroes de gasto
- cards informativos, por exemplo: `Ansiedade + Alimentacao = R$ 150,00`

### Analise completa do RF09

`GET /api/reports/emotion-spending-analysis?month=2026-06`

Filtros opcionais: `month`, `start_date`, `end_date` e `category_id`.

Principais campos da resposta:

- `conclusions_enabled`: indica se a consulta esta dentro de um unico mes
- `overall_statistics`: media geral de despesas com emocao informada
- `reference_statistics`: media ponderada das emocoes de referencia
- `emotion_analysis`: medias e classificacao geral de cada emocao
- `category_distribution`: mesma matriz retornada por `/reports/triggers`
- `category_triggers`: classificacao por emocao e categoria
- `details_by_emotion`: ate dez maiores categorias e transacoes de cada emocao com dados

Regras de classificacao:

- referencia: `calma`, `felicidade`, `indiferenca` e `satisfacao`
- candidatas: `raiva`, `frustracao`, `empolgacao`, `ansiedade`, `estresse` e `tedio`
- `not_specified` aparece como `Nao Informado`, mas nao participa das conclusoes
- a media geral tambem exclui `Nao Informado`
- exige cinco despesas candidatas e cinco despesas de referencia
- gatilho exige media candidata pelo menos 20% superior
- gatilho por categoria usa a referencia da mesma categoria
- valores exatos decidem a classificacao; percentuais arredondados servem para exibicao

Valores possiveis de `reason`:

- `trigger`
- `not_trigger`
- `period_not_single_month`
- `insufficient_candidate_data`
- `insufficient_reference_data`
- `not_candidate`

O frontend deve apresentar uma conclusao automatica somente quando
`conclusions_enabled`, `sufficient_data` e `is_trigger` forem verdadeiros.

---

## 24. Integrando transacoes recorrentes no frontend

Todas as rotas de recorrencia exigem `Authorization: Bearer <token>`.

### Criar um agendamento mensal

`POST /api/recurrences/`

```json
{
  "category_id": 1,
  "type": "expense",
  "amount": "120.00",
  "description": "Internet",
  "emotion": "not_specified",
  "frequency": "monthly",
  "day_of_month": 31,
  "start_date": "2026-06-10",
  "end_date": null
}
```

A criacao apenas salva o agendamento. Quando `day_of_month` nao for informado,
o backend usa o dia de `start_date`. Em meses sem o dia escolhido, a ocorrencia
usa o ultimo dia disponivel.

Na edicao, enviar `day_of_month: null` redefine o dia mensal para o dia de
`start_date`.

As respostas de recorrencia incluem:

- `is_active`: campo booleano mantido para verificacoes simples;
- `status: "active"`: recorrencia apta a gerar transacoes;
- `status: "paused"`: recorrencia pausada que ainda pode ser retomada;
- `status: "completed"`: recorrencia encerrada pela data final.

### Gerar ocorrencias vencidas

`POST /api/recurrences/run-due`

```json
{
  "through_date": "2026-06-10",
  "generated_count": 1,
  "generated_transactions": [
    {
      "id": 20,
      "user_id": 4,
      "category_id": 1,
      "recurrence_id": 3,
      "is_recurring": true,
      "type": "expense",
      "amount": "120.00",
      "date": "2026-06-10",
      "description": "Internet",
      "emotion": "not_specified"
    }
  ]
}
```

O frontend deve chamar esse endpoint depois do login ou ao abrir o dashboard.
Ele gera todas as ocorrencias vencidas do usuario ate hoje. A chamada pode ser
repetida com seguranca porque ocorrencias ja registradas nao sao duplicadas.
Depois da chamada, o frontend deve atualizar transacoes, relatorios e consultar
o alerta de teto de gastos.

### Regras de edicao, pausa e cancelamento

- editar uma recorrencia afeta somente transacoes futuras;
- pausar impede novas geracoes;
- retomar calcula a proxima ocorrencia a partir de hoje e ignora o periodo pausado;
- retomar uma recorrencia que ja esta ativa nao altera seu agendamento;
- uma recorrencia concluida nao pode ser retomada sem antes editar sua data final;
- cancelar remove o agendamento, mas mantem as transacoes ja registradas;
- receitas sempre usam `emotion: "not_specified"`;
- categoria e tipo precisam ser compativeis.

---

## 25. Integrando previsao de saldo no frontend

`GET /api/reports/balance-prediction`

O endpoint exige token e sempre calcula o mes atual em Brasilia. Ele nao aceita
um mes selecionavel e nao representa o saldo real de uma conta bancaria.

Formula:

```text
saldo projetado =
  receitas registradas no mes
  - despesas registradas no mes
  + receitas recorrentes pendentes no mes
  - despesas recorrentes pendentes no mes
  - estimativa de despesas variaveis restantes
```

A estimativa variavel usa a media diaria das despesas nao recorrentes dos tres
meses completos anteriores ou menos. Meses sem despesas variaveis sao ignorados.

Exemplo de resposta:

```json
{
  "month": "2026-06",
  "calculated_on": "2026-06-11",
  "days_remaining": 19,
  "current_income": "1000.00",
  "current_expense": "300.00",
  "current_month_balance": "700.00",
  "expected_future_recurring_income": "2000.00",
  "expected_future_recurring_expense": "500.00",
  "historical_daily_variable_expense_average": "20.00",
  "expected_remaining_variable_expense": "380.00",
  "predicted_end_balance": "1820.00",
  "history_months_used": [
    {
      "month": "2026-05",
      "variable_expense": "620.00",
      "days_in_month": 31
    }
  ],
  "confidence_level": "low"
}
```

Niveis de confianca:

- `insufficient`: nenhum mes completo com despesa variavel;
- `low`: um mes utilizavel;
- `medium`: dois meses utilizaveis;
- `high`: tres meses utilizaveis.

Regras de integracao:

- consultar ao abrir ou atualizar o dashboard;
- consultar novamente depois de criar, editar ou excluir uma transacao;
- consultar novamente depois de alterar ou executar recorrencias;
- valores gerados por recorrencias possuem `is_recurring: true`;
- cancelar uma recorrencia preserva `is_recurring: true` nas transacoes antigas;
- recorrencias vencidas no mes, mas ainda nao geradas, entram na projecao;
- o frontend deve deixar claro que o valor e uma estimativa do mes, nao saldo bancario.

---

## 26. Observacao importante sobre CORS

Se o frontend e o backend rodarem em origens diferentes, o navegador exige uma
permissao CORS correspondente.

Exemplo:

- frontend em `http://localhost:3000`
- backend em `http://127.0.0.1:8000`

O backend registra `CORSMiddleware` e libera por padrao:

- `http://localhost:3000`
- `http://127.0.0.1:3000`

As origens sao configuradas no `.env` do backend, separadas por virgula:

```env
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Quando o frontend utilizar outro dominio ou porta, sua origem deve ser adicionada
a essa lista e o backend deve ser reiniciado. Informe somente protocolo, host e
porta, sem `/api`, caminhos ou barra final.

Como a autenticacao atual envia JWT no header `Authorization`, o CORS nao
habilita credenciais por cookie. Origens desconhecidas nao recebem permissao do
backend e sao bloqueadas pelo navegador.

---

## 27. Resumo final

Fluxo recomendado para a integracao:

1. iniciar o backend
2. definir a URL base da API no frontend
3. criar `auth.service.ts`
4. implementar `AuthContext`
5. persistir o token no frontend
6. proteger as rotas do dashboard
7. testar `register -> login -> me -> logout`
8. aplicar o mesmo padrao nas demais funcionalidades
