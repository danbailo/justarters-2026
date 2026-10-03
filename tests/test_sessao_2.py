"""Testes da sessão 2: API com X-API-KEY, cliente e demo de bloqueio."""

import asyncio
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from sessao_2.cliente import carga, checar, primeiro_id_existente
from sessao_2.extras.demo_bloqueio import app as demo_app
from sessao_2.solucao.app import app

client: TestClient = TestClient(app)
CHAVE: dict[str, str] = {"X-API-KEY": "justarters"}


def test_processo_com_api_key() -> None:
    resposta = client.get("/processo/1001", headers=CHAVE)
    assert resposta.status_code == 200
    assert resposta.json()["foro"] == {"nome_normalizado": "Foro Central"}


def test_processo_inexistente() -> None:
    assert client.get("/processo/999999", headers=CHAVE).status_code == 404


def test_sem_api_key() -> None:
    assert client.get("/processo/1001").status_code == 401


def test_api_key_errada() -> None:
    assert client.get("/processo/1001", headers={"X-API-KEY": "errada"}).status_code == 401


def test_api_key_vem_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "outra")
    assert client.get("/processo/1001", headers=CHAVE).status_code == 401
    assert client.get("/processo/1001", headers={"X-API-KEY": "outra"}).status_code == 200


def test_grupo_processual_exige_api_key() -> None:
    cnj = "0000121-97.1999.8.16.0048"
    assert client.get(f"/v2/grupo_processual/{cnj}").status_code == 401
    assert client.get(f"/v2/grupo_processual/{cnj}", headers=CHAVE).status_code == 200


def test_docs_continua_publico() -> None:
    assert client.get("/docs").status_code == 200


def test_primeiro_id_existente_le_diretorio(tmp_path: Path) -> None:
    (tmp_path / "processo").mkdir()
    (tmp_path / "processo" / "77.json").write_text("{}")
    (tmp_path / "processo" / "5.json").write_text("{}")
    assert primeiro_id_existente(tmp_path) == 5


def test_checar_passa_contra_a_solucao() -> None:
    checagens = checar(client, "justarters", 1001)
    assert [checagem.esperado for checagem in checagens] == [200, 404, 401, 401]
    assert all(checagem.ok for checagem in checagens)


def _carga(caminho: str, n: int) -> float:
    async def _executar() -> float:
        transport = httpx.ASGITransport(app=demo_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            return await carga(async_client, caminho, n)

    return asyncio.run(_executar())


def test_demo_bloqueante_serializa_e_livre_nao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_ESPERA", "0.2")
    assert _carga("/bloqueante", 5) >= 1.0
    assert _carga("/livre", 5) < 0.6
