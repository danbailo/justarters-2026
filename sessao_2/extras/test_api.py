"""Exemplo de testes de API com TestClient.

Rode com: uv run pytest sessao_2/extras
"""

from fastapi.testclient import TestClient

from sessao_2.solucao.app import app

client: TestClient = TestClient(app)


def test_com_chave_responde_200() -> None:
    assert client.get("/processo/1001", headers={"X-API-KEY": "justarters"}).status_code == 200


def test_sem_chave_responde_401() -> None:
    assert client.get("/processo/1001").status_code == 401
