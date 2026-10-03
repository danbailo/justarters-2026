"""Testes do bônus de cadastro no Google Form."""

from unittest.mock import MagicMock
import pytest
import requests

from sessao_1.bonus.cadastrar_requests import enviar_via_requests
from sessao_1.bonus.comum import CAMPOS, FORM_URL, executar_cadastro, montar_payload
from sessao_1.solucao import Localizacao, ResultadoDePara

OK: ResultadoDePara = ResultadoDePara("0000121-97.1999.8.16.0048", True, Localizacao("PR", "TJPR", "Curitiba", "Foro Central"))
INCOMPLETO: ResultadoDePara = ResultadoDePara("1001227-41.2025.5.02.0037", False, Localizacao("SP", "TRT2", None, "37ª Vara"), "Localização incompleta")


def test_form_e_campos_do_spec() -> None:
    assert FORM_URL == "https://docs.google.com/forms/d/e/1FAIpQLSciaeAzDZI8233vcPUgvPua1YcMQVCCdeLEppHsLq0-gs1uKA"
    assert CAMPOS == {
        "cnj": "entry.1564099154",
        "estado": "entry.939829063",
        "tribunal": "entry.323214906",
        "comarca": "entry.1170186343",
        "foro": "entry.697666039",
    }


def test_montar_payload() -> None:
    assert montar_payload(OK) == {
        "entry.1564099154": "0000121-97.1999.8.16.0048",
        "entry.939829063": "PR",
        "entry.323214906": "TJPR",
        "entry.1170186343": "Curitiba",
        "entry.697666039": "Foro Central",
    }


def test_executar_cadastro_pula_sem_sucesso_e_registra_falhas() -> None:
    falha = ResultadoDePara("5046688-52.2025.8.13.0702", True, Localizacao("MG", "TJMG", "Uberlândia", "JEC"))
    enviar_um = MagicMock(side_effect=[True, False])
    resumo = executar_cadastro([OK, INCOMPLETO, falha], enviar_um)
    assert resumo.enviados == [OK.cnj]
    assert resumo.falhas == [falha.cnj]
    assert resumo.pulados == [INCOMPLETO]
    assert [chamada.args[0] for chamada in enviar_um.call_args_list] == [OK, falha]


def test_enviar_via_requests_posta_no_form_response() -> None:
    session = MagicMock()
    session.post.return_value.status_code = 200
    assert enviar_via_requests(OK, session) is True
    session.post.assert_called_once_with(f"{FORM_URL}/formResponse", data=montar_payload(OK), timeout=10)


def test_enviar_via_requests_falha_quando_status_nao_e_200() -> None:
    session = MagicMock()
    session.post.return_value.status_code = 400
    assert enviar_via_requests(OK, session) is False


def test_enviar_via_requests_retorna_false_quando_conexao_falha() -> None:
    session: MagicMock = MagicMock()
    session.post.side_effect = requests.ConnectionError("Network error")
    assert enviar_via_requests(OK, session) is False


def test_preencher_e_enviar_retorna_false_com_erro_playwright() -> None:
    pytest.importorskip("playwright")
    from sessao_1.bonus.cadastrar_playwright import preencher_e_enviar
    from playwright.sync_api import Error as PlaywrightError

    page: MagicMock = MagicMock()
    page.goto.side_effect = PlaywrightError("Navigation failed")
    assert preencher_e_enviar(page, OK) is False


def test_preencher_e_enviar_retorna_true_no_caminho_feliz() -> None:
    pytest.importorskip("playwright")
    from sessao_1.bonus.cadastrar_playwright import preencher_e_enviar

    page: MagicMock = MagicMock()
    page.get_by_text.return_value.wait_for = MagicMock()
    assert preencher_e_enviar(page, OK) is True
