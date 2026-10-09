# Justarters 2026 - Kit de exercícios

Kit das sessões **Introdução ao Python** e **Comunicação via APIs**.
Roda 100% offline: um mock local imita a `consulta-api` do Jusbrasil.

## Setup

**Opção 1 - Codespaces (sem instalar nada):**

1. Entre na sua conta do GitHub (crie uma, se ainda não tiver).
2. Abra https://codespaces.new/danbailo/justarters-2026 e clique em **Create codespace**.
   O mesmo vale pelo botão **Code > Codespaces > Create codespace** no repositório.
3. Espere de 1 a 3 minutos na primeira vez: o ambiente sobe com Python, `uv` e as dependências já instaladas.
   Crie o seu antes da aula começar.

Cada pessoa ganha o próprio Codespace, na própria conta: o que você editar fica só nele e não altera
este repositório. O uso sai da cota gratuita de Codespaces da sua conta.

Para abrir uma API que você subiu (ex.: `uv run fastapi dev mock/app.py`), clique em **Open in Browser**
no aviso da porta 8000, ou abra a aba **Ports**, e acrescente `/docs` na URL.
Um servidor por vez: todos usam a porta 8000, então pare o anterior (Ctrl+C) antes de subir outro.

**Opção 2 - Local:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # instala o uv
uv sync                                            # instala as dependências
```

Todos os comandos abaixo rodam a partir da raiz do repositório.

## Sessão 1 - Introdução ao Python

Fundamentos, do "Hello World!" às exceções:

```bash
uv run python -m sessao_1.fundamentos            # todos os temas
uv run python -m sessao_1.fundamentos excecoes   # um tema só
```

Hands-on do de-para:

```bash
uv run fastapi dev mock/app.py          # terminal 1: sobe o mock em http://localhost:8000
uv run python -m sessao_1.exercicio     # terminal 2: seu exercício
uv run python -m sessao_1.solucao       # a solução
```

Extras:

```bash
uv run python -m sessao_1.extras.sync_vs_async   # cronômetro: sync vs async
MOCK_FAIL_RATE=0.5 uv run fastapi dev mock/app.py
uv run python -m sessao_1.extras.retry           # retry com backoff contra um mock instável
uv run pytest sessao_1/extras                    # exemplo de testes
```

Cada servidor usa a porta 8000: pare o anterior (Ctrl+C) antes de iniciar outro e, depois do retry, reinicie o mock sem `MOCK_FAIL_RATE`.

Variáveis do mock: `MOCK_LATENCY_MS` (padrão 500), `MOCK_FAIL_RATE` (padrão 0).
Com acesso à `consulta-api` real via proxy, rode o exercício com `BASE_URL=http://localhost:8074`.

### Bônus - cadastrar no "sistema do cliente"

Demo do instrutor: envia respostas a um formulário real, não rode sem combinar.

```bash
uv sync --group bonus && uv run playwright install chromium
uv run python -m sessao_1.bonus.cadastrar_requests
uv run python -m sessao_1.bonus.cadastrar_playwright
```

No Codespaces (sem janela): `uv run playwright install --with-deps chromium` e `HEADLESS=1` ao rodar o Playwright.

## Sessão 2 - Comunicação via APIs

```bash
uv run fastapi dev sessao_2/exercicio/app.py      # sua API em http://localhost:8000
uv run python -m sessao_2.cliente checar          # testa 200 / 404 / 401
uv run fastapi dev sessao_2/solucao/app.py        # a solução
```

A API key padrão é `justarters` (env `API_KEY`).

Extras:

```bash
uv run fastapi dev sessao_2/extras/demo_bloqueio.py
uv run python -m sessao_2.cliente carga --caminho /bloqueante -n 10
uv run python -m sessao_2.cliente carga --caminho /livre -n 10
uv run pytest sessao_2/extras
```

### CRUD de processos: o mesmo núcleo, dois entrypoints

```bash
uv run fastapi dev sessao_2/crud/api.py                                      # entrypoint HTTP
uv run python -m sessao_2.crud.cli criar --cnj 0000121-97.1999.8.16.0048 --uf PR   # entrypoint CLI
uv run python -m sessao_2.crud.cli listar
```

A PythonAPI, a CLI e a GoAPI gravam no mesmo arquivo (`sessao_2/crud/processos.json`, env `CRUD_ARQUIVO`),
então o que você cria por um aparece nos outros.

A mesma API em Go (precisa do Go instalado, não vem no Codespaces): `cd sessao_2/crud_go && go run .`
sobe em http://localhost:8080. Swagger das duas: http://localhost:8000/docs (PythonAPI) e
http://localhost:8080/docs (GoAPI). O `openapi.json` da GoAPI é gerado do FastAPI; um teste garante
que os dois contratos continuam iguais.

## Antes de cada sessão (instrutor)

```bash
uv run pytest
```

Os dados em `mock/data` foram capturados da consulta-api com whitelist de campos (`scripts/capturar.py`); para voltar aos sintéticos: `uv run python -m scripts.gerar_sinteticos mock/data`.
