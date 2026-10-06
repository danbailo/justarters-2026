"""Testes do script de fundamentos da sessão 1."""

import pytest

from sessao_1.fundamentos import Processo, _classificar, _sigla_do_estado, _tipo_de_justica, main


def test_tipo_de_justica() -> None:
    assert _tipo_de_justica("0000121-97.1999.8.16.0048") == "Justiça Estadual"
    assert _tipo_de_justica("1001227-41.2025.5.02.0037") == "Justiça do Trabalho"
    assert _tipo_de_justica("5000001-00.2024.4.04.7000") == "Justiça Federal"
    assert _tipo_de_justica("0000000-00.2026.1.00.0000") == "Outra justiça"


def test_classificar() -> None:
    assert _classificar({}) == "Processo vazio"
    assert _classificar({"comarca": None}) == "Localização incompleta"
    assert _classificar({"comarca": "Curitiba"}) == "Localização completa"


def test_sigla_do_estado() -> None:
    assert _sigla_do_estado({"estado": {"sigla": "SP"}}) == "SP"
    assert _sigla_do_estado({"estado": None}) is None


def test_localizacao_completa() -> None:
    assert Processo("x", "TJPR", "Curitiba").localizacao_completa() is True
    assert Processo("x", "TRT2").localizacao_completa() is False


def test_main_roda_todos_os_temas(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    saida = capsys.readouterr().out
    assert "Iniciando os fundamentos: 11 tema(s)..." in saida
    assert "Hello World!" in saida
    assert "ValueError capturado" in saida
    assert "Progresso 11/11: dataclasses" in saida
    assert saida.rstrip().endswith("Fundamentos finalizados!")


def test_main_roda_um_tema(capsys: pytest.CaptureFixture[str]) -> None:
    main(["excecoes"])
    saida = capsys.readouterr().out
    assert "Progresso 1/1: excecoes" in saida
    assert "Hello World!" not in saida


def test_main_tema_desconhecido() -> None:
    with pytest.raises(SystemExit) as erro:
        main(["nao-existe"])
    assert "Tema desconhecido: nao-existe" in str(erro.value)
