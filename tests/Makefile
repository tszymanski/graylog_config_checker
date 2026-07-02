GRAYLOG_URL    := http://localhost:9000
COMPOSE        := docker compose -f docker-compose.yml
ENV_FILE       := .env
TOKEN_NAME     := test-token
VENV           := $(abspath ../.venv)
PYTHON         := $(VENV)/bin/python

# Load .env if it exists (for GRAYLOG_ROOT_PASSWORD)
-include $(ENV_FILE)
GRAYLOG_ROOT_PASSWORD ?= admin

.PHONY: help setup sysctl venv start stop restart clean wait create-token delete-token show-config run seed

help:
	@echo "Graylog test environment"
	@echo ""
	@echo "First-time setup:"
	@echo "  1. make setup        Generate secrets and create .env"
	@echo "  2. make start        Start all containers"
	@echo "  3. Open http://localhost:9000 in your browser"
	@echo "     Login: admin / <random password printed in 'docker compose logs graylog'>"
	@echo "     (look for: 'Initial configuration is accessible at ... with username"
	@echo "     'admin' and password ...' -- this is NOT GRAYLOG_ROOT_PASSWORD)"
	@echo "     Follow the preflight wizard:"
	@echo "       a) CA is auto-created (or create it in the UI)"
	@echo "       b) Configure renewal policy -> set Automatic, click Next"
	@echo "       c) Wait for DataNode provisioning to complete"
	@echo "       d) Click Finish"
	@echo "  4. make create-token  Create API token and write config.yaml"
	@echo "  5. make seed          Create random streams and users for testing"
	@echo "  6. make run           Test the checker"
	@echo ""
	@echo "Subsequent runs (volumes persist, no preflight wizard):"
	@echo "  make start / make stop"
	@echo ""
	@echo "Commands:"
	@echo "  make venv          Create Python virtual environment (.venv)"
	@echo "  make setup         Generate secrets and create .env"
	@echo "  make sysctl        Set vm.max_map_count=262144 (requires sudo)"
	@echo "  make start         Start all containers"
	@echo "  make stop          Stop all containers"
	@echo "  make restart       Restart all containers"
	@echo "  make clean         Stop containers and remove volumes (resets all state)"
	@echo "  make wait          Wait until Graylog API is ready (post-preflight)"
	@echo "  make create-token  Create API token and write config.yaml"
	@echo "  make delete-token  Delete the test API token"
	@echo "  make show-config   Print generated config.yaml"
	@echo "  make seed          Create random streams and users on local instance"
	@echo "  make run           Run graylog_config_checker and graylog_permission_checker"
	@echo "                     (against a random user from the last 'make seed')"

setup:
	@if [ -f $(ENV_FILE) ]; then \
		echo "$(ENV_FILE) already exists, skipping. Remove it first to regenerate."; \
	else \
		cp .env.example $(ENV_FILE); \
		SECRET=$$(< /dev/urandom tr -dc A-Z-a-z-0-9 | head -c96); \
		sed -i "s|^GRAYLOG_PASSWORD_SECRET=$$|GRAYLOG_PASSWORD_SECRET=$$SECRET|" $(ENV_FILE); \
		echo "Created $(ENV_FILE) with generated GRAYLOG_PASSWORD_SECRET."; \
		echo "Default admin password: admin  (GRAYLOG_ROOT_PASSWORD in $(ENV_FILE))"; \
	fi

venv:
	@if [ ! -d $(VENV) ]; then \
		python3 -m venv $(VENV); \
		$(VENV)/bin/pip install -q -r ../requirements.txt; \
		echo "Virtual environment created at $(VENV)"; \
	else \
		echo "Virtual environment already exists at $(VENV)"; \
	fi

sysctl:
	@echo "Setting vm.max_map_count=262144 (required by Graylog DataNode)"
	echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
	sudo sysctl -p

start:
	@[ -f $(ENV_FILE) ] || (echo "Run 'make setup' first"; exit 1)
	$(COMPOSE) up -d
	@echo "Graylog UI will be available at $(GRAYLOG_URL) (first boot may take 2-3 minutes)"

stop:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

clean:
	$(COMPOSE) down -v
	@echo "All containers and volumes removed."

wait:
	@echo "Waiting for Graylog API at $(GRAYLOG_URL)/api/system/lbstatus ..."
	@until curl -sf $(GRAYLOG_URL)/api/system/lbstatus | grep -q "ALIVE"; do \
		printf "."; sleep 5; \
	done
	@echo ""
	@echo "Graylog is ready."

create-token: wait
	@echo "Creating API token '$(TOKEN_NAME)' for user 'admin'..."
	@TOKEN=$$(curl -sf \
		-u "admin:$(GRAYLOG_ROOT_PASSWORD)" \
		-H "Accept: application/json" \
		-H "X-Requested-By: cli" \
		-X POST \
		"$(GRAYLOG_URL)/api/users/local%3Aadmin/tokens/$(TOKEN_NAME)" \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['token'])"); \
	if [ -z "$$TOKEN" ]; then echo "ERROR: failed to create token"; exit 1; fi; \
	printf -- "- graylog-local:\n    host: \"$(GRAYLOG_URL)\"\n    token: \"$$TOKEN\"\n" > config.yaml; \
	echo "Token created. config.yaml written."

delete-token:
	@echo "Deleting API token '$(TOKEN_NAME)'..."
	curl -sf \
		-u "admin:$(GRAYLOG_ROOT_PASSWORD)" \
		-H "X-Requested-By: cli" \
		-X DELETE \
		"$(GRAYLOG_URL)/api/users/local%3Aadmin/tokens/$(TOKEN_NAME)" \
		&& echo "Token deleted." || echo "Token not found or already deleted."

show-config:
	@[ -f config.yaml ] || (echo "Run 'make create-token' first"; exit 1)
	@cat config.yaml

seed: venv
	@[ -f config.yaml ] || (echo "Run 'make create-token' first"; exit 1)
	$(PYTHON) seed_data.py --config config.yaml

run: venv
	@[ -f config.yaml ] || (echo "Run 'make create-token' first"; exit 1)
	@[ -f seeded_users.txt ] || (echo "Run 'make seed' first to create test users"; exit 1)
	@echo "--- Testing graylog_config_checker.py ---"
	cd .. && $(PYTHON) graylog_config_checker.py --config tests/config.yaml --save --debug
	@echo ""
	@echo "--- Testing graylog_permission_checker.py ---"
	@USERNAME=$$($(PYTHON) -c "import random; print(random.choice(open('seeded_users.txt').read().split()))"); \
	echo "Random seeded user: $$USERNAME"; \
	cd .. && $(PYTHON) graylog_permission_checker.py --config tests/config.yaml --username $$USERNAME --debug
