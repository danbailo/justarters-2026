# Justarters 2026 - Kit de exercícios

Kit das sessões **Introdução ao Python** e **Comunicação via APIs**.
Roda 100% offline: um mock local imita a `consulta-api` do Jusbrasil.

## Setup

**Opção 1 - Codespaces (sem instalar nada):** botão **Code > Codespaces > Create codespace**.
O ambiente já sobe com Python e as dependências.

**Opção 2 - Local:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # instala o uv
uv sync                                            # instala as dependências
```

Todos os comandos abaixo rodam a partir desta pasta.

## Sessão 1 - Introdução ao Python

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

Variáveis do mock: `MOCK_LATENCY_MS` (padrão 500), `MOCK_FAIL_RATE` (padrão 0).
Com acesso à `consulta-api` real via proxy, rode o exercício com `BASE_URL=http://localhost:8074`.

### Bônus - cadastrar no "sistema do cliente"

```bash
uv sync --group bonus && uv run playwright install chromium
uv run python -m sessao_1.bonus.cadastrar_requests
uv run python -m sessao_1.bonus.cadastrar_playwright
```

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

## Antes de cada sessão (instrutor)

```bash
uv run pytest
```

Os dados em `mock/data` são sintéticos até a captura (`scripts/capturar.py`).
