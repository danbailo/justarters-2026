"""Fundamentos de Python, do "Hello World!" às exceções.

Rode todos os temas:   uv run python -m sessao_1.fundamentos
Rode um tema só:       uv run python -m sessao_1.fundamentos excecoes

Temas: hello, tipos, textos, listas, dicionarios, funcoes, fstrings, condicionais,
excecoes, comprehensions, dataclasses.

Dica: f"{expressao = }" imprime a expressão e o valor dela, por isso aparece tanto aqui.
"""

import sys
from collections.abc import Callable
from dataclasses import dataclass

CNJS: list[str] = [
    "0000121-97.1999.8.16.0048",
    "1001227-41.2025.5.02.0037",
    "5000001-00.2024.4.04.7000",
]


@dataclass
class Processo:
    """Um processo com o mínimo para saber onde ele tramita."""

    cnj: str
    tribunal: str
    comarca: str | None = None

    def localizacao_completa(self) -> bool:
        """True quando a comarca está preenchida."""
        return self.comarca is not None


def hello() -> None:
    """O primeiro programa de toda linguagem."""
    print("Hello World!")


def tipos() -> None:
    """Tipos básicos e conversões entre eles."""
    cnj = "0000121-97.1999.8.16.0048"
    processo_id = 1001
    valor_da_causa = 15000.50
    sucesso = True
    comarca = None
    print(f"{cnj = }", type(cnj))
    print(f"{processo_id = }", type(processo_id))
    print(f"{valor_da_causa = }", type(valor_da_causa))
    print(f"{sucesso = }", type(sucesso))
    print(f"{comarca = }", type(comarca))
    print(f'{int("42") + 1 = }')
    print(f'{float("3.5") * 2 = }')
    print(f"{str(processo_id) + '!' = }")
    print(f'{bool("") = }  {bool("texto") = }')


def textos() -> None:
    """Operações comuns com str."""
    cnj = "0000121-97.1999.8.16.0048"
    tribunal = "tribunal de justiça do paraná"
    print(f"{tribunal.upper() = }")
    print(f"{tribunal.title() = }")
    print(f"{len(cnj) = }")
    print(f"{cnj[:7] = }")
    print(f'{cnj.split(".") = }')
    print(f'{cnj.replace("-", "").replace(".", "") = }')
    print(f'{"8.16" in cnj = }')


def listas() -> None:
    """Criar, acessar, alterar e percorrer uma list."""
    cnjs = ["0000121-97.1999.8.16.0048", "1001227-41.2025.5.02.0037"]
    cnjs.append("5000001-00.2024.4.04.7000")
    print(f"{cnjs = }")
    print(f"{len(cnjs) = }")
    print(f"{cnjs[0] = }")
    print(f"{cnjs[-1] = }")
    for indice, cnj in enumerate(cnjs, start=1):
        print(f"Progresso {indice}/{len(cnjs)}: {cnj}")


def dicionarios() -> None:
    """Criar, acessar e percorrer um dict, inclusive aninhado."""
    processo = {"id": 1001, "estado": {"sigla": "PR"}, "comarca": None}
    print(f'{processo["id"] = }')
    print(f'{processo["estado"]["sigla"] = }')
    print(f'{processo.get("foro") = }')
    print(f'{processo.get("foro", "sem foro") = }')
    processo["foro"] = "Foro Central"
    for chave, valor in processo.items():
        print(f"{chave}: {valor}")


def _sigla_do_estado(processo: dict) -> str | None:
    """Lê processo["estado"]["sigla"] sem quebrar quando o estado não existe.

    Args:
        processo: Processo no formato da consulta-api.

    Returns:
        A sigla do estado, ou None.
    """
    estado = processo.get("estado") or {}
    return estado.get("sigla")


def funcoes() -> None:
    """Uma função com type hints, chamada com e sem dado."""
    print(f'{_sigla_do_estado({"estado": {"sigla": "SP"}}) = }')
    print(f"{_sigla_do_estado({}) = }")


