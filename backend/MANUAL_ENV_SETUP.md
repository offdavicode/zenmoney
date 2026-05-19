# Configuracao Manual do .env

Este backend esta usando a opcao manual para variaveis de ambiente.

Isso significa que:

- o arquivo `.env` existe localmente
- mas o Python so vai enxergar essas variaveis se voce carregar o arquivo na sessao do terminal antes de rodar o `uvicorn`

## Arquivos envolvidos

- `.env`: valores locais do ambiente
- `.env.example`: modelo de referencia
- `config.py`: le as variaveis com `os.getenv(...)`

## Passo a passo no PowerShell

### 1. Entrar na pasta do backend

```powershell
cd "C:\Users\usuario\Documents\Codex\2026-04-27\files-mentioned-by-the-user-c\zenmoney_v2\backend"
```

### 2. Ativar o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativacao:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Conferir o conteudo do `.env`

Abra o arquivo `.env` e ajuste os valores se quiser, principalmente:

- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `MAX_LOGIN_ATTEMPTS`
- `ACCOUNT_LOCK_MINUTES`

## 4. Carregar o `.env` manualmente na sessao atual

Rode este bloco no PowerShell:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}
```

Esse comando:

- le cada linha do `.env`
- ignora linhas vazias
- separa `NOME=VALOR`
- cria cada variavel na sessao atual do terminal

## 5. Confirmar que as variaveis foram carregadas

Exemplos:

```powershell
echo $env:APP_NAME
echo $env:DATABASE_URL
echo $env:SECRET_KEY
```

Se o carregamento deu certo, o terminal vai mostrar os valores do `.env`.

## 6. Rodar a API

```powershell
uvicorn main:app --reload
```

## 7. Testar

Abra:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Importante

As variaveis carregadas dessa forma valem so para a sessao atual do terminal.

Se voce fechar o PowerShell e abrir de novo, vai precisar:

1. ativar a `.venv`
2. carregar o `.env` novamente
3. subir o `uvicorn`

## Fluxo resumido de uso diario

```powershell
cd "C:\Users\usuario\Documents\Codex\2026-04-27\files-mentioned-by-the-user-c\zenmoney_v2\backend"
.\.venv\Scripts\Activate.ps1
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}
uvicorn main:app --reload
```
