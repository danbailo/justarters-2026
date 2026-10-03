"""Mock da consulta-api para os exercícios do Justarters.

Serve as duas rotas usadas pelo de-para, no mesmo formato da consulta-api
real, a partir de JSONs em MOCK_DATA_DIR (padrão: mock/data).

Rode com: uv run fastapi dev mock/app.py
"""

import asyncio
import json
import os
import pathlib
import random
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path

DATA_DIR_PADRAO: pathlib.Path = pathlib.Path(__file__).parent / "data"
CNJ_PATTERN: str = r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$"

app = FastAPI(title="consulta-api (mock)")


def _data_dir() -> pathlib.Path:
    """Diretório de dados, lido do ambiente a cada request."""
    return pathlib.Path(os.environ.get("MOCK_DATA_DIR", DATA_DIR_PADRAO))


def _ler_json(caminho: pathlib.Path) -> dict:
    """Lê um JSON de resposta ou devolve 404.

    Args:
        caminho: Arquivo da resposta.

    Returns:
        O conteúdo do arquivo.

    Raises:
        HTTPException: 404 quando o arquivo não existe.
    """
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Não encontrado")
    return json.loads(caminho.read_text(encoding="utf-8"))


async def _simular_upstream() -> None:
    """Aplica a latência (MOCK_LATENCY_MS) e a falha aleatória (MOCK_FAIL_RATE).

    Raises:
        HTTPException: 503 quando a falha aleatória é sorteada.
    """
    await asyncio.sleep(int(os.environ.get("MOCK_LATENCY_MS", "500")) / 1000)
    if random.random() < float(os.environ.get("MOCK_FAIL_RATE", "0")):
        raise HTTPException(status_code=503, detail="Upstream indisponível")


@app.get("/v2/grupo_processual/{cnj}")
async def grupo_processual(cnj: Annotated[str, Path(pattern=CNJ_PATTERN)]) -> dict:
    """Grupo processual de um CNJ (formato NNNNNNN-DD.AAAA.J.TR.OOOO)."""
    await _simular_upstream()
    return _ler_json(_data_dir() / "grupo_processual" / f"{cnj}.json")


@app.get("/processo/{processo_id}")
async def processo(processo_id: int) -> dict:
    """Dados de um processo pelo id interno."""
    await _simular_upstream()
    return _ler_json(_data_dir() / "processo" / f"{processo_id}.json")
