"""Testes dos extras da sessão 1."""

import asyncio
import time
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from cnjs import CNJS
from mock.app import app
from sessao_1.extras.retry import get_com_retry
from sessao_1.extras.sync_vs_async import rodar_async
from sessao_1.solucao import ResultadoDePara, de_para


def _rodar_async(limite: int) -> list[ResultadoDePara]:
    async def _executar() -> list[ResultadoDePara]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await rodar_async(CNJS, client, limite)

    return asyncio.run(_executar())


def test_rodar_async_da_o_mesmo_resultado_que_o_sync() -> None:
    sync = [de_para(cnj, TestClient(app)) for cnj in CNJS]
    assert _rodar_async(limite=11) == sync


def test_rodar_async_respeita_o_limite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_LATENCY_MS", "50")
    inicio = time.perf_counter()
    _rodar_async(limite=1)
    sequencial = time.perf_counter() - inicio
    inicio = time.perf_counter()
    _rodar_async(limite=11)
    concorrente = time.perf_counter() - inicio
    assert sequencial >= 1.0
    assert concorrente < sequencial / 3


@dataclass
class ClienteFalso:
    client: httpx.Client
    chamadas: MagicMock


def _client_com_respostas(*status: int) -> ClienteFalso:
    chamadas = MagicMock(side_effect=[httpx.Response(codigo) for codigo in status])
    return ClienteFalso(httpx.Client(transport=httpx.MockTransport(chamadas), base_url="http://x"), chamadas)


@patch("sessao_1.extras.retry.time.sleep")
def test_get_com_retry_recupera_depois_de_503(sleep: MagicMock) -> None:
    falso = _client_com_respostas(503, 503, 200)
    assert get_com_retry(falso.client, "/processo/1").status_code == 200
    assert falso.chamadas.call_count == 3
    assert [chamada.args[0] for chamada in sleep.call_args_list] == [0.2, 0.4]


@patch("sessao_1.extras.retry.time.sleep")
def test_get_com_retry_desiste_depois_das_tentativas(sleep: MagicMock) -> None:
    falso = _client_com_respostas(503, 503, 503)
    assert get_com_retry(falso.client, "/processo/1").status_code == 503
    assert falso.chamadas.call_count == 3


@patch("sessao_1.extras.retry.time.sleep")
def test_get_com_retry_nao_repete_erro_4xx(sleep: MagicMock) -> None:
    falso = _client_com_respostas(404)
    assert get_com_retry(falso.client, "/processo/1").status_code == 404
    assert falso.chamadas.call_count == 1
    sleep.assert_not_called()
