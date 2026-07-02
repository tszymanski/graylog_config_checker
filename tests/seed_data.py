#!/usr/bin/env python
"""
Seed a local Graylog test instance with random streams and users so that
graylog_config_checker.py and graylog_permission_checker.py have something
non-trivial to read.

Usage:
    .venv/bin/python seed_data.py --config config.yaml [--streams 8] [--users 6]
"""

import argparse
import random
import string
import sys

import requests
import yaml

ADJECTIVES = [
    "silent", "amber", "quiet", "rusty", "brisk", "hollow", "cobalt",
    "nimble", "stale", "vivid", "murky", "dusty", "solar", "arctic",
]
NOUNS = [
    "falcon", "otter", "beacon", "harbor", "canyon", "meadow", "quartz",
    "signal", "engine", "cinder", "vortex", "ledger", "prairie", "anchor",
]

# Roles shipped by default with Graylog, used to build users with a mix of
# access levels (read-only, feature-manager, admin).
ROLE_POOL = [
    ["Reader"],
    ["Reader", "Views Manager"],
    ["Reader", "Dashboard Creator"],
    ["Reader", "Alerts Manager"],
    ["Reader", "Pipelines Manager"],
    ["Admin"],
]


def read_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def graylog_post(host, token, path, payload):
    h = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Requested-By": "seed-data",
    }
    response = requests.post(host + path, auth=(token, "token"), headers=h, json=payload)
    response.raise_for_status()
    return response


def graylog_get(host, token, path):
    h = {"Accept": "application/json"}
    response = requests.get(host + path, auth=(token, "token"), headers=h)
    response.raise_for_status()
    return response.json()


def random_name():
    return f"{random.choice(ADJECTIVES)}-{random.choice(NOUNS)}-{random.randint(100, 999)}"


def random_password():
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=16)) + "1!"


def create_streams(host, token, count, debug):
    index_sets = graylog_get(host, token, "/api/system/indices/index_sets")["index_sets"]
    default_index_id = next(i["id"] for i in index_sets if i["default"])

    created = []
    for _ in range(count):
        name = random_name()
        payload = {
            "entity": {
                "title": name,
                "description": f"Randomly seeded stream {name}",
                "index_set_id": default_index_id,
                "rules": [],
                "matching_type": "AND",
                "remove_matches_from_default_stream": False,
            }
        }
        resp = graylog_post(host, token, "/api/streams", payload).json()
        created.append((name, resp["stream_id"]))
        if debug:
            print(f"Created stream: {name} ({resp['stream_id']})")
    return created


def create_users(host, token, count, debug):
    created = []
    for _ in range(count):
        name = random_name().replace("-", "_")
        roles = random.choice(ROLE_POOL)
        payload = {
            "username": name,
            "first_name": name.split("_")[0].capitalize(),
            "last_name": name.split("_")[1].capitalize(),
            "email": f"{name}@example.test",
            "password": random_password(),
            "roles": roles,
            "permissions": [],
            "timezone": "UTC",
        }
        graylog_post(host, token, "/api/users", payload)
        created.append((name, roles))
        if debug:
            print(f"Created user: {name} roles={roles}")
    return created


def main():
    parser = argparse.ArgumentParser(description="Seed a Graylog test instance with random data")
    parser.add_argument("--config", required=True, help="Config file (same format as graylog_config_checker.py)")
    parser.add_argument("--streams", type=int, default=8, help="Number of random streams to create")
    parser.add_argument("--users", type=int, default=6, help="Number of random users to create")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    graylog_config = read_config(args.config)

    for graylogs in graylog_config:
        for graylog, values in graylogs.items():
            host, token = values["host"], values["token"]
            print(f"Seeding {graylog} ({host})")

            streams = create_streams(host, token, args.streams, args.debug)
            print(f"  {len(streams)} streams created")

            users = create_users(host, token, args.users, args.debug)
            print(f"  {len(users)} users created")


if __name__ == "__main__":
    sys.exit(main())
