"""Demo: `time.sleep` dentro de `async def` trava o servidor inteiro.

Rode o servidor e dispare carga com o cliente:
    uv run fastapi dev sessao_2/extras/demo_bloqueio.py
    uv run python -m sessao_2.cliente carga --caminho /bloqueante -n 10   # ~10 s
    uv run python -m sessao_2.cliente carga --caminho /livre -n 10        # ~1 s
"""

import asyncio
import os
import time

from fastapi import FastAPI

app = FastAPI(title="Demo: event loop bloqueado vs livre")


def _espera() -> float:
    """Segundos de espera por request (env DEMO_ESPERA, padrão 1).

    Returns:
        Tempo em segundos a aguardar.
    """
    return float(os.environ.get("DEMO_ESPERA", "1"))


@app.get("/bloqueante")
async def bloqueante() -> dict:
    """ERRADO: time.sleep bloqueia o event loop; os requests passam a ser atendidos um por vez.

    Returns:
        Resposta JSON com o nome da rota.
    """
    time.sleep(_espera())
    return {"rota": "bloqueante"}


@app.get("/livre")
async def livre() -> dict:
    """CERTO: await asyncio.sleep devolve o controle ao event loop enquanto espera.

    Returns:
        Resposta JSON com o nome da rota.
    """
    await asyncio.sleep(_espera())
    return {"rota": "livre"}
