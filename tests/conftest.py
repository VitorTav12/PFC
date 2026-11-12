"""Configuração comum a toda a suíte.

Os testes são separados por pasta e o marcador correspondente é aplicado
automaticamente:

    tests/unit/         -> @pytest.mark.unit
    tests/integration/  -> @pytest.mark.integration

Assim a pipeline roda cada grupo isoladamente:

    pytest -m unit
    pytest -m integration
"""
import os
import sys

import pytest

# Valores apenas para teste (não são segredos reais). setdefault preserva
# qualquer variável já definida no ambiente.
os.environ.setdefault("SECRET_KEY", "chave-apenas-para-testes")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("FLASK_DEBUG", "0")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

GRUPOS = ("unit", "integration")


def pytest_collection_modifyitems(items):
    for item in items:
        grupo = item.path.parent.name
        if grupo not in GRUPOS:
            raise pytest.UsageError(
                f"{item.nodeid}: todo teste deve ficar em tests/unit/ ou tests/integration/"
            )
        item.add_marker(getattr(pytest.mark, grupo))
