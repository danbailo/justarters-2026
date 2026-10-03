"""API de processos protegida por X-API-KEY (solução da sessão 2).

Rode com: uv run fastapi dev sessao_2/solucao/app.py
Docs:     http://localhost:8000/docs (botão Authorize, chave padrão "justarters")
"""

import json
import os
import pathlib
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from mock.app import CNJ_PATTERN, DATA_DIR_PADRAO

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

app = FastAPI(title="API de processos - Justarters")


class Estado(BaseModel):
    """Estado do processo, só com a sigla."""

    sigla: str | None


class Nome(BaseModel):
    """Entidade identificada só pelo nome normalizado (tribunal, comarca, foro)."""

    nome_normalizado: str | None


class Processo(BaseModel):
    """Processo com os campos de localização."""

    id: int
    estado: Estado | None
    tribunal: Nome | None
    comarca: Nome | None
    foro: Nome | None


def exigir_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> None:
    """Exige o header X-API-KEY igual ao env API_KEY (padrão "justarters").

    Args:
        api_key: Valor do header X-API-KEY, pode ser None.

    Raises:
        HTTPException: 401 quando a chave falta ou não confere.
    """
    esperada = os.environ.get("API_KEY", "justarters")
    if api_key is None or not secrets.compare_digest(api_key, esperada):
        raise HTTPException(status_code=401, detail="API key ausente ou inválida")
    return None


def _ler_json(caminho: pathlib.Path) -> dict:
    """Lê um JSON de dados ou devolve 404.

    Args:
        caminho: Arquivo a ler.

    Returns:
        O conteúdo do arquivo como dict.

    Raises:
        HTTPException: 404 quando o arquivo não existe.
    """
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Não encontrado")
    return json.loads(caminho.read_text(encoding="utf-8"))


def _data_dir() -> pathlib.Path:
    """Diretório de dados, compartilhado com o mock da sessão 1.

    Returns:
        Caminho do diretório de dados.
    """
    return pathlib.Path(os.environ.get("MOCK_DATA_DIR", DATA_DIR_PADRAO))


@app.get("/processo/{processo_id}", response_model=Processo, dependencies=[Depends(exigir_api_key)])
def processo(processo_id: int) -> dict:
    """Dados de localização de um processo.

    Args:
        processo_id: ID do processo.

    Returns:
        Dados do processo.
    """
    return _ler_json(_data_dir() / "processo" / f"{processo_id}.json")


@app.get("/v2/grupo_processual/{cnj}", dependencies=[Depends(exigir_api_key)])
def grupo_processual(cnj: Annotated[str, Path(pattern=CNJ_PATTERN)]) -> dict:
    """Grupo processual de um CNJ.

    Args:
        cnj: CNJ no formato NNNNNNN-DD.AAAA.J.TR.OOOO.

    Returns:
        Dados do grupo processual.
    """
    return _ler_json(_data_dir() / "grupo_processual" / f"{cnj}.json")
