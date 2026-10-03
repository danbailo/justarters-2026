"""Testes da captura com whitelist."""

import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from cnjs import CNJS
from mock.app import DATA_DIR_PADRAO, app
from scripts.capturar import capturar, filtrar_grupo, filtrar_processo, substituir_dados
from sessao_1.solucao import de_para

GRUPO_REAL: dict = {
    "processos_categorizados": {
        "conhecimento_principal": {"id": 42, "cnj": "x", "tribunal": {"sigla": "TJSP"}, "segredo_justica": False},
        "conhecimento_recurso": [{"id": 43, "instancia": 2}],
        "execucao_principal": None,
    },
    "partes": [{"nome": "Fulano", "documento": "123.456.789-00"}],
}

PROCESSO_REAL: dict = {
    "id": 42,
    "cnj": "0000000-00.2026.8.26.0100",
    "estado": {"sigla": "SP", "nome": "São Paulo"},
    "tribunal": {"nome_normalizado": "TJSP", "sigla": "TJSP"},
    "comarca": None,
    "foro": {"nome_normalizado": "Foro Central", "codigo": 1},
    "partes": [{"nome": "Fulano", "documento": "123.456.789-00", "advogados": ["Beltrano"]}],
    "valor_acao": 1000,
}


def test_filtrar_grupo_mantem_so_ids() -> None:
    assert filtrar_grupo(GRUPO_REAL) == {
        "processos_categorizados": {
            "conhecimento_principal": {"id": 42},
            "conhecimento_recurso": [{"id": 43}],
            "execucao_principal": None,
        }
    }


def test_filtrar_processo_mantem_so_a_whitelist() -> None:
    assert filtrar_processo(PROCESSO_REAL) == {
        "id": 42,
        "estado": {"sigla": "SP"},
        "tribunal": {"nome_normalizado": "TJSP"},
        "comarca": None,
        "foro": {"nome_normalizado": "Foro Central"},
    }


def test_filtrar_processo_tolera_campo_ausente() -> None:
    assert filtrar_processo({"id": 1})["estado"] is None


def test_capturar_grava_so_dados_filtrados(tmp_path: Path) -> None:
    def responder(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/v2/grupo_processual/0000000"):
            return httpx.Response(200, json=GRUPO_REAL)
        if request.url.path == "/processo/42":
            return httpx.Response(200, json=PROCESSO_REAL)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(responder), base_url="http://x")
    capturar(["0000000-00.2026.8.26.0100", "1111111-11.2026.8.26.0100"], client, tmp_path)

    arquivos = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*.json"))
    assert arquivos == ["grupo_processual/0000000-00.2026.8.26.0100.json", "processo/42.json"]
    conteudo = "".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*.json"))
    assert "123.456.789-00" not in conteudo
    assert "Fulano" not in conteudo
    assert json.loads((tmp_path / "processo" / "42.json").read_text())["comarca"] is None


def test_mock_data_atual_roda_o_de_para(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke test sobre mock/data (sintético ou capturado): o de-para roda sem exceção."""
    monkeypatch.setenv("MOCK_DATA_DIR", str(DATA_DIR_PADRAO))
    resultados = [de_para(cnj, TestClient(app)) for cnj in CNJS]
    assert any(resultado.sucesso for resultado in resultados)


def test_substituir_dados_move_arquivos(tmp_path: Path) -> None:
    """Verifica que substituir_dados move arquivos e limpa destino antigo."""
    origem = tmp_path / "origem"
    destino = tmp_path / "destino"
    destino.mkdir()

    (origem / "grupo_processual").mkdir(parents=True)
    (origem / "grupo_processual" / "test.json").write_text('{"id": 1}')
    (destino / "processo").mkdir(parents=True)
    (destino / "processo" / "old.json").write_text('{"id": 999}')

    substituir_dados(origem, destino)

    assert (destino / "grupo_processual" / "test.json").exists()
    assert not (destino / "processo" / "old.json").exists()
    assert not (origem / "grupo_processual" / "test.json").exists()


def test_capturar_falha_nao_toca_destino(tmp_path: Path) -> None:
    """Verifica que falha na requisição não toca arquivos no destino."""
    origem = tmp_path / "origem"
    destino = tmp_path / "destino"
    origem.mkdir()
    destino.mkdir()

    (destino / "processo").mkdir()
    (destino / "processo" / "old.json").write_text('{"id": 999}')

    def responder(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/v2/grupo_processual/0000000"):
            return httpx.Response(200, json=GRUPO_REAL)
        if request.url.path == "/processo/42":
            return httpx.Response(500)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(responder), base_url="http://x")
    with pytest.raises(httpx.HTTPStatusError):
        capturar(["0000000-00.2026.8.26.0100"], client, origem)

    assert (destino / "processo" / "old.json").exists()


def test_capturar_resume_com_contadores(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verifica que capturar resume skips por razão e tempo decorrido."""
    def responder(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/v2/grupo_processual/1111111"):
            return httpx.Response(404)
        if request.url.path.startswith("/v2/grupo_processual/2222222"):
            grupo_sem_processo = {
                "processos_categorizados": {
                    "conhecimento_principal": None,
                    "conhecimento_recurso": [],
                    "execucao_principal": None,
                }
            }
            return httpx.Response(200, json=grupo_sem_processo)
        if request.url.path.startswith("/v2/grupo_processual/0000000"):
            return httpx.Response(200, json=GRUPO_REAL)
        if request.url.path == "/processo/42":
            return httpx.Response(200, json=PROCESSO_REAL)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(responder), base_url="http://x")
    capturar(["1111111-11.2026.8.26.0100", "2222222-22.2026.8.26.0100", "0000000-00.2026.8.26.0100"], client, tmp_path)

    captured = capsys.readouterr()
    assert "1 gravados" in captured.out
    assert "1 nao_encontrado" in captured.out
    assert "1 grupo_sem_processos" in captured.out
    assert "s:" in captured.out
