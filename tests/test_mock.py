"""Testes do mock da consulta-api."""

import time

import pytest
from fastapi.testclient import TestClient

from mock.app import app

client: TestClient = TestClient(app)


def test_grupo_existente_retorna_principal() -> None:
    resposta = client.get("/v2/grupo_processual/0000121-97.1999.8.16.0048")
    assert resposta.status_code == 200
    assert resposta.json()["processos_categorizados"]["conhecimento_principal"]["id"] == 1001


def test_grupo_inexistente_retorna_404() -> None:
    resposta = client.get("/v2/grupo_processual/1234567-89.2026.8.26.0100")
    assert resposta.status_code == 404


def test_cnj_com_formato_invalido_retorna_422() -> None:
    resposta = client.get("/v2/grupo_processual/nao-e-um-cnj")
    assert resposta.status_code == 422


def test_processo_sem_comarca() -> None:
    resposta = client.get("/processo/1004")
    assert resposta.status_code == 200
    assert resposta.json()["comarca"] is None


def test_processo_inexistente_retorna_404() -> None:
    resposta = client.get("/processo/999999")
    assert resposta.status_code == 404


def test_latencia_configuravel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_LATENCY_MS", "200")
    inicio = time.perf_counter()
    client.get("/processo/1001")
    assert time.perf_counter() - inicio >= 0.2


def test_falha_configuravel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_FAIL_RATE", "1")
    resposta = client.get("/processo/1001")
    assert resposta.status_code == 503
