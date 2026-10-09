"""Entrypoint de linha de comando do CRUD: as mesmas regras da API, outro jeito de chamar.

    uv run python -m sessao_2.crud.cli criar --cnj 0000121-97.1999.8.16.0048 --uf PR
    uv run python -m sessao_2.crud.cli listar --uf PR
    uv run python -m sessao_2.crud.cli buscar 1
    uv run python -m sessao_2.crud.cli atualizar 1 --comarca Curitiba
    uv run python -m sessao_2.crud.cli remover 1
"""

import argparse
import sys

from sessao_2.crud.processos import Repositorio


def _parser() -> argparse.ArgumentParser:
    """Monta os subcomandos da CLI."""
    parser = argparse.ArgumentParser(description="CRUD de processos pela linha de comando")
    sub = parser.add_subparsers(dest="comando", required=True)
    criar = sub.add_parser("criar")
    criar.add_argument("--cnj", required=True)
    criar.add_argument("--uf", required=True)
    criar.add_argument("--comarca")
    listar = sub.add_parser("listar")
    listar.add_argument("--uf")
    sub.add_parser("buscar").add_argument("id", type=int)
    atualizar = sub.add_parser("atualizar")
    atualizar.add_argument("id", type=int)
    atualizar.add_argument("--cnj")
    atualizar.add_argument("--uf")
    atualizar.add_argument("--comarca")
    sub.add_parser("remover").add_argument("id", type=int)
    return parser


def main(argv: list[str]) -> None:
    """Executa um comando do CRUD e imprime o resultado.

    Args:
        argv: Argumentos da linha de comando, sem o nome do programa.
    """
    args = _parser().parse_args(argv)
    repo = Repositorio()
    if args.comando == "criar":
        print(f"Criado: {repo.criar(args.cnj, args.uf, args.comarca)}")
        return None
    if args.comando == "listar":
        processos = repo.listar(args.uf)
        for processo in processos:
            print(processo)
        print(f"{len(processos)} processo(s)")
        return None
    if args.comando == "buscar":
        print(repo.buscar(args.id) or f"Processo {args.id} não encontrado")
        return None
    if args.comando == "atualizar":
        campos = {campo: getattr(args, campo) for campo in ("cnj", "uf", "comarca") if getattr(args, campo) is not None}
        print(repo.atualizar(args.id, campos) or f"Processo {args.id} não encontrado")
        return None
    removido = repo.remover(args.id)
    print(f"Processo {args.id} removido" if removido else f"Processo {args.id} não encontrado")
    return None


if __name__ == "__main__":
    main(sys.argv[1:])
