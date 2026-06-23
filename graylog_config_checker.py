#!/usr/bin/env python
"""
This script read information about streams, pipelines and indexes from graylog server
and create separate csv file and one diff file with streams names

To run this script, you need to have the configuration file with:
* graylog host
* graylog user token with rights to read all streams, pipelines and indexes

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

__author__ = "Tomasz Szymanski"
__copyright__ = "Copyright 2026, Tomasz Szymanski"
__credits__ = ["Tomasz Szymanski"]
__license__ = "Apache 2.0"
__version__ = "1.0.0"
__maintainer__ = "Tomasz Szymanski"
__email__ = "tomasz.szymanski@greenit.com.pl"
__status__ = "Production"


# variables

path_stream = "/api/streams"                                # stream
path_pipeline = "/api/system/pipelines/connections"         # relation stream_id vs pipeline
path_indexes = "/api/system/indices/index_sets"             # getting title and prefix
path_pipeline_config = "/api/system/pipelines/pipeline"     # pipeline settings
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


def search(index, value, key, dict):
    return next((item[key] for item in dict if item[index] == value), None)


def graylog_data(host, token):
    # collect all needed data
    streams = graylog_get(host + path_stream, token).json()
    pipeline = graylog_get(host + path_pipeline, token).json()
    indexes = graylog_get(host + path_indexes, token).json()
    pipeline_config = graylog_get(host + path_pipeline_config, token).json()
    config = {}

    for elements in streams["streams"]:
        temp_pipeline_ids = search("stream_id", elements["id"], "pipeline_ids", pipeline)
        temp_pipeline_name = []
        if type(temp_pipeline_ids) is list:
            for pipeline_id in temp_pipeline_ids:
                temp_pipeline_name.append(search("id", pipeline_id, "title", pipeline_config))
        elif temp_pipeline_ids is None:
            temp_pipeline_name.append("missing")
        else:
            temp_pipeline_name.append(temp_pipeline_ids)

        config[elements["title"]] = {
            "id": elements["id"],
            "title": elements["title"],
            "description": elements["description"],
            "index_id": elements["index_set_id"],
            "index": search("id", elements["index_set_id"], "title", indexes["index_sets"]),
            "rules": elements["rules"],
            "pipeline_id": temp_pipeline_ids,
            "pipeline_name": temp_pipeline_name,
        }

    return config


def graylog_stream_diff(graylog_stream_config, debug):

    #  stream \ clsuter:   dev, prod
    #  stream 1        :     x, x
    #  stream 2        :      , x

    diff_config = {}
    table_lenght = 0
    # iterate over all graylog cluster from config
    for graylog in graylog_stream_config:
        # iterate over all streams in one graylog cluster
        # current length of list for streams
        table_lenght += 1
        for streams in graylog_stream_config[graylog]:

            # if stream not exist in output table we need to create it
            if streams not in diff_config:
                if table_lenght == 1:
                    diff_config[streams] = [graylog]
                else:
                    temp_table_lenght = 1
                    while temp_table_lenght < table_lenght:
                        if streams not in diff_config:
                            diff_config[streams] = [None]
                        else:
                            diff_config[streams].append(None)
                        temp_table_lenght += 1

                    if temp_table_lenght == table_lenght:
                        diff_config[streams].append(graylog)
            else:
                diff_config[streams].append(graylog)

        # checking if some stream was empty for current graylog cluster
        for streams in diff_config.keys():
            if len(diff_config[streams]) < table_lenght:
                diff_config[streams].append(None)

    if debug:
        print(diff_config)

    # check max length in each list
    max_cluster = len(graylog_stream_config.keys())
    streams_length = True
    while streams_length:
        for streams in diff_config:
            if len(diff_config[streams]) < max_cluster:
                diff_config[streams].append(None)
                streams_length = True
            else:
                streams_length = False

    diff_output = pd.DataFrame(dict(sorted(diff_config.items())))
    # save output
    if debug:
        print(diff_output.to_csv(index=True))

    return diff_output


def save_file(data, filename, prefix):

    if prefix == "":
        final_filename = filename
    else:
        final_filename = prefix + "-" + filename

    with open(final_filename, "w") as outfile:
        print(data, file=outfile)


def main(args):
    parser = argparse.ArgumentParser(description="Graylog config checker")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--config", action="store", help="Configuration file", required=True)
    parser.add_argument("--save", action="store_true", help="save output to csv format")
    parser.add_argument("--diff", action="store_true", help="Create stream diff file")
    parser.add_argument("--file-prefix", action="store",
                        help="Prefix for save file, default will be streams-<name of graylog from config file>.csv",
                        default="streams")
    parser.add_argument("--data-transpose", action="store_true",
                        help="Save csv data as transpose table")
    args = parser.parse_args()

    if args.config:
        graylog_config = read_config(args.config, args.debug)

    if not args.save and not args.diff:
        print("You need to choose what you want to save graylog stream config or diff ?")
        sys.exit(0)
    else:
        graylog_stream_config = {}
        for graylogs in graylog_config:
            for graylog, values in graylogs.items():
                if args.debug:
                    print("graylog ", graylog, "host: ", values["host"], "token: ", values["token"])

                graylog_stream_config[graylog] = graylog_data(values["host"], values["token"])

        if args.save:
            for graylog in graylog_stream_config:
                if args.debug:
                    print("Saving stream for ", graylog)

                output = pd.DataFrame(dict(sorted(graylog_stream_config[graylog].items())))
                if args.debug:
                    print(output.to_csv(index=True))

                if args.data_transpose:
                    final_output = output.transpose()
                else:
                    final_output = output

                save_file(final_output.to_csv(index=True), graylog + ".csv", args.file_prefix)

        elif args.diff:
            diff_output = graylog_stream_diff(graylog_stream_config, args.debug)

            # save data to file
            if args.data_transpose:
                final_diff_output = diff_output.transpose()
            else:
                final_diff_output = diff_output

            save_file(final_diff_output.to_csv(index=True), "graylog-diff.csv", args.file_prefix)


if __name__ == "__main__":
    main(sys.argv)