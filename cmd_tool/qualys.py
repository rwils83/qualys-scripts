#!/usr/bin/env python
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
import yaml
import logging
import json
import pdb
from jinja2 import Environment, FileSystemLoader


class Qualys:
    def __init__(self, username, password, url, module, resource, action, filters, output_type):
        self.username = username
        self.password = password
        self.url = url
        self.headers = {'X-Requested-With': 'Curl Sample'}
        self.session = requests.session()
        self.module = module
        self.resource = resource
        self.action = action
        self.filters = filters
        self.filter_dict = {}
        self.output_type = output_type
        self.output_data = []
        self.config = None
        self.config_parse()

    def config_parse(self):
        stream = open('config.yml', 'r')
        self.config = yaml.safe_load(stream)
        logging.debug("Config: {}".format(self.config))

    def list_modules(self):
        print("Modules")
        count = 1
        for k,name in self.config['modules'].items():
            print(f"{count}. {k} - {name['name']}")
            count += 1
        sys.exit(1)

    def list_resources(self):
        print("Resources")
        if 'resources' in self.config['modules'][self.module]:
            count = 1
            for k,name in self.config['modules'][self.module]['resources'].items():
                print(f"{count}. {k} - {name['name']}")
                count += 1
        else:
            print(f"{self.module} has no resources")
        sys.exit(1)

    def list_actions(self):
        print("Actions")
        if 'actions' in self.config['modules'][self.module]['resources'][self.resource]:
            count = 1
            for k,name in self.config['modules'][self.module]['resources'][self.resource]['actions'].items():
                print(f"{count}. {k}")
                count += 1
        else:
            print(f"{self.module} has no resources")
        sys.exit(1)


    def list_filters(self):
        print("Fitlers")
        if 'parameters' in self.config['modules'][self.module]['resources'][self.resource]['actions'][self.action]:
            count = 1
            for k,name in self.config['modules'][self.module]['resources'][self.resource]['actions'][self.action]['parameters'].items():
                print(f"{count}. {k}")
                count += 1
        else:
            print(f"{self.module} has no parameters")
        sys.exit(1)

    def list_output(self):
        print("Outputs\nPlease use -ot and pass one of the following arguments to it")
        count = 1
        for outname, outinfo in self.config['reporting']['output_type'].items():
            print(f"{count}. {outname} - {outinfo['description']}")
            count += 1
        sys.exit(1)

    def checkdate(self, d):
        logging.debug(f"Current date: {d}")

        # Convert string to date format
        formatted_date = datetime.datetime.strptime(d, '%Y%m%d')
        logging.debug(f"Date time: {formatted_date}")

        # Convert date to qualys supported version
        qualys_date = formatted_date.isoformat(sep='T').split('.')[0] + 'Z'
        logging.debug(f"Updated format: {qualys_date}")
        return qualys_date

    def checkfilter(self, f, value):
        logging.debug(f"Checking filter: {f}")
        filters = parameters = self.config['modules'][self.module]['resources'][self.resource]['actions'][self.action]['parameters']

        if filters[f]['desc'] == "date":
            logging.debug("This is a date filter")

            updatedvalue = self.checkdate(value)
        else:
            updatedvalue = value

        return updatedvalue

    def parse_filters(self):
        filter_data = []
        logging.debug("Parsing filters")
        logging.debug(f"Filters: {self.filters}")

        parameters = self.config['modules'][self.module]['resources'][self.resource]['actions'][self.action]['parameters']
        operators = self.config['operators']

        for fparam in self.filters:

            logging.debug("Working on {}".format(fparam))
            # Get filter name
            if "=" in fparam:
                opertext = "equals"
                opersymb = "="
            elif ">" in fparam:
                opertext = "greater"
                opersymb = ">"
            elif "<" in fparam:
                opertext = "less"
                opersymb = "<"
            else:
                opertext = ""
                opersymb = ""

            # Set variables
            fname = fparam.split(opersymb)[0]

            # Make sure parameter has value
            if len(fparam.split(opersymb)) >= 2:
                logging.debug(f"values {fparam.split(opersymb)[1]}")
                # Check if more than one value passed to parameter
                # Add filters to list of dictionaries
                if len(fparam.split(opersymb)[1].split(',')) >= 2:
                    for param in fparam.split(opersymb)[1].split(','):

                        logging.debug(json.dumps({
                            "field": parameters[fname]['parameter'],
                            "operator": operators[opertext]['name'],
                            "value": self.checkfilter(fname, param)
                        }, indent=1))
                        filter_data.append({
                            "field": parameters[fname]['parameter'],
                            "operator": operators[opertext]['name'],
                            "value": self.checkfilter(fname, param)
                        })
                else:
                    logging.debug(f"One value {fparam.split(opersymb)[1]}")
                    logging.debug(json.dumps({
                        "field": parameters[fname]['parameter'],
                        "operator": operators[opertext]['name'],
                        "value": self.checkfilter(fname, fparam.split(opersymb)[1])
                    }, indent=1))
                    filter_data.append({
                        "field": parameters[fname]['parameter'],
                        "operator": operators[opertext]['name'],
                        "value": self.checkfilter(fname, fparam.split(opersymb)[1])
                    })
        logging.debug("End filter")
        return filter_data


    def connect(self, data=None, json=None, base_url="/", method="GET",content_type="", application_type="", extraheaders=None):
        headers = {'Cache-Control': 'no-cache'}

        if extraheaders:
            headers.update(extraheaders)

        # Update header depending on content_type
        if content_type:
            headers.update({"Content-Type": content_type})

        if application_type:
            headers.update({"Accept": application_type})

        # update header based on method
        if method == "GET":
            pass
        elif method == "POST":
            pass

        api_url = f"https://{self.config['default']['server']}{base_url}"
        try:
            logging.debug(f"Making API call to: {api_url}")
            #logging.debug(f"Headers: {headers}")
            output = requests.request(method=method,url=api_url, json=json, data=data, headers=headers, auth=(self.config['default']['username'], self.config['default']['password']))

            #debugmsg = f"Headers: {output.headers}\nBody: {output.content}"
            #logging.debug(debugmsg)

            return output
        except Exception as e:
            logging.debug("Error: {}".format(e))

    def portal(self):
        response = self.connect(base_url=self.config['modules'][self.module]['base_url'],
                     content_type=self.config['modules'][self.module]['content_type'],application_type=self.config['modules'][self.module]['application_type'])
        logging.debug("Response: {}".format(response))
        msg = f"Status: {response.status_code}\nHeaders: {response.headers}\nText: {response.text}"
        logging.debug(msg)


    def am(self):
        hasmore = "false"
        lastid = 0
        output = []
        filters = []

        if self.filters:
            filters = self.parse_filters()

        if "json" in self.config['modules'][self.module]['content_type']:
            tname = f"{os.path.dirname(os.path.abspath(__file__))}/templates/{self.action}.json"
            with open(tname, 'r') as jsonfile:
                data = json.load(jsonfile)

            #logging.debug(f'Data is: {data}')
            for fdict in filters:
                data['ServiceRequest']['filters']['Criteria'].append(fdict)

            # Build API URL
            url = f"{self.config['modules'][self.module]['base_url']}{self.action}/{self.module}{self.config['modules'][self.module]['resources'][self.resource]['url']}"
            method = f"{self.config['modules'][self.module]['resources'][self.resource]['actions'][self.action]['method']}"
            #logging.debug(f"URL {url}\nMethod: {method}\nData: {json.dumps(data, indent=1)}")

            # Handle pagination
            while True:
                # Make API call
                response = self.connect(json=data,
                                        base_url=url,
                                        method=method,
                                        content_type=self.config['modules'][self.module]['content_type'],
                                        application_type=self.config['modules'][self.module]['application_type'])

                output.append(response.json())
                # Print results
                # dict(response.json())['ServiceResponse'].keys()
                # Keys: dict_keys(['hasMoreRecords', 'responseCode', 'lastId', 'data', 'count'])
                #print(f"Response: {json.dumps(response.json(), indent=1)}\nKeys: {dict(response.json())['ServiceResponse'].keys()}")
                if 'lastId' in dict(response.json())['ServiceResponse']:
                    lastid = dict(response.json())['ServiceResponse']['lastId']

                    data["ServiceRequest"]["filters"]['Criteria'][0]['value'] = lastid


                if "hasMoreRecords" in dict(response.json())['ServiceResponse'] and dict(response.json())['ServiceResponse']['hasMoreRecords'] == "true":
                    #logging.debug(f"Has more records: {dict(response.json())['ServiceResponse']['hasMoreRecords']}\nLastid: {lastid}")
                    #logging.debug(f"Type: {type(response.json())}")
                    logging.debug("Has more records")
                else:
                    logging.debug("No more records")
                    break


        elif "xml" in self.config['modules'][self.module]['content_type']:
            pass
            # rtemplate = Environment(
            #     loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)) + "/templates")).get_template(
            #     "{}.xml".format(self.action))
            # xml = rtemplate.render(call=self.action, tag="Cloud Agent", filters=self.filters)
            # print("XML: {}".format(xml))
        else:
            logging.debug("Something went wrong")

        self.output_data = output

    def check_csv_field(self, d):
        logging.debug(f"Type: {type(d)}\nData: {d}")
        if isinstance(d, dict):
            if len(d) == 1:
                if 'list' in d:
                    return len(d['list'])
                else:
                    return "Review data"
            else:
                return "Review data"
        else:
            return d

    def report_csv(self):
        logging.debug("Generating CSV")
        configdata = self.config['reporting'][self.module]['resources'][self.resource]['data']
        header = list(configdata['hostdata'].keys())
        missing_headers = []
        logging.debug(f"Header: {header}")
        with open('test.csv', 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()

            for d in self.output_data:
                # Get data from response

                for data in d['ServiceResponse']['data']:
                    row = {}
                    for hd in data[configdata['name']]:
                        if hd not in header:
                            header.append(hd)
                            missing_headers.append(hd)
                        logging.debug(data[configdata['name']][hd])
                        row.update({hd: self.check_csv_field(data[configdata['name']][hd])})
                    logging.debug(f"Rows: {row}")
                    writer.writerow(row)
        logging.warning(f"The following headers were missing: {missing_headers}")


    def score_card(self):
        score_by_tags = {}
        score_by_teams = {}
        qualys_kb = {}
        logging.debug("Generating Score card")
        configdata = self.config['reporting'][self.module]['resources'][self.resource]['data']
        logging.debug(f"Output_data: {self.output_data}")
        for d in self.output_data:
            for data in d['ServiceResponse']['data']:
                logging.debug(f"Tags: {data[configdata['name']]['tags']}")
                logging.debug(f"Name: {data[configdata['name']]['name']}")
                logging.debug(f"OS: {data[configdata['name']]['os']}")
                logging.debug(f"DNS Host Name: {data[configdata['name']]['dnsHostName']}")
                hid = data[configdata['name']]['id']
                logging.debug(f"ID: {hid}\ntype: {type(hid)}")
                logging.debug(f"Keys: {data.keys()}")
                baseurl = f"/api/2.0/fo/asset/patch/index.php?host_id={hid}"

                #response = self.connect(method="GET", base_url=baseurl,application_type="text/xml", content_type="text/xml", extraheaders={"X-Requested-With": "Curl"})
                #logging.debug(response.content)
                #input("Press enter to pass")
                for hd in data[configdata['name']]:
                    logging.debug(f"HD: {hd}")
                    if hd == "vuln":
                        if "list" in data[configdata['name']][hd]:
                            pass
                            input("Press enter to continue")
                            for vulns in data[configdata['name']][hd]['list']:
                                print(vulns)
                                print(f"QID is {vulns['HostAssetVuln']['qid']}")
                                baseurl = f"/api/2.0/fo/knowledge_base/vuln/?action=list&details=Basic&ids={vulns['HostAssetVuln']['qid']}"
                                logging.debug(f"Base URL: {baseurl}")
                                pdb.set_trace()
                                response = self.connect(method="POST",base_url=baseurl,application_type="application/xml", content_type="application/xml", extraheaders={"X-Requested-With": "Curl"})
                                if isinstance(response.content, bytes):
                                    xmldata = response.content.decode('utf-8')
                                    logging.debug(f"URL Response (Bytes): {xmldata}")
                                else:
                                    xmldata = response.content
                                    logging.debug(f"URL Response (String): {xmldata}")
                                root = ET.fromstring(xmldata)
                                for child in root:
                                    logging.debug(f"Root Tag: {child.tag}\n Root Attrib: {child.attrib}")

                                logging.debug(f"Root: {root}")

                                # Locate Severity
                                for severity_level in root.iter('SEVERITY_LEVEL'):
                                    logging.debug(f"Severity: {severity_level.text}")

                                # Locate Type
                                for severity_level in root.iter('VULN_TYPE'):
                                    logging.debug(f"Vuln Type: {severity_level.text}")

                                # Locate Title
                                for severity_level in root.iter('TITLE'):
                                    logging.debug(f"Title: {severity_level.text}")

                                # locate Diagnosis
                                for severity_level in root.iter('DIAGNOSIS'):
                                    logging.debug(f"Diagnosis: {severity_level.text}")

                        # input("Press enter to pass")



    def report(self):
        logging.debug(f"Reporting on {self.output_type}")
        if self.output_type == "csv":
            self.report_csv()
        if self.output_type == "scorecard":
            self.score_card()


    def run(self):
        logging.debug("Running")

        # check for help
        if self.resource == "help" and self.module != "help":
            self.list_resources()
        elif self.action == "help" and self.resource != "help" and self.module != "help":
            self.list_actions()
        elif not self.filters and self.action != "help" and self.resource != "help" and self.module != "help":
            self.list_filters()
        elif self.module == "help":
            self.list_modules()

        if not self.output_type:
            self.list_output()

        # Run modules
        if self.module == "portal":
            self.portal()
        elif self.module == "am":
            self.am()


        # Display output
        self.report()


