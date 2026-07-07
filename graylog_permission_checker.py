#!/usr/bin/env python
"""
This script reads information about user permissions from graylog server
and displays or saves the permissions to a file.

To run this script, you need to have the configuration file with:
* graylog host
* graylog user token with rights to read user permissions

Structure of configuration file (yaml)

graylog_name:
    host: <url to graylog api server>
    token: <user token>
"""


import requests
import pandas as pd
import yaml
import argparse
import sys
import json

__author__ = "Tomasz Szymanski"
__copyright__ = "Copyright 2026, Tomasz Szymanski"
__credits__ = ["Tomasz Szymanski"]
__license__ = "Apache 2.0"
__version__ = "1.0.0"
__maintainer__ = "Tomasz Szymanski"
__email__ = "tomasz.szymanski@greenit.com.pl"
__status__ = "Production"


# variables
path_user_permissions = "/api/users/{username}"
graylog_config = {}


# define get function
def read_config(file, debug):
    with open(file, "r") as yamlfile:
        data = yaml.safe_load(yamlfile)
        if debug:
            print("Read successful")

    if debug:
        print(data)
    return data


def graylog_get(url, token, **kwargs):
    h = {'Accept': 'application/json'}
    access_token = (token, "token")
    try:
        response = requests.get(url, auth=access_token, headers=h, params=kwargs)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    return response


def get_user_permissions(host, token, username, debug):
    """
    Get user permissions from Graylog API

    Args:
        host: Graylog host URL
        token: API token
        username: Username to check permissions for
        debug: Debug flag

    Returns:
        Dictionary with user permissions
    """
    url = host + path_user_permissions.format(username=username)

    if debug:
        print(f"Fetching permissions for user: {username}")
        print(f"URL: {url}")

    response = graylog_get(url, token)
    permissions = response.json()

    if debug:
        print(f"Raw response: {json.dumps(permissions, indent=2)}")

    return permissions


def save_file(data, filename):
    """
    Save data to file

    Args:
        data: Data to save
        filename: Output filename
    """
    with open(filename, "w") as outfile:
        print(data, file=outfile)


def main(args):
    parser = argparse.ArgumentParser(description="Graylog user permission checker")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--config", action="store", help="Configuration file", required=True)
    parser.add_argument("--username", action="store", help="Username to check permissions for", required=True)
    parser.add_argument("--save", action="store_true", help="Save output to file")
    parser.add_argument("--output", action="store",
                        help="Output filename (default: permissions-<username>-<graylog>.txt)",
                        default="")
    parser.add_argument("--format", action="store",
                        help="Output format: json, csv, or text (default: text)",
                        default="text",
                        choices=["json", "csv", "text"])
    args = parser.parse_args()

    if args.config:
        graylog_config = read_config(args.config, args.debug)

    # Process each graylog instance from config
    for graylogs in graylog_config:
        for graylog, values in graylogs.items():
            if args.debug:
                print(f"Checking permissions on graylog: {graylog}")
                print(f"Host: {values['host']}")

            permissions = get_user_permissions(
                values["host"],
                values["token"],
                args.username,
                args.debug
            )

            # Display or save permissions
            if args.format == "json":
                output_data = json.dumps(permissions, indent=2)
            elif args.format == "csv":
                # Convert permissions list to DataFrame
                if isinstance(permissions, dict) and "permissions" in permissions:
                    df = pd.DataFrame(permissions["permissions"], columns=["permission"])
                else:
                    df = pd.DataFrame(permissions, columns=["permission"])
                output_data = df.to_csv(index=False)
            else:  # text format
                if isinstance(permissions, dict) and "permissions" in permissions:
                    output_data = f"User: {args.username}\nGraylog: {graylog}\n\nPermissions:\n"
                    output_data += "\n".join(f"  - {perm}" for perm in permissions["permissions"])
                else:
                    output_data = f"User: {args.username}\nGraylog: {graylog}\n\nPermissions:\n"
                    output_data += "\n".join(f"  - {perm}" for perm in permissions)

            if args.save:
                # Determine output filename
                if args.output:
                    filename = args.output
                else:
                    extension = {"json": "json", "csv": "csv", "text": "txt"}[args.format]
                    filename = f"permissions-{args.username}-{graylog}.{extension}"

                save_file(output_data, filename)
                print(f"Permissions saved to: {filename}")
            else:
                print(output_data)
                print()


if __name__ == "__main__":
    main(sys.argv)
