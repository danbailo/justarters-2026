"""Cadastra os de-paras no Google Form com um POST direto (sem navegador).

O endpoint /formResponse não é API oficial do Google: funciona em form
público, mas pode mudar sem aviso.

Rode com o mock no ar:
    uv run python -m sessao_1.bonus.cadastrar_requests
"""

import os
import time

import requests

from cnjs import CNJS
from sessao_1.bonus.comum import FORM_URL, executar_cadastro, imprimir_resumo, montar_payload
from sessao_1.solucao import BASE_URL_PADRAO, ResultadoDePara, rodar


def enviar_via_requests(resultado: ResultadoDePara, session: requests.Session) -> bool:
    """Envia um de-para com POST no /formResponse.

    Args:
        resultado: De-para com sucesso.
        session: Sessão HTTP reaproveitada entre os envios.

    Returns:
        True quando o Google respondeu 200.
    """
    try:
        resposta = session.post(f"{FORM_URL}/formResponse", data=montar_payload(resultado), timeout=10)
        return resposta.status_code == 200
    except requests.RequestException as e:
        print(f"Erro ao enviar {resultado.cnj}: {e}")
        return False


def main() -> None:
    """De-para dos CNJs e cadastro via requests, com cronômetro."""
    resultados = rodar(CNJS, os.environ.get("BASE_URL", BASE_URL_PADRAO))
    inicio = time.perf_counter()
    with requests.Session() as session:
        resumo = executar_cadastro(resultados, lambda resultado: enviar_via_requests(resultado, session))
    imprimir_resumo(resumo)
    print(f"Tempo de cadastro: {time.perf_counter() - inicio:.2f} s")


if __name__ == "__main__":
    main()
