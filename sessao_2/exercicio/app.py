"""Hands-on da sessão 2: construa a API de processos.

Complete os TODOs na ordem dos passos. Rode e teste com:
    uv run fastapi dev sessao_2/exercicio/app.py
    uv run python -m sessao_2.cliente checar
"""

import json
import os
import pathlib

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

from mock.app import DATA_DIR_PADRAO

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

app = FastAPI(title="API de processos - minha versão")


def _data_dir() -> pathlib.Path:
    """Pasta com os JSONs: processo/<id>.json e grupo_processual/<cnj>.json."""
    return pathlib.Path(os.environ.get("MOCK_DATA_DIR", DATA_DIR_PADRAO))


def exigir_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Passo 3: valida o header X-API-KEY."""
    # TODO Passo 3: compare api_key com os.environ.get("API_KEY", "justarters").
    #   Se faltar ou não bater: raise HTTPException(status_code=401, detail="API key ausente ou inválida")
    #   Depois, adicione dependencies=[Depends(exigir_api_key)] no @app.get abaixo.
    return None


# TODO Passo 1: crie a rota GET /processo/{processo_id} (processo_id: int)
#   que lê e devolve json.loads(caminho.read_text()) de _data_dir() / "processo" / f"{processo_id}.json".
# TODO Passo 2: se o arquivo não existir, raise HTTPException(status_code=404, detail="Não encontrado").
# TODO Passo 4: abra http://localhost:8000/docs, clique em Authorize e teste com a chave.
