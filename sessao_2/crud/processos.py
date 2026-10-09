"""Núcleo do CRUD de processos: as regras, sem saber quem chama (API, CLI ou worker).

Os dados ficam num arquivo JSON (env CRUD_ARQUIVO, padrão sessao_2/crud/processos.json),
para que a API e a CLI enxerguem os mesmos processos.
"""

import json
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path

ARQUIVO_PADRAO: Path = Path(__file__).parent / "processos.json"


@dataclass
class Processo:
    """Um processo cadastrado."""

    id: int
    cnj: str
    uf: str
    comarca: str | None = None


class Repositorio:
    """Create, Read, Update e Delete de processos num arquivo JSON."""

    def __init__(self, arquivo: Path | None = None) -> None:
        """Abre o repositório.

        Args:
            arquivo: Arquivo JSON dos dados. Sem ele, usa CRUD_ARQUIVO ou o padrão.
        """
        self.arquivo = arquivo or Path(os.environ.get("CRUD_ARQUIVO", ARQUIVO_PADRAO))

    def _ler(self) -> dict[int, Processo]:
        """Carrega todos os processos, indexados pelo id."""
        if not self.arquivo.exists():
            return {}
        brutos = json.loads(self.arquivo.read_text(encoding="utf-8"))
        return {bruto["id"]: Processo(**bruto) for bruto in brutos}

    def _salvar(self, processos: dict[int, Processo]) -> None:
        """Grava todos os processos no arquivo."""
        dados = [asdict(processo) for processo in processos.values()]
        self.arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    def criar(self, cnj: str, uf: str, comarca: str | None = None) -> Processo:
        """Create: cadastra um processo novo com o próximo id.

        Args:
            cnj: Número CNJ.
            uf: Sigla do estado.
            comarca: Comarca, se conhecida.

        Returns:
            O processo criado.
        """
        processos = self._ler()
        processo = Processo(max(processos, default=0) + 1, cnj, uf, comarca)
        processos[processo.id] = processo
        self._salvar(processos)
        return processo

    def listar(self, uf: str | None = None) -> list[Processo]:
        """Read: lista os processos, opcionalmente filtrando pela UF.

        Args:
            uf: Sigla do estado para filtrar. None devolve todos.

        Returns:
            Os processos encontrados.
        """
        processos = list(self._ler().values())
        if uf is None:
            return processos
        return [processo for processo in processos if processo.uf == uf]

    def buscar(self, processo_id: int) -> Processo | None:
        """Read: busca um processo pelo id.

        Args:
            processo_id: Id do processo.

        Returns:
            O processo, ou None se não existir.
        """
        return self._ler().get(processo_id)

    def substituir(self, processo_id: int, cnj: str, uf: str, comarca: str | None = None) -> Processo | None:
        """Update completo (PUT): troca todos os campos do processo.

        Args:
            processo_id: Id do processo.
            cnj: Novo CNJ.
            uf: Nova UF.
            comarca: Nova comarca; None apaga a anterior.

        Returns:
            O processo atualizado, ou None se não existir.
        """
        processos = self._ler()
        if processo_id not in processos:
            return None
        processos[processo_id] = Processo(processo_id, cnj, uf, comarca)
        self._salvar(processos)
        return processos[processo_id]

    def atualizar(self, processo_id: int, campos: dict[str, str | None]) -> Processo | None:
        """Update parcial (PATCH): troca só os campos informados.

        Args:
            processo_id: Id do processo.
            campos: Campos a alterar, por exemplo {"comarca": "Curitiba"}.

        Returns:
            O processo atualizado, ou None se não existir.
        """
        processos = self._ler()
        atual = processos.get(processo_id)
        if atual is None:
            return None
        processos[processo_id] = replace(atual, **campos)
        self._salvar(processos)
        return processos[processo_id]

    def remover(self, processo_id: int) -> bool:
        """Delete: remove um processo.

        Args:
            processo_id: Id do processo.

        Returns:
            True se removeu; False se o processo não existia.
        """
        processos = self._ler()
        if processo_id not in processos:
            return False
        del processos[processo_id]
        self._salvar(processos)
        return True
