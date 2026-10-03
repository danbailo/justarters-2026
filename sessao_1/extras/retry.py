"""Retry com backoff exponencial para erros 5xx.

Rode com um mock instável:
    MOCK_FAIL_RATE=0.5 uv run fastapi dev mock/app.py
    uv run python -m sessao_1.extras.retry
"""

import os
import time

import httpx

from sessao_1.solucao import BASE_URL_PADRAO


def get_com_retry(
    client: httpx.Client,
    url: str,
    tentativas: int = 3,
    espera_base: float = 0.2,
) -> httpx.Response:
    """GET que repete em erro 5xx, esperando 0.2 s, 0.4 s, 0.8 s...

    Erros 4xx não são repetidos: repetir não muda a resposta.

    Args:
        client: Cliente HTTP.
        url: Caminho a buscar.
        tentativas: Total de chamadas, contando a primeira.
        espera_base: Espera antes da segunda chamada; dobra a cada nova falha.

    Returns:
        A primeira resposta abaixo de 500, ou a última resposta se todas falharem.
    """
    resposta = client.get(url)
    for tentativa in range(1, tentativas):
        if resposta.status_code < 500:
            return resposta
        espera = espera_base * 2 ** (tentativa - 1)
        print(f"Tentativa {tentativa} falhou com {resposta.status_code}; nova tentativa em {espera:.1f} s")
        time.sleep(espera)
        resposta = client.get(url)
    if resposta.status_code >= 500:
        print(f"Desisti depois de {tentativas} tentativas: {url} -> {resposta.status_code}")
    return resposta


if __name__ == "__main__":
    with httpx.Client(base_url=os.environ.get("BASE_URL", BASE_URL_PADRAO), timeout=10) as client:
        for _ in range(5):
            print(get_com_retry(client, "/processo/1001").status_code)
