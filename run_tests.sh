#!/bin/bash
# Script para ejecutar los tests con nosetests y verificar cobertura >= 95%
# Usa Python 3.12 en virtualenv y SQLite en memoria si no hay PostgreSQL disponible

set -e

PROJECT_DIR="/Users/william/terraform/devops-capstone-project/devops-capstone-project"
cd "$PROJECT_DIR"

# Activar entorno virtual con Python 3.12
if [ -d venv312 ]; then
    source venv312/bin/activate
else
    echo "Error: venv312 no encontrado. Ejecute primero: python3.12 -m venv venv312"
    exit 1
fi

echo "Python version: $(python --version)"

# Instalar dependencias si es necesario
pip install -q -r requirements.txt 2>/dev/null || true

# Configurar base de datos para tests (SQLite si no hay PostgreSQL)
if command -v pg_isready &>/dev/null && pg_isready -q 2>/dev/null; then
    export DATABASE_URI="${DATABASE_URI:-postgresql://postgres:postgres@localhost:5432/postgres}"
    echo "Usando PostgreSQL para tests"
else
    export DATABASE_URI="sqlite:///test.db"
    echo "Usando SQLite para tests (PostgreSQL no disponible)"
fi

export FLASK_APP=service:app
export FLASK_ENV=testing
export FORCE_HTTPS=false

# Limpiar base de datos y cobertura de tests anteriores
rm -f test.db .coverage coverage.xml

# Ejecutar nosetests/nose2 con cobertura
echo "=== Ejecutando tests con cobertura ==="
coverage run --source=service -m nose2 -v tests/

echo ""
echo "=== Reporte de cobertura ==="
coverage report -m --fail-under=95

echo ""
echo "=== Tests y cobertura completados (>= 95%) ==="
