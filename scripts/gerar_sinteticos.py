"""Gera os JSONs sintéticos da consulta-api num diretório de destino.

Uso: uv run python -m scripts.gerar_sinteticos <destino>
"""

import json
import sys
from pathlib import Path

PROCESSOS: list[dict] = [
    {"id": 1001, "cnj": "0000121-97.1999.8.16.0048", "uf": "PR", "tribunal": "Tribunal de Justiça do Paraná", "comarca": "Curitiba", "foro": "Foro Central"},
    {"id": 1002, "cnj": "0000336-31.2013.8.26.0169", "uf": "SP", "tribunal": "Tribunal de Justiça de São Paulo", "comarca": "Tanabi", "foro": "Vara Única"},
    {"id": 1003, "cnj": "0000545-48.2012.8.26.0132", "uf": "SP", "tribunal": "Tribunal de Justiça de São Paulo", "comarca": "Garça", "foro": "1ª Vara"},
    {"id": 1004, "cnj": "1001227-41.2025.5.02.0037", "uf": "SP", "tribunal": "Tribunal Regional do Trabalho da 2ª Região", "comarca": None, "foro": "37ª Vara do Trabalho de São Paulo"},
    {"id": 1005, "cnj": "0007627-21.2025.5.05.0000", "uf": "BA", "tribunal": "Tribunal Regional do Trabalho da 5ª Região", "comarca": "Salvador", "foro": "Tribunal Pleno"},
    {"id": 1006, "cnj": "0004083-39.2025.8.12.0110", "uf": "MS", "tribunal": "Tribunal de Justiça do Mato Grosso do Sul", "comarca": "Campo Grande", "foro": "Juizado Especial Cível"},
    {"id": 1007, "cnj": "1050631-71.2025.8.11.0001", "uf": "MT", "tribunal": "Tribunal de Justiça do Mato Grosso", "comarca": "Cuiabá", "foro": "Vara Cível"},
    {"id": 1008, "cnj": "5046688-52.2025.8.13.0702", "uf": "MG", "tribunal": "Tribunal de Justiça de Minas Gerais", "comarca": "Uberlândia", "foro": "Juizado Especial Cível"},
    {"id": 1009, "cnj": "5046683-30.2025.8.13.0702", "uf": "MG", "tribunal": "Tribunal de Justiça de Minas Gerais", "comarca": "Uberlândia", "foro": "Juizado Especial Cível"},
    {"id": 1010, "cnj": "5002107-62.2025.8.13.0051", "uf": "MG", "tribunal": "Tribunal de Justiça de Minas Gerais", "comarca": "Bambuí", "foro": "Vara Única"},
]

SEM_PRINCIPAL: set[int] = {1003}


def _nome(valor: str | None) -> dict | None:
    """Envolve um nome no formato `{"nome_normalizado": ...}` da consulta-api.

    Args:
        valor: Nome ou None.

    Returns:
        O objeto da consulta-api, ou None quando o nome não existe.
    """
    if valor is None:
        return None
    return {"nome_normalizado": valor}


def _grupo(processo: dict) -> dict:
    """Monta a resposta de /v2/grupo_processual para um processo.

    Args:
        processo: Item de PROCESSOS.

    Returns:
        Grupo processual com o processo como principal, ou como recurso quando
        o id está em SEM_PRINCIPAL.
    """
    resumo = {"id": processo["id"], "cnj": processo["cnj"]}
    sem_principal = processo["id"] in SEM_PRINCIPAL
    return {
        "processos_categorizados": {
            "conhecimento_principal": None if sem_principal else resumo,
            "conhecimento_recurso": [resumo] if sem_principal else [],
            "conhecimento_apenso": [],
            "execucao": [],
            "execucao_principal": None,
            "indefinida": [],
        }
    }


def _processo(processo: dict) -> dict:
    """Monta a resposta de /processo/{id}.

    Args:
        processo: Item de PROCESSOS.

    Returns:
        Processo com os campos de localização.
    """
    return {
        "id": processo["id"],
        "cnj": processo["cnj"],
        "estado": {"sigla": processo["uf"]},
        "tribunal": _nome(processo["tribunal"]),
        "comarca": _nome(processo["comarca"]),
        "foro": _nome(processo["foro"]),
    }


def gerar(destino: Path) -> None:
    """Escreve grupo_processual/<cnj>.json e processo/<id>.json em destino.

    Args:
        destino: Diretório raiz dos dados (ex.: mock/data).
    """
    (destino / "grupo_processual").mkdir(parents=True, exist_ok=True)
    (destino / "processo").mkdir(parents=True, exist_ok=True)
    print(f"Iniciando a geração de {len(PROCESSOS)} processos sintéticos em {destino}...")
    for indice, processo in enumerate(PROCESSOS, start=1):
        print(f"Progresso {indice}/{len(PROCESSOS)}: {processo['cnj']}")
        grupo_path = destino / "grupo_processual" / f"{processo['cnj']}.json"
        grupo_path.write_text(json.dumps(_grupo(processo), ensure_ascii=False, indent=2), encoding="utf-8")
        processo_path = destino / "processo" / f"{processo['id']}.json"
        processo_path.write_text(json.dumps(_processo(processo), ensure_ascii=False, indent=2), encoding="utf-8")
    print("Geração de dados sintéticos finalizada!")


if __name__ == "__main__":
    gerar(Path(sys.argv[1]))
