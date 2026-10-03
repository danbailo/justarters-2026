"""Exemplo de testes com pytest para o de-para.

Rode com: uv run pytest sessao_1/extras
"""

from sessao_1.solucao import Localizacao, escolher_processo_id, extrair_localizacao


def test_usa_o_processo_principal() -> None:
    grupo = {"processos_categorizados": {"conhecimento_principal": {"id": 1}}}
    assert escolher_processo_id(grupo) == 1


def test_sem_principal_pega_o_primeiro_encontrado() -> None:
    grupo = {"processos_categorizados": {"conhecimento_principal": None, "conhecimento_recurso": [{"id": 2}]}}
    assert escolher_processo_id(grupo) == 2


def test_comarca_nula_deixa_a_localizacao_incompleta() -> None:
    processo = {
        "estado": {"sigla": "SP"},
        "tribunal": {"nome_normalizado": "TRT2"},
        "comarca": None,
        "foro": {"nome_normalizado": "37ª Vara do Trabalho"},
    }
    localizacao = extrair_localizacao(processo)
    assert localizacao == Localizacao("SP", "TRT2", None, "37ª Vara do Trabalho")
    assert localizacao.completa() is False
