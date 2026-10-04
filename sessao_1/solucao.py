"""De-para de processo: CNJ -> localização (solução da sessão 1).

Fluxo:
    1. GET /v2/grupo_processual/{cnj}
    2. Escolhe o processo principal (ou o primeiro encontrado)
    3. GET /processo/{id}
    4. Extrai estado, tribunal, comarca e foro

Rode com: uv run python -m sessao_1.solucao
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
    """Escolhe o processo do grupo: o principal ou, sem ele, o primeiro encontrado.

    Args:
        grupo: Resposta de /v2/grupo_processual/{cnj}.

    Returns:
        O id do processo, ou None quando o grupo não tem nenhum processo.
    """
    categorias = grupo.get("processos_categorizados") or {}
    principal = categorias.get("conhecimento_principal")
    if principal:
        return principal["id"]
    for valor in categorias.values():
        if isinstance(valor, dict):
            return valor["id"]
        if isinstance(valor, list) and valor:
            return valor[0]["id"]
    return None


def _nome_normalizado(processo: dict, campo: str) -> str | None:
    """Lê `processo[campo]["nome_normalizado"]`, tolerando campo ausente ou nulo."""
    return (processo.get(campo) or {}).get("nome_normalizado")


def extrair_localizacao(processo: dict) -> Localizacao:
    """Extrai a localização de uma resposta de /processo/{id}.

    Args:
        processo: Resposta de /processo/{id}.

    Returns:
        A localização. Campos ausentes viram None.
    """
    return Localizacao(
        estado=(processo.get("estado") or {}).get("sigla"),
        tribunal=_nome_normalizado(processo, "tribunal"),
        comarca=_nome_normalizado(processo, "comarca"),
        foro=_nome_normalizado(processo, "foro"),
    )


def de_para(cnj: str, client: httpx.Client) -> ResultadoDePara:
    """Faz o de-para de um CNJ para a localização do processo.

    Args:
        cnj: Número CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO).
        client: Cliente HTTP já apontado para a consulta-api (ou o mock).

    Returns:
        O resultado, com sucesso=True só quando a localização está completa.

    Raises:
        httpx.HTTPStatusError: Erro HTTP diferente de 404 no grupo.
    """
    resposta = client.get(f"/v2/grupo_processual/{cnj}")
    if resposta.status_code == 404:
        return ResultadoDePara(cnj, sucesso=False, motivo="CNJ não encontrado")
    resposta.raise_for_status()

    processo_id = escolher_processo_id(resposta.json())
    if processo_id is None:
        return ResultadoDePara(cnj, sucesso=False, motivo="Grupo sem processos")

    resposta = client.get(f"/processo/{processo_id}")
    resposta.raise_for_status()
    localizacao = extrair_localizacao(resposta.json())
    if not localizacao.completa():
        return ResultadoDePara(cnj, sucesso=False, localizacao=localizacao, motivo="Localização incompleta")
    return ResultadoDePara(cnj, sucesso=True, localizacao=localizacao)


def imprimir_relatorio(resultados: list[ResultadoDePara]) -> None:
    """Imprime uma linha por CNJ e o total de sucessos.

    Args:
        resultados: Resultados do de-para.
    """
    for resultado in resultados:
        if resultado.sucesso and resultado.localizacao:
            loc = resultado.localizacao
            print(f"OK     {resultado.cnj}  {loc.estado} | {loc.tribunal} | {loc.comarca} | {loc.foro}")
            continue
        print(f"FALHA  {resultado.cnj}  {resultado.motivo}")
    sucessos = sum(resultado.sucesso for resultado in resultados)
    print(f"\n{sucessos}/{len(resultados)} CNJs com localização completa")


def _processar(cnjs: list[str], client: httpx.Client) -> list[ResultadoDePara]:
    """Roda o de-para de cada CNJ em sequência, mostrando o progresso.

    Args:
        cnjs: CNJs a processar.
        client: Cliente HTTP já apontado para o mock.

    Returns:
        Um resultado por CNJ, na mesma ordem.
    """
    resultados = []
    for indice, cnj in enumerate(cnjs, start=1):
        print(f"Progresso {indice}/{len(cnjs)}: {cnj}")
        resultados.append(de_para(cnj, client))
    return resultados


def rodar(cnjs: list[str], base_url: str) -> list[ResultadoDePara]:
    """Roda o de-para para cada CNJ, em sequência.

    Args:
        cnjs: CNJs a processar.
        base_url: URL da consulta-api ou do mock.

    Returns:
        Um resultado por CNJ, na mesma ordem.
    """
    print(f"Iniciando o de-para de {len(cnjs)} CNJs em {base_url}...")
    try:
        with httpx.Client(base_url=base_url, timeout=10) as client:
            resultados = _processar(cnjs, client)
    except httpx.ConnectError:
        sys.exit(
            f"Não consegui conectar em {base_url}. "
            "O mock está rodando? Suba com: uv run fastapi dev mock/app.py"
        )
    print("De-para finalizado!")
    return resultados


if __name__ == "__main__":
    imprimir_relatorio(rodar(CNJS, os.environ.get("BASE_URL", BASE_URL_PADRAO)))
