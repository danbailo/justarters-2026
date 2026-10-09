"""Testes do CRUD de processos: núcleo, API e CLI."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sessao_2.crud.api import app
from sessao_2.crud.cli import main
from sessao_2.crud.processos import Processo, Repositorio

CNJ: str = "0000121-97.1999.8.16.0048"


@pytest.fixture(autouse=True)
def _arquivo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    arquivo = tmp_path / "processos.json"
    monkeypatch.setenv("CRUD_ARQUIVO", str(arquivo))
    return arquivo


def test_repositorio_crud_completo() -> None:
    repo = Repositorio()
    criado = repo.criar(CNJ, "PR")
    assert criado == Processo(1, CNJ, "PR", None)
    assert repo.criar("1001227-41.2025.5.02.0037", "SP").id == 2
    assert repo.listar("PR") == [criado]
    assert repo.atualizar(1, {"comarca": "Curitiba"}) == Processo(1, CNJ, "PR", "Curitiba")
    assert repo.substituir(1, CNJ, "SP") == Processo(1, CNJ, "SP", None)
    assert repo.remover(1) is True
    assert repo.buscar(1) is None
    assert repo.remover(1) is False
    assert repo.atualizar(1, {"uf": "SP"}) is None
    assert repo.substituir(1, CNJ, "SP") is None


def test_api_fluxo_completo() -> None:
    client = TestClient(app)
    resposta = client.post("/processos", json={"cnj": CNJ, "uf": "PR"})
    assert resposta.status_code == 201
    assert resposta.headers["Location"] == "/processos/1"
    assert client.get("/processos", params={"uf": "PR"}).json() == [{"id": 1, "cnj": CNJ, "uf": "PR", "comarca": None}]
    assert client.patch("/processos/1", json={"comarca": "Curitiba"}).json()["comarca"] == "Curitiba"
    assert client.get("/processos/1").json()["uf"] == "PR"
    assert client.put("/processos/1", json={"cnj": CNJ, "uf": "SP"}).json() == {"id": 1, "cnj": CNJ, "uf": "SP", "comarca": None}
    assert client.delete("/processos/1").status_code == 204
    assert client.get("/processos/1").status_code == 404


@pytest.mark.parametrize("metodo", ["get", "patch", "put", "delete"])
def test_api_404(metodo: str) -> None:
    corpo = {"patch": {"uf": "SP"}, "put": {"cnj": CNJ, "uf": "SP"}}.get(metodo)
    resposta = TestClient(app).request(metodo.upper(), "/processos/99", json=corpo)
    assert resposta.status_code == 404


def test_cli_e_api_compartilham_os_dados(capsys: pytest.CaptureFixture[str]) -> None:
    main(["criar", "--cnj", CNJ, "--uf", "PR"])
    assert TestClient(app).get("/processos/1").json()["cnj"] == CNJ
    main(["atualizar", "1", "--comarca", "Curitiba"])
    main(["listar"])
    main(["remover", "1"])
    main(["buscar", "1"])
    saida = capsys.readouterr().out
    assert "Criado: Processo(id=1" in saida
    assert "comarca='Curitiba'" in saida
    assert "1 processo(s)" in saida
    assert "Processo 1 removido" in saida
    assert "Processo 1 não encontrado" in saida


def test_contrato_da_goapi_igual_ao_da_pythonapi() -> None:
    spec_python = app.openapi()
    spec_go = json.loads((Path(__file__).parents[1] / "sessao_2/crud_go/openapi.json").read_text(encoding="utf-8"))
    assert spec_python["info"]["title"] == "PythonAPI"
    assert spec_go["info"]["title"] == "GoAPI"
    assert spec_go["paths"] == spec_python["paths"]
    assert spec_go["components"] == spec_python["components"]
