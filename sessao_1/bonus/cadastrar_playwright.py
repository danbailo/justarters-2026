"""Cadastra os de-paras no Google Form pelo navegador, como um robô.

Rode com o mock no ar (o navegador abre na tela):
    uv sync --group bonus && uv run playwright install chromium
    uv run python -m sessao_1.bonus.cadastrar_playwright

HEADLESS=1 roda sem janela (necessário no Codespaces).
"""

import os
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from cnjs import CNJS
from sessao_1.bonus.comum import FORM_URL, executar_cadastro, imprimir_resumo
from sessao_1.solucao import BASE_URL_PADRAO, ResultadoDePara, rodar

CONFIRMACAO: str = "Sua resposta foi registrada"


def preencher_e_enviar(page: Page, resultado: ResultadoDePara) -> bool:
    """Abre o form, preenche os cinco campos e envia.

    Args:
        page: Aba do navegador.
        resultado: De-para com sucesso.

    Returns:
        True quando a página de confirmação apareceu.
    """
    loc = resultado.localizacao
    assert loc is not None
    try:
        page.goto(f"{FORM_URL}/viewform")
        campos = {
            "CNJ": resultado.cnj,
            "Estado": loc.estado or "",
            "Tribunal": loc.tribunal or "",
            "Comarca": loc.comarca or "",
            "Foro": loc.foro or "",
        }
        for rotulo, valor in campos.items():
            page.get_by_role("textbox", name=rotulo).fill(valor)
        page.get_by_role("button", name="Enviar").click()
        page.get_by_text(CONFIRMACAO).wait_for(timeout=10_000)
    except PlaywrightError as e:
        print(f"Erro ao preencher {resultado.cnj}: {e}")
        return False
    return True


def main() -> None:
    """De-para dos CNJs e cadastro via navegador, com cronômetro."""
    resultados = rodar(CNJS, os.environ.get("BASE_URL", BASE_URL_PADRAO))
    headless = os.environ.get("HEADLESS") == "1"
    print("Iniciando os cadastros via Playwright...")
    inicio = time.perf_counter()
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=headless, slow_mo=0 if headless else 150)
        try:
            page = navegador.new_page(locale="pt-BR")
            resumo = executar_cadastro(resultados, lambda resultado: preencher_e_enviar(page, resultado))
        finally:
            navegador.close()
    imprimir_resumo(resumo)
    print(f"Tempo de cadastro: {time.perf_counter() - inicio:.2f} s")
    print("Cadastros via Playwright finalizados!")


if __name__ == "__main__":
    main()