def fstrings() -> None:
    """Montar texto: concatenação vs f-string, e formatação de números."""
    cnj = "0000121-97.1999.8.16.0048"
    tribunal = "TJPR"
    segundos = 2.25619
    print("Concatenação: CNJ " + cnj + " no " + tribunal)
    print(f"f-string:     CNJ {cnj} no {tribunal}")
    print(f"Duas casas:   levou {segundos:.2f} s")


def _tipo_de_justica(cnj: str) -> str:
    """Tipo de justiça pelo dígito J do CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO).

    Args:
        cnj: Número CNJ.

    Returns:
        O nome do tipo de justiça.
    """
    justica = cnj.split(".")[2]
    if justica == "8":
        return "Justiça Estadual"
    elif justica == "5":
        return "Justiça do Trabalho"
    elif justica == "4":
        return "Justiça Federal"
    else:
        return "Outra justiça"


def _classificar(processo: dict) -> str:
    """Guard clauses: trata o caso ruim primeiro e sai cedo.

    Args:
        processo: Processo como dict.

    Returns:
        A classificação da localização.
    """
    if not processo:
        return "Processo vazio"
    if processo.get("comarca") is None:
        return "Localização incompleta"
    return "Localização completa"


def condicionais() -> None:
    """if/elif/else, None e guard clauses."""
    for cnj in CNJS:
        print(f"{cnj} -> {_tipo_de_justica(cnj)}")
    for processo in [{}, {"comarca": None}, {"comarca": "Curitiba"}]:
        print(f"{processo} -> {_classificar(processo)}")


def excecoes() -> None:
    """Erros comuns, capturados para o programa seguir rodando."""
    try:
        int("abc")
    except ValueError as erro:
        print(f"ValueError capturado: {erro}")
    try:
        10 / 0
    except ZeroDivisionError as erro:
        print(f"ZeroDivisionError capturado: {erro}")
    processo = {"id": 1001}
    try:
        processo["comarca"]
    except KeyError as erro:
        print(f"KeyError capturado: a chave {erro} não existe")
    finally:
        print("O finally roda sempre, com ou sem erro")


def comprehensions() -> None:
    """Criar listas e dicts em uma linha a partir de outra lista."""
    print(f"{[cnj[:7] for cnj in CNJS] = }")
    print(f'{[cnj for cnj in CNJS if cnj.split(".")[2] == "8"] = }')
    justica_por_numero = {cnj[:7]: _tipo_de_justica(cnj) for cnj in CNJS}
    print(f"{justica_por_numero = }")
    print(f"{sum([True, False, True]) = }")


def dados_com_dataclass() -> None:
    """Uma classe só com dados, com tipos e um método."""
    completo = Processo("0000121-97.1999.8.16.0048", "TJPR", "Curitiba")
    incompleto = Processo("1001227-41.2025.5.02.0037", "TRT2")
    print(f"{completo = }")
    print(f"{completo.localizacao_completa() = }")
    print(f"{incompleto = }")
    print(f"{incompleto.localizacao_completa() = }")


def main(argv: list[str]) -> None:
    """Roda os temas pedidos na linha de comando, ou todos.

    Args:
        argv: Nomes dos temas. Vazio roda todos.
    """
    temas: dict[str, Callable[[], None]] = {
        "hello": hello,
        "tipos": tipos,
        "textos": textos,
        "listas": listas,
        "dicionarios": dicionarios,
        "funcoes": funcoes,
        "fstrings": fstrings,
        "condicionais": condicionais,
        "excecoes": excecoes,
        "comprehensions": comprehensions,
        "dataclasses": dados_com_dataclass,
    }
    escolhidos = argv or list(temas)
    desconhecidos = [nome for nome in escolhidos if nome not in temas]
    if desconhecidos:
        sys.exit(f"Tema desconhecido: {', '.join(desconhecidos)}. Opções: {', '.join(temas)}")
    print(f"Iniciando os fundamentos: {len(escolhidos)} tema(s)...")
    for indice, nome in enumerate(escolhidos, start=1):
        print(f"\n=== Progresso {indice}/{len(escolhidos)}: {nome} ===")
        temas[nome]()
    print("\nFundamentos finalizados!")
    return None


if __name__ == "__main__":
    main(sys.argv[1:])
