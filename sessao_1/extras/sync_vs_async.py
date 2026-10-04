"""Cronômetro: de-para dos CNJs em sequência (sync) vs concorrente (async).

Rode com o mock no ar (latência padrão de 500 ms):
    uv run python -m sessao_1.extras.sync_vs_async
"""

import asyncio
import os
import time

import httpx

from cnjs import CNJS
from sessao_1.solucao import (
    BASE_URL_PADRAO,
    ResultadoDePara,
    escolher_processo_id,
    extrair_localizacao,
    rodar,
)


async def de_para_async(cnj: str, client: httpx.AsyncClient) -> ResultadoDePara:
    """Mesmo de-para da solução, com `await` nas chamadas HTTP.

    Args:
        cnj: Número CNJ.
        client: Cliente HTTP assíncrono apontado para o mock.

    Returns:
        O resultado do de-para.
    """
    resposta = await client.get(f"/v2/grupo_processual/{cnj}")
    if resposta.status_code == 404:
        return ResultadoDePara(cnj, sucesso=False, motivo="CNJ não encontrado")
    resposta.raise_for_status()

    processo_id = escolher_processo_id(resposta.json())
    if processo_id is None:
        return ResultadoDePara(cnj, sucesso=False, motivo="Grupo sem processos")

    resposta = await client.get(f"/processo/{processo_id}")
    resposta.raise_for_status()
    localizacao = extrair_localizacao(resposta.json())
    if not localizacao.completa():
        return ResultadoDePara(cnj, sucesso=False, localizacao=localizacao, motivo="Localização incompleta")
    return ResultadoDePara(cnj, sucesso=True, localizacao=localizacao)


async def rodar_async(cnjs: list[str], client: httpx.AsyncClient, limite: int) -> list[ResultadoDePara]:
    """Roda o de-para de todos os CNJs ao mesmo tempo, com no máximo `limite` em voo.

    Args:
        cnjs: CNJs a processar.
        client: Cliente HTTP assíncrono.
        limite: Máximo de CNJs processados simultaneamente (protege o upstream).

    Returns:
        Um resultado por CNJ, na mesma ordem de `cnjs`.
    """
    semaforo = asyncio.Semaphore(limite)
    concluidos = 0

    async def _com_limite(cnj: str) -> ResultadoDePara:
        nonlocal concluidos
        async with semaforo:
            resultado = await de_para_async(cnj, client)
        concluidos += 1
        print(f"Progresso {concluidos}/{len(cnjs)}: {cnj}")
        return resultado

    return list(await asyncio.gather(*(_com_limite(cnj) for cnj in cnjs)))


async def _rodar_async_cronometrado(base_url: str) -> float:
    """Executa a versão async e devolve os segundos gastos."""
    print(f"Iniciando o de-para async de {len(CNJS)} CNJs, até 5 ao mesmo tempo...")
    inicio = time.perf_counter()
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        await rodar_async(CNJS, client, limite=5)
    print("De-para async finalizado!")
    return time.perf_counter() - inicio


def main() -> None:
    """Imprime o tempo das duas versões."""
    base_url = os.environ.get("BASE_URL", BASE_URL_PADRAO)
    print("Iniciando a comparação sync vs async...")
    inicio = time.perf_counter()
    rodar(CNJS, base_url)
    sync = time.perf_counter() - inicio
    assincrono = asyncio.run(_rodar_async_cronometrado(base_url))
    print(f"Sync  (um por vez):           {sync:5.2f} s")
    print(f"Async (até 5 ao mesmo tempo): {assincrono:5.2f} s")
    print("Comparação finalizada!")


if __name__ == "__main__":
    main()
