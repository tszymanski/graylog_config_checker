# Graylog Config Checker

This repository contains tools to interact with Graylog API for configuration checking and user permission management.

## Scripts

### 1. graylog_config_checker.py
This script reads information about streams, pipelines, and indexes from Graylog servers and creates separate CSV files and diff files with stream names.

### 2. graylog_permission_checker.py
This script reads user permissions from Graylog servers and displays or saves them in various formats (JSON, CSV, or text).

## Configuration

Both scripts require a YAML configuration file containing:
* Graylog host URL
* Graylog user token with appropriate permissions

### Configuration File Structure

```yaml
- graylog_name:
    host: <url to graylog api server>
    token: <user token>
```

#### Example Configuration

```yaml
- graylog-dev:
    host: "https://graylog-dev.example.com"
    token: "your-api-token-here"
- graylog-prod:
    host: "https://graylog-prod.example.com"
    token: "your-api-token-here"
```

## Requirements

The project uses the following Python dependencies (see `requirements.txt`):
- requests
- flatten_json
- pandas
- pyyaml

## Docker

### Building the Docker Image

```bash
docker build -t graylog_config_checker .
```

### Running with Docker

The Docker container sets `graylog_config_checker.py` as the default entrypoint. Mount your configuration file and an output directory for results:

#### Config Checker (default entrypoint)
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    graylog_config_checker --config config.yaml --save --file-prefix output/streams
```

For diff file:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    graylog_config_checker --config config.yaml --diff --file-prefix output/streams
```

#### Permission Checker
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    --entrypoint /code/graylog_permission_checker.py \
    graylog_config_checker --config config.yaml --username <username> --save --output output/permissions.txt
```

## Usage

### graylog_config_checker.py

#### Options

```bash
  -h, --help            Show help message and exit
  --debug               Enable debug mode
  --config CONFIG       Configuration file (required)
  --save                Save output to CSV format
  --diff                Create stream diff file
  --file-prefix FILE_PREFIX
                        Prefix for save file (default: streams)
  --data-transpose      Save CSV data as transposed table
```

#### Examples

Save stream configurations for all Graylog instances:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    graylog_config_checker --config config.yaml --save --file-prefix output/streams
```

Create a diff file comparing streams across all Graylog instances:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    graylog_config_checker --config config.yaml --diff --file-prefix output/streams
```

Save with custom prefix and transpose data:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    graylog_config_checker --config config.yaml --save --file-prefix output/report --data-transpose
```

Enable debug mode:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    graylog_config_checker --config config.yaml --save --file-prefix output/streams --debug
```

### graylog_permission_checker.py

#### Options

```bash
  -h, --help            Show help message and exit
  --debug               Enable debug mode
  --config CONFIG       Configuration file (required)
  --username USERNAME   Username to check permissions for (required)
  --save                Save output to file
  --output OUTPUT       Output filename (default: permissions-<username>-<graylog>.<format>)
  --format FORMAT       Output format: json, csv, or text (default: text)
```

#### Examples

Display user permissions in text format:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    --entrypoint /code/graylog_permission_checker.py \
    graylog_config_checker --config config.yaml --username admin
```

Save permissions in JSON format:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    --entrypoint /code/graylog_permission_checker.py \
    graylog_config_checker --config config.yaml --username admin --save --format json --output output/permissions.json
```

Save permissions to a specific file:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    -v $(pwd)/output:/code/output \
    --entrypoint /code/graylog_permission_checker.py \
    graylog_config_checker --config config.yaml --username admin --save --output output/user-perms.txt
```

Enable debug mode:
```bash
docker run -it --rm \
    -v $(pwd)/config.yaml:/code/config.yaml:ro \
    --entrypoint /code/graylog_permission_checker.py \
    graylog_config_checker --config config.yaml --username admin --debug
```

## Output Files

When using Docker with the mounted output directory (`-v $(pwd)/output:/code/output`), all output files will be saved to the `output/` directory on your host machine.

### graylog_config_checker.py
- `output/streams-<graylog-name>.csv` - Stream configurations for each Graylog instance
- `output/streams-graylog-diff.csv` - Comparison of streams across all Graylog instances

### graylog_permission_checker.py
- `output/permissions-<username>-<graylog>.txt` - User permissions in text format (default)
- `output/permissions-<username>-<graylog>.json` - User permissions in JSON format
- `output/permissions-<username>-<graylog>.csv` - User permissions in CSV format

## Local Test Environment

The `tests/` directory contains a self-contained Graylog stack (MongoDB, DataNode, Graylog) run via Docker Compose, along with a Makefile that automates setup and seeding. It's meant for trying out these scripts against a real Graylog API without touching a shared/production instance.

### First-time setup

```bash
cd tests
make setup        # generates .env with a password secret
make start         # starts mongodb, datanode, graylog containers
```

Open http://localhost:9000 in a browser, log in as `admin` / `admin` (or the password set in `tests/.env`), and complete the preflight wizard (accept the auto-created CA, set the renewal policy to Automatic, wait for DataNode provisioning, click Finish).

```bash
make create-token  # waits for the API, creates an API token, writes tests/config.yaml
make seed          # creates random streams and users for testing
make run           # runs graylog_config_checker.py against the local instance
```

### Subsequent runs

Container volumes persist, so the preflight wizard only needs to be done once:

```bash
cd tests
make start
make stop
```

### Commands

```
make venv          Create Python virtual environment (tests/.venv)
make setup         Generate secrets and create .env
make sysctl        Set vm.max_map_count=262144 (requires sudo, needed by DataNode)
make start         Start all containers
make stop          Stop all containers
make restart       Restart all containers
make clean         Stop containers and remove volumes (resets all state)
make wait          Wait until the Graylog API is ready (post-preflight)
make create-token  Create API token and write tests/config.yaml
make delete-token  Delete the test API token
make show-config   Print generated tests/config.yaml
make seed          Create random streams and users on the local instance
make run           Run graylog_config_checker.py against the local instance
```

`make seed` (`tests/seed_data.py`) populates the instance with randomly named streams and users assigned a mix of built-in roles (`Reader`, `Views Manager`, `Alerts Manager`, `Dashboard Creator`, `Admin`), so both scripts have realistic, varied data to read.

`tests/.env` and `tests/config.yaml` contain generated secrets/tokens and are gitignored — never commit them.

## Author

**Tomasz Szymanski**
- Email: tomasz.szymanski@greenit.com.pl
- Copyright: 2026, Tomasz Szymanski
- License: Apache 2.0
- Version: 1.0.0
