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


class StoreFilter(argparse.Action):
    """
    Use Store filter to create a dictionary of all filter items for parsoing
    """
    def __call__(self, parser, namespace, values, option_string=None):
        my_dict = {}
        print(values)
        for kv in values:
            k, v = kv.split("=")
            if len(v.split(",")) > 1:
                my_dict[k] = v.split(",")
            else:
                if k == "tags.name":
                    my_dict[k] = [v]
                else:
                    my_dict[k] = v
        setattr(namespace, self.dest, my_dict)


class PwdAction(argparse.Action):
    """
    Use getpassword to hide password on the command line and return to the password argument
    """
    def __call__(self, parser, namespace, values, option_string=None):
        mypass = getpass.getpass()
        setattr(namespace, self.dest, mypass)


def main():
    parser = argparse.ArgumentParser(description="Qualys Query Tool")

    configuration = parser.add_argument_group('Configuration')
    optional_group = parser.add_argument_group('Optional')

    configuration.add_argument("-t", "--test_authentication", action="store_true",
                        help="Test authentication buy get a count of all hosts")
    configuration.add_argument("-u", "--username", action="store",
                        help="Username for Qualys")
    configuration.add_argument("-p", "--password", action=PwdAction, nargs=0,
                        help="This will cause the script to prompt you for your qualys password")
    configuration.add_argument("-url", "--url", action="store",
                        help="Qualys API server domain")

    supported_modules = ["ca", "av", "vm", "was"]
    parser.add_argument("-m", "--module", action="store", help="Supply the Qualys module you want to query (Supported Modules: {})".format(", ".join(supported_modules)))

    supported_calls = ['count', 'search', 'activate', 'deactivate']
    parser.add_argument("-c", "--call", action="store", help="Make API call and execute action (Supported Calls: {}".format(", ".join(supported_calls)))

    supported_filters = ['tags.name', "ec2.instanceState", "updated", "created"]
    parser.add_argument("-f", "--filters", action=StoreFilter, nargs="*",
                         help="Pass all filter arguments in using the Qualys format (Supported Tags: {} ".format(", ".join(supported_filters)))

    optional_group.add_argument('-d', '--debug', action='store_const', dest="loglevel", const=logging.DEBUG,
                                default=logging.INFO, help='Print lots of debugging statements')
    optional_group.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))

    args = parser.parse_args()
    # Set Logging
    logging.basicConfig(level=args.loglevel)
    logging.debug("Args are: {}".format(args))

    # Check filters against supported list
    if args.filters:
        for filter in args.filters:
            if filter in supported_filters:
                pass
            else:
                print("{} not a supported filter".format(filter))
                sys.exit(1)

    # Run queries, scans or reports
    q = Qualys(args.username, args.password, args.url, module=args.module, call=args.call, filters=args.filters)
    if args.test_authentication:
        q.testcreds()
    elif args.module:
        q.run()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

