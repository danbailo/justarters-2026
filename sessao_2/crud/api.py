"""Entrypoint HTTP do CRUD de processos.

Rode com: uv run fastapi dev sessao_2/crud/api.py
Docs:     http://localhost:8000/docs
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel

from sessao_2.crud.processos import Processo, Repositorio

app = FastAPI(title="PythonAPI", description="CRUD de processos")


class ProcessoEntrada(BaseModel):
    """Corpo de POST e PUT: todos os campos."""

    cnj: str
    uf: str
    comarca: str | None = None


class ProcessoParcial(BaseModel):
    """Corpo de PATCH: só os campos que mudam."""

    cnj: str | None = None
    uf: str | None = None
    comarca: str | None = None


def _repositorio() -> Repositorio:
    """Abre o repositório a cada request (lê CRUD_ARQUIVO do ambiente)."""
    return Repositorio()


Repo = Annotated[Repositorio, Depends(_repositorio)]


def _ou_404(processo: Processo | None) -> Processo:
    """Devolve o processo ou responde 404."""
    if processo is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    return processo


@app.post("/processos", status_code=201)
def criar(entrada: ProcessoEntrada, response: Response, repo: Repo) -> Processo:
    """Create: cadastra um processo e devolve 201 com o header Location."""
    processo = repo.criar(**entrada.model_dump())
    response.headers["Location"] = f"/processos/{processo.id}"
    return processo


@app.get("/processos")
def listar(repo: Repo, uf: str | None = None) -> list[Processo]:
    """Read: lista os processos; ?uf=SP filtra pelo estado."""
    return repo.listar(uf)


@app.get("/processos/{processo_id}")
def buscar(processo_id: int, repo: Repo) -> Processo:
    """Read: um processo pelo id."""
    return _ou_404(repo.buscar(processo_id))


@app.put("/processos/{processo_id}")
def substituir(processo_id: int, entrada: ProcessoEntrada, repo: Repo) -> Processo:
    """Update completo: troca todos os campos."""
    return _ou_404(repo.substituir(processo_id, **entrada.model_dump()))


@app.patch("/processos/{processo_id}")
def atualizar(processo_id: int, entrada: ProcessoParcial, repo: Repo) -> Processo:
    """Update parcial: troca só os campos enviados no body."""
    return _ou_404(repo.atualizar(processo_id, entrada.model_dump(exclude_unset=True)))


@app.delete("/processos/{processo_id}", status_code=204)
def remover(processo_id: int, repo: Repo) -> None:
    """Delete: remove o processo e responde 204, sem body."""
    if not repo.remover(processo_id):
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    return None
