"""Ambiente de teste: mock sem latência, sem falhas e lendo as fixtures."""

from pathlib import Path

import pytest

FIXTURES: Path = Path(__file__).parent / "tests" / "fixtures" / "data"


@pytest.fixture(autouse=True)
def _ambiente_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zera latência e falhas do mock e aponta os dados para as fixtures."""
    monkeypatch.setenv("MOCK_LATENCY_MS", "0")
    monkeypatch.setenv("MOCK_FAIL_RATE", "0")
    monkeypatch.setenv("MOCK_DATA_DIR", str(FIXTURES))
