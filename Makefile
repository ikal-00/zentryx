PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
API_URL ?= http://100.72.215.34:5000

.PHONY: help setup compile test-app test-backend verify app server-up server-stop server-status server-logs smoke

help:
	@echo "Zentryx"
	@echo "  make setup          Crear .venv e instalar dependencias"
	@echo "  make verify         Compilar y ejecutar tests"
	@echo "  make app            Abrir Flet contra la API compartida"
	@echo "  make server-up      Levantar API, DB y simulador"
	@echo "  make server-stop    Detener servicios sin borrar datos"
	@echo "  make server-status  Mostrar estado de Docker"
	@echo "  make server-logs    Seguir logs"
	@echo "  make smoke          Smoke test contra API_URL"

setup:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

compile:
	$(VENV_PYTHON) -m compileall -q app backend

test-app:
	cd app && ../$(VENV_PYTHON) -m unittest discover -s tests -v

test-backend:
	$(VENV_PYTHON) -m unittest discover -s backend/tests -v

verify: compile test-app test-backend

app:
	bash app/run_shared_api.sh

server-up:
	docker compose --profile demo up -d --build

server-stop:
	docker compose --profile demo stop

server-status:
	docker compose --profile demo ps

server-logs:
	docker compose --profile demo logs -f --tail=150

smoke:
	$(VENV_PYTHON) scripts/check_shared_api.py $(API_URL)
