"""Captura respostas reais da consulta-api para o mock, com whitelist de campos.

Só grava o necessário para o de-para: ids de processos e a localização.
Partes, documentos e qualquer outro campo são descartados antes de gravar.

Rode na máquina do instrutor, com o proxy no ar:
    legal-port-forward-consulta-api        # outro terminal, expõe localhost:8074
    uv run python -m scripts.capturar
"""

import json
import os
import shutil
import time
from pathlib import Path

import httpx

from cnjs import CNJS
from sessao_1.solucao import escolher_processo_id

DESTINO_PADRAO: Path = Path(__file__).resolve().parents[1] / "mock" / "data"


def _so_ids(valor: dict | list | None) -> dict | list | None:
    """Reduz um processo (ou lista de processos) do grupo ao seu id."""
    if isinstance(valor, dict):
        return {"id": valor["id"]}
    if isinstance(valor, list):
        return [{"id": item["id"]} for item in valor]
    return None


def filtrar_grupo(raw: dict) -> dict:
    """Mantém só os ids de cada categoria do grupo processual.

    Args:
        raw: Resposta real de /v2/grupo_processual/{cnj}.

    Returns:
        Grupo com a mesma estrutura de categorias e só os ids.
    """
    categorias = raw.get("processos_categorizados") or {}
    return {"processos_categorizados": {chave: _so_ids(valor) for chave, valor in categorias.items()}}


def _manter(raw: dict, campo: str, subcampo: str) -> dict | None:
    """Copia `raw[campo][subcampo]`, ou None quando `raw[campo]` não existe."""
    objeto = raw.get(campo)
    if objeto is None:
        return None
    return {subcampo: objeto.get(subcampo)}


def filtrar_processo(raw: dict) -> dict:
    """Mantém só id, estado.sigla e nome_normalizado de tribunal, comarca e foro.

    Args:
        raw: Resposta real de /processo/{id}.

    Returns:
        Processo reduzido à whitelist.
    """
    return {
        "id": raw["id"],
        "estado": _manter(raw, "estado", "sigla"),
        "tribunal": _manter(raw, "tribunal", "nome_normalizado"),
        "comarca": _manter(raw, "comarca", "nome_normalizado"),
        "foro": _manter(raw, "foro", "nome_normalizado"),
    }


def _gravar(caminho: Path, dados: dict) -> None:
    """Escreve um JSON formatado, criando o diretório se preciso."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def capturar(cnjs: list[str], client: httpx.Client, destino: Path) -> None:
    """Busca grupo e processo de cada CNJ e grava as versões filtradas.

    Args:
        cnjs: CNJs a capturar.
        client: Cliente apontado para a consulta-api real.
        destino: Raiz dos dados do mock.
    """
    inicio = time.time()
    print(f"Captura iniciada: {len(cnjs)} CNJs -> {destino}")
    gravados = 0
    pulados_nao_encontrado = 0
    pulados_grupo_sem_processos = 0

    try:
        for cnj in cnjs:
            resposta = client.get(f"/v2/grupo_processual/{cnj}")
            if resposta.status_code == 404:
                pulados_nao_encontrado += 1
                continue
            resposta.raise_for_status()
            grupo = filtrar_grupo(resposta.json())
            _gravar(destino / "grupo_processual" / f"{cnj}.json", grupo)

            processo_id = escolher_processo_id(grupo)
            if processo_id is None:
                pulados_grupo_sem_processos += 1
                continue
            resposta = client.get(f"/processo/{processo_id}")
            resposta.raise_for_status()
            _gravar(destino / "processo" / f"{processo_id}.json", filtrar_processo(resposta.json()))
            gravados += 1
    except Exception as e:
        duracao = time.time() - inicio
        print(f"Captura falhou após {duracao:.1f}s: {gravados} gravados, {pulados_nao_encontrado} nao_encontrado, {pulados_grupo_sem_processos} grupo_sem_processos. Erro: {type(e).__name__}: {e}")
        raise

    duracao = time.time() - inicio
    print(f"Captura finalizada em {duracao:.1f}s: {gravados} gravados, {pulados_nao_encontrado} nao_encontrado, {pulados_grupo_sem_processos} grupo_sem_processos")


def substituir_dados(origem: Path, destino: Path) -> None:
    """Move captured files from origem to destino, replacing existing files.

    Args:
        origem: Temporary directory with captured files.
        destino: Final destination for mock data.
    """
    for arquivo in destino.glob("*/*.json"):
        arquivo.unlink()
    for arquivo in origem.glob("*/*.json"):
        arquivo_destino = destino / arquivo.relative_to(origem)
        arquivo_destino.parent.mkdir(parents=True, exist_ok=True)
        arquivo.rename(arquivo_destino)


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with httpx.Client(base_url=os.environ.get("BASE_URL", "http://localhost:8074"), timeout=30) as client:
            capturar(CNJS, client, temp_path)
        substituir_dados(temp_path, DESTINO_PADRAO)
