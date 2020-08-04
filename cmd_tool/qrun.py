#!/usr/bin/env python
from version import __version__
from qualys import Qualys
import xml.etree.ElementTree as ET
import argparse
import requests
import configparser
import getpass
import sys
import time
import csv
import datetime
import os
import logging
from jinja2 import Environment, FileSystemLoader


def main():
    parser = argparse.ArgumentParser(description="Qualys Query Tool")

    configuration = parser.add_argument_group('Configuration')
    required_group = parser.add_argument_group('Required')
    optional_group = parser.add_argument_group('Optional')

    configuration.add_argument("-u", "--username", action="store",
                        help="Username for Qualys")
    configuration.add_argument("-p", "--password", action="store_true",
                        help="This will cause the script to prompt you for your qualys password")
    configuration.add_argument("-url", "--url", action="store",
                        help="Qualys API server domain")

    required_group.add_argument("-m", "--module", nargs='?', const="help", default="help", action="store", help="Supply the Qualys module you want to query)")

    required_group.add_argument("-r", "--resource", nargs='?', const="help", default="help", action="store", help="Resource that will be queried")

    required_group.add_argument("-a", "--action", nargs='?', const="help", default="help", action="store", help="Action that will be executed")

    required_group.add_argument("-ot", "--output_type", action="store", help="Will output the information in a certain format")
    optional_group.add_argument("-o", "--output_filter", action="store", default="tagname",
                                help="Will filter output by tagname")

    optional_group.add_argument("-f", "--filters", action="store", nargs="*", default=['name=OPSAD00'],
                         help="Pass all filter arguments in using the Qualys format")

    optional_group.add_argument('-d', '--debug', action='store_const', dest="loglevel", const=logging.DEBUG,
                                default=logging.INFO, help='Print lots of debugging statements')
    optional_group.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))

    args = parser.parse_args()
    # Set Logging
    logging.basicConfig(level=args.loglevel)
    logging.debug("Args are: {}".format(args))

    # Check filters against supported list

    # Run queries, scans or reports
    if len(sys.argv) < 2:
        parser.print_help()
    else:
        q = Qualys(
            username=args.username,
            password=args.password,
            url=args.url,
            module=args.module,
            resource=args.resource,
            action=args.action,
            filters=args.filters,
            output_type=args.output_type
        )
        q.run()


if __name__ == "__main__":
    main()

