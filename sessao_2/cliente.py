"""Cliente pronto da sessão 2.

    uv run python -m sessao_2.cliente checar                         # 200 / 404 / 401
    uv run python -m sessao_2.cliente carga --caminho /livre -n 10   # demo de async
"""

import argparse
import asyncio
import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from mock.app import DATA_DIR_PADRAO, primeiro_id_existente


@dataclass
class Checagem:
    """Uma verificação de status HTTP."""

    nome: str
    esperado: int
    obtido: int

    @property
    def ok(self) -> bool:
        """True quando o status obtido é o esperado.

        Returns:
            True se status obtido confere com esperado, False caso contrário.
        """
        return self.esperado == self.obtido


def checar(client: httpx.Client, api_key: str, processo_id: int) -> list[Checagem]:
    """Roda as quatro verificações do hands-on contra a API.

    Args:
        client: Cliente apontado para a API da turma.
        api_key: Chave válida.
        processo_id: Id de um processo existente.

    Returns:
        Uma Checagem por caso.
    """
    casos = [
        ("Processo existente, com API key", f"/processo/{processo_id}", {"X-API-KEY": api_key}, 200),
        ("Processo inexistente", "/processo/999999", {"X-API-KEY": api_key}, 404),
        ("Sem API key", f"/processo/{processo_id}", {}, 401),
        ("API key errada", f"/processo/{processo_id}", {"X-API-KEY": "errada"}, 401),
    ]
    return [
        Checagem(nome, esperado, client.get(caminho, headers=headers).status_code)
        for nome, caminho, headers, esperado in casos
    ]


async def carga(client: httpx.AsyncClient, caminho: str, n: int) -> float:
    """Dispara n requests simultâneos e devolve os segundos até o último responder.

    Args:
        client: Cliente HTTP assíncrono.
        caminho: Rota a chamar.
        n: Quantidade de requests.

    Returns:
        Tempo total em segundos.
    """
    inicio = time.perf_counter()
    await asyncio.gather(*(client.get(caminho) for _ in range(n)))
    return time.perf_counter() - inicio


async def _carga_cli(base_url: str, caminho: str, n: int) -> float:
    """Abre o cliente assíncrono e roda a carga.

    Args:
        base_url: URL base do servidor.
        caminho: Rota a chamar.
        n: Número de requests simultâneos.

    Returns:
        Tempo total em segundos.
    """
    async with httpx.AsyncClient(base_url=base_url, timeout=60) as client:
        return await carga(client, caminho, n)


def main() -> None:
    """Interface de linha de comando."""
    parser = argparse.ArgumentParser(description="Cliente da sessão 2")
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8000"))
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("checar")
    parser_carga = sub.add_parser("carga")
    parser_carga.add_argument("--caminho", default="/livre")
    parser_carga.add_argument("-n", type=int, default=10)
    args = parser.parse_args()

    if args.comando == "carga":
        segundos = asyncio.run(_carga_cli(args.base_url, args.caminho, args.n))
        print(f"{args.n} requests em {args.caminho}: {segundos:.2f} s")
        return None

    processo_id = primeiro_id_existente(Path(os.environ.get("MOCK_DATA_DIR", DATA_DIR_PADRAO)))
    with httpx.Client(base_url=args.base_url, timeout=10) as client:
        for checagem in checar(client, os.environ.get("API_KEY", "justarters"), processo_id):
            status = "OK    " if checagem.ok else "FALHOU"
            print(f"{status} {checagem.nome}: esperado {checagem.esperado}, obtido {checagem.obtido}")
    return None


if __name__ == "__main__":
    main()
