"""Testes da solução do de-para (sessão 1)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mock.app import app
from sessao_1.solucao import (
    Localizacao,
    de_para,
    escolher_processo_id,
    extrair_localizacao,
    rodar,
)

client: TestClient = TestClient(app)


def test_escolher_processo_id_usa_principal() -> None:
    grupo = {"processos_categorizados": {"conhecimento_recurso": [{"id": 9}], "conhecimento_principal": {"id": 7}}}
    assert escolher_processo_id(grupo) == 7


def test_escolher_processo_id_fallback_para_primeiro_encontrado() -> None:
    grupo = {"processos_categorizados": {"conhecimento_principal": None, "execucao": [], "conhecimento_recurso": [{"id": 9}, {"id": 10}]}}
    assert escolher_processo_id(grupo) == 9


def test_escolher_processo_id_fallback_aceita_objeto() -> None:
    grupo = {"processos_categorizados": {"conhecimento_principal": None, "execucao_principal": {"id": 5}}}
    assert escolher_processo_id(grupo) == 5


def test_escolher_processo_id_grupo_vazio() -> None:
    grupo = {"processos_categorizados": {"conhecimento_principal": None, "execucao": [], "execucao_principal": None}}
    assert escolher_processo_id(grupo) is None


def test_extrair_localizacao_completa() -> None:
    processo = {
        "estado": {"sigla": "SP"},
        "tribunal": {"nome_normalizado": "TJSP"},
        "comarca": {"nome_normalizado": "Garça"},
        "foro": {"nome_normalizado": "1ª Vara"},
    }
    assert extrair_localizacao(processo) == Localizacao("SP", "TJSP", "Garça", "1ª Vara")


def test_extrair_localizacao_tolera_ausentes() -> None:
    processo = {"tribunal": {"nome_normalizado": None}, "comarca": None}
    assert extrair_localizacao(processo) == Localizacao(None, None, None, None)


def test_localizacao_completa_exige_os_quatro_campos() -> None:
    assert Localizacao("SP", "TJSP", "Garça", "1ª Vara").completa() is True
    assert Localizacao("SP", "TJSP", None, "1ª Vara").completa() is False


def test_de_para_sucesso() -> None:
    resultado = de_para("0000121-97.1999.8.16.0048", client)
    assert resultado.sucesso is True
    assert resultado.localizacao == Localizacao("PR", "Tribunal de Justiça do Paraná", "Curitiba", "Foro Central")
    assert resultado.motivo is None


def test_de_para_sem_principal_usa_fallback() -> None:
    resultado = de_para("0000545-48.2012.8.26.0132", client)
    assert resultado.sucesso is True
    assert resultado.localizacao is not None
    assert resultado.localizacao.comarca == "Garça"


def test_de_para_localizacao_incompleta() -> None:
    resultado = de_para("1001227-41.2025.5.02.0037", client)
    assert resultado.sucesso is False
    assert resultado.motivo == "Localização incompleta"


def test_de_para_cnj_inexistente() -> None:
    resultado = de_para("1234567-89.2026.8.26.0100", client)
    assert resultado.sucesso is False
    assert resultado.motivo == "CNJ não encontrado"


def test_de_para_grupo_vazio(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cnj = "9999999-99.2026.8.26.0100"
    (tmp_path / "grupo_processual").mkdir()
    (tmp_path / "grupo_processual" / f"{cnj}.json").write_text('{"processos_categorizados": {"conhecimento_principal": null}}')
    monkeypatch.setenv("MOCK_DATA_DIR", str(tmp_path))
    resultado = de_para(cnj, client)
    assert resultado.sucesso is False
    assert resultado.motivo == "Grupo sem processos"


def test_rodar_sem_mock_sai_com_mensagem() -> None:
    with pytest.raises(SystemExit) as erro:
        rodar(["0000121-97.1999.8.16.0048"], "http://127.0.0.1:9")
    assert "fastapi dev mock/app.py" in str(erro.value)
