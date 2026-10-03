"""Hands-on da sessão 1: de-para de processo, CNJ -> localização.

Complete os TODOs na ordem dos passos e rode:
    uv run python -m sessao_1.exercicio

O mock precisa estar no ar em outro terminal:
    uv run fastapi dev mock/app.py
"""

import os
import sys
from dataclasses import dataclass

import httpx

from cnjs import CNJS

BASE_URL_PADRAO: str = "http://localhost:8000"


@dataclass
class Localizacao:
    """Onde o processo tramita."""

    estado: str | None
    tribunal: str | None
    comarca: str | None
    foro: str | None

    def completa(self) -> bool:
        """True quando os quatro campos estão preenchidos."""
        return all([self.estado, self.tribunal, self.comarca, self.foro])


@dataclass
class ResultadoDePara:
    """Resultado do de-para de um CNJ."""

    cnj: str
    sucesso: bool
    localizacao: Localizacao | None = None
    motivo: str | None = None


def escolher_processo_id(grupo: dict) -> int | None:
    """Passo 2: escolhe o processo do grupo.

    Args:
        grupo: Resposta de /v2/grupo_processual/{cnj}.

    Returns:
        O id do processo, ou None quando o grupo não tem nenhum processo.
    """
    # TODO Passo 2a: pegue grupo["processos_categorizados"]["conhecimento_principal"].
    #   Se existir, devolva o "id" dele.
    # TODO Passo 2b: se for None, percorra os valores de processos_categorizados e
    #   devolva o id do primeiro processo encontrado (o valor pode ser um dict ou uma lista).
    # TODO Passo 2c: se nada for encontrado, devolva None.
    raise NotImplementedError("Passo 2")


def extrair_localizacao(processo: dict) -> Localizacao:
    """Passo 4: extrai a localização de uma resposta de /processo/{id}.

    Args:
        processo: Resposta de /processo/{id}.

    Returns:
        A localização. Campos ausentes viram None.
    """
    # TODO Passo 4: estado -> processo["estado"]["sigla"]
    #   tribunal, comarca e foro -> processo[campo]["nome_normalizado"]
    #   Cuidado: qualquer um deles pode vir None.
    raise NotImplementedError("Passo 4")


def de_para(cnj: str, client: httpx.Client) -> ResultadoDePara:
    """Faz o de-para de um CNJ.

    Args:
        cnj: Número CNJ.
        client: Cliente HTTP já apontado para o mock.

    Returns:
        O resultado, com sucesso=True só quando a localização está completa.
    """
    # TODO Passo 1: client.get(f"/v2/grupo_processual/{cnj}")
    #   Se o status for 404, devolva ResultadoDePara(cnj, sucesso=False, motivo="CNJ não encontrado").
    # TODO Passo 2: processo_id = escolher_processo_id(resposta.json())
    #   Se for None, devolva sucesso=False com motivo="Grupo sem processos".
    # TODO Passo 3: client.get(f"/processo/{processo_id}")
    # TODO Passo 4: localizacao = extrair_localizacao(resposta.json())
    #   sucesso=True só se localizacao.completa(); senão motivo="Localização incompleta".
    raise NotImplementedError("Passos 1 a 4")


def imprimir_relatorio(resultados: list[ResultadoDePara]) -> None:
    """Imprime uma linha por CNJ e o total de sucessos."""
    for resultado in resultados:
        print(resultado)
    sucessos = sum(resultado.sucesso for resultado in resultados)
    print(f"\n{sucessos}/{len(resultados)} CNJs com localização completa")


def rodar(cnjs: list[str], base_url: str) -> list[ResultadoDePara]:
    """Roda o de-para para cada CNJ, em sequência."""
    try:
        with httpx.Client(base_url=base_url, timeout=10) as client:
            return [de_para(cnj, client) for cnj in cnjs]
    except httpx.ConnectError:
        sys.exit(
            f"Não consegui conectar em {base_url}. "
            "O mock está rodando? Suba com: uv run fastapi dev mock/app.py"
        )


if __name__ == "__main__":
    imprimir_relatorio(rodar(CNJS, os.environ.get("BASE_URL", BASE_URL_PADRAO)))
