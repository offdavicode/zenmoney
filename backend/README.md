# ZenMoney Backend v2

Backend reorganizado seguindo a arquitetura MVC em camadas descrita em
`../ARCHITECTURE_v2.md`.

## Estrutura

- `main.py`: ponto de entrada do FastAPI
- `database.py`: engine, sessao, base ORM e criacao de tabelas
- `models/`: tabelas SQLAlchemy
- `schemas/`: validacao de entrada e saida com Pydantic
- `routers/`: endpoints HTTP
- `services/`: regras de negocio
- `utils/`: seguranca e datas

## Dependencias

As dependencias estao listadas em `requirements.txt`.

## Como instalar localmente

1. Instale Python 3.11 ou superior
2. Crie um ambiente virtual:
   - `python -m venv .venv`
3. Ative o ambiente virtual
4. Instale as dependencias:
   - `pip install -r requirements.txt`
5. Inicie a API:
   - `uvicorn main:app --reload`

## Observacao desta versao

Esta etapa entrega a base estrutural da arquitetura v2 e os stubs das features. As regras de negocio vao sendo preenchidas na ordem que voce definir.
