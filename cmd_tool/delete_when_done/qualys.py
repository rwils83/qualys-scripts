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
from jinja2 import Environment, FileSystemLoader


class Qualys:
    def __init__(self, username, password, url, module, call, filters):
        self.username = username
        self.password = password
        self.url = url
        self.headers = {'X-Requested-With': 'Curl Sample'}
        self.session = requests.session()
        self.module = module
        self.call = call
        self.filters = filters
        self.config = None
        self.config_parse()
        self.check_module()
        self.check_api_call()

    def config_parse(self):
        stream = open('config.yml', 'r')
        self.config = yaml.safe_load(stream)
        logging.debug("Config: {}".format(self.config))
        input("Press enter to pass")

        # Check for user supplied config items
        if self.username:
            pass
        elif self.config['default']['username']:
            self.username = self.config['default']['username']
        else:
            logging.debug("No username was set in the config file or passed via -u/--username")
            sys.exit(1)

        # Check for user supplied password and config password
        if self.password:
            pass
        elif self.config['default']['password']:
            self.password = self.config['default']['password']
        else:
            logging.debug("No password was set in the config file or passed via -u/--password")
            sys.exit(1)

        # Check for user supplied api url and config api url
        if self.url:
            pass
        elif self.config['default']['server']:
            self.url = self.config['default']['server']
        else:
            logging.debug("No password was set in the config file or passed via -u/--password")
            sys.exit(1)

    def check_module(self):
        logging.debug("Supplied Module: {}\nSupported Module list: {}".format(self.module, self.config['modules'].keys()))
        if self.module in self.config['modules']:
            logging.debug("{} is a supported module".format(self.module))
        else:
            logging.error("{} is not a supported module".format(self.module))
            sys.exit(1)

    def check_api_call(self):
        logging.debug("Supplied API call: {}\nSupported API calls: {}".format(self.call, self.config['modules'][self.module]))
        if self.call in self.config['modules'][self.module]:
            pass
        else:
            logging.error("{} not a supported call".format(self.call))
            sys.exit(1)

    def connect(self, xml):
        logging.debug("Connecting to API")
        headers = {'Content-Type': 'text/xml', 'Cache-Control': 'no-cache'}
        api_url = "https://" + self.url + self.config['api'][self.call]
        try:
            logging.debug("Making API call to: {}".format(api_url))
            output = requests.post(api_url, data=xml, headers=headers, auth=(self.username, self.password))

            if "status_code" in output:
                logging.debug("Status_code: {}".format(output.status_code))
            if "content" in output:
                logging.debug("Content: {}".format(output.content))
            if "headers" in output:
                logging.debug("Headers: {}".format(output.headers))
            return output
        except Exception as e:
            logging.debug("Error: {}".format(e))

    def run(self):
        mod = "self.{}_{}()".format(self.module, self.call)
        logging.debug("Running {}".format(mod))
        items = eval(mod)
        if items:
            self.report(data=items, name="{}-{}".format(self.module, self.call))
        else:
            logging.debug("Noting to report. Items was empty")


## Old code that will be refactored or deleted

    def checkdate(self, date):
        formatted_date = None
        operator = None
        if str(date).startswith("-"):
            d = str(date).replace("-", "", 1)
            operator = "LESSER"
            formatted_date = datetime.datetime.fromisoformat(d)
        elif str(date).startswith("+"):
            operator = "GREATER"
            d = str(date).replace("+", "")
            formatted_date = datetime.datetime.fromisoformat(d)
        elif str(date).startswith("is"):
            operator = "EQUALS"
            d = str(date).replace("is", "")
            formatted_date = datetime.datetime.fromisoformat(d)
        elif str(date).startswith("not"):
            operator = "NOT EQUALS"
            d = str(date).replace("not", "")
            formatted_date = datetime.datetime.fromisoformat(d)
        elif datetime.datetime.fromisoformat(date):
            formatted_date = datetime.datetime.fromisoformat(date)
        else:
            logging.debug("Date: {} is not in the correct format\nExample 2018-08-25T00:00:01".format(date))
            sys.exit(1)
        logging.debug("New date: {}\nOperator: {}".format(formatted_date, operator))
        logging.debug(self.filters)
        self.filters['updated'] = formatted_date.isoformat(sep='T').split(".")[0] + "Z"
        self.filters['updated_operator'] = operator
        logging.debug(self.filters)
        return operator, formatted_date

    def ca_count(self):
        logging.debug("Counting")
        countitems = []
        # Check for filters
        if self.filters and "tags.name" in self.filters:
            tags = self.filters["tags.name"]
        else:
            tags = ["all"]

        if "updated" in self.filters:
            logging.debug("Date Filter: {}".format(self.filters["updated"]))
            self.checkdate(self.filters["updated"])
        else:
            pass

        for tag in tags:
            rtemplate = Environment(
                loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)) + "/templates")).get_template(
                "{}.xml".format(self.call))
            xml = rtemplate.render(call=self.call, tag=tag, filters=self.filters)
            logging.debug("XML: {}".format(xml))
        # Remove after testing
        #return countitems

            output = self.connect(xml=xml)
            if output.status_code == 200:
                tree = ET.ElementTree(ET.fromstring(output.content))
                root = tree.getroot()
                for child in root:
                    if child.tag == "count":
                        foundcount = {"count":child.text}
                        foundcount.update({"tag":tag})
                        logging.debug("{} Count is: {}".format(tag, child.text))
                        countitems.append(foundcount)

        logging.debug("Count Items gathered")
        logging.debug("Count: {}".format(countitems))
        return countitems

    def ca_deactivate(self):
        logging.debug("Deactivating cloud agent")
        hostitems = []
        uniquehostlist = []
        # hasmore = "false"

        # Check for filters
        if self.filters and "tags.name" in self.filters:
            tags = self.filters["tags.name"]
        else:
            tags = ["all"]

        if "updated" in self.filters:
            logging.debug("Date Filter: {}".format(self.filters["updated"]))
            self.checkdate(self.filters["updated"])
        else:
            pass

        for tag in tags:
            lastid = 0
            rtemplate = Environment(
                loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)) + "/templates")).get_template(
                "{}.xml".format(self.call))
            xml = rtemplate.render(lastid=lastid, call=self.call, tag=tag, filters=self.filters, module=self.module)
            logging.debug("XML: {}".format(xml))

            output = self.connect(xml=xml)
            if "status_code" in output and output.status_code == 200:
                tree = ET.ElementTree(ET.fromstring(output.content))
                root = tree.getroot()
                for child in root:
                    if child.tag != "data":
                        # Good for debug
                        #logging.debug("Tag {}: {}".format(child.tag, child.text))
                        pass
                    if child.tag == "responseCode":
                        #logging.debug("Tag {}: {}".format(child.tag, child.text))
                        pass
                    if child.tag == "count":
                        #logging.debug("Tag {}: {}\nType: {}".format(child.tag, child.text, type(child.text)))
                        pass
                    if child.tag == "hasMoreRecords":
                        hasmore = child.text
                    if child.tag == "lastId":
                        lastid = child.text
                    if child.tag == "data":
                        for hostasset in child:
                            # Parse each tag and store attributes in dictionary
                            if hostasset.tag == "Asset":
                                foundhost = {}
                                # Located in List Agents from CLoud Agent API page 22
                                for qualystag in hostasset:
                                    if qualystag.tag == "id":
                                        foundhost.update({"id": qualystag.text})
                                    if qualystag.tag == "os":
                                        foundhost.update({"os": qualystag.text})
                                    if qualystag.tag == "address":
                                        foundhost.update({"address": qualystag.text})
                                    if qualystag.tag == "modified":
                                        foundhost.update({"modified": qualystag.text})
                                    if qualystag.tag == "created":
                                        foundhost.update({"created": qualystag.text})
                                    if qualystag.tag == "name":
                                        foundhost.update({"name": qualystag.text})
                                    if qualystag.tag == "type":
                                        foundhost.update({"type": qualystag.text})
                                    if qualystag.tag == "lastSystemBoot":
                                        foundhost.update({"lastSystemBoot": qualystag.text})
                                    if qualystag.tag == "agentInfo":
                                        for agentinfo in qualystag:
                                            if agentinfo.tag == "agentVersion":
                                                foundhost.update({"agentVersion": agentinfo.text})
                                            if agentinfo.tag == "status":
                                                foundhost.update({"status": agentinfo.text})
                                            if agentinfo.tag == "lastCheckedIn":
                                                foundhost.update({"lastCheckedIn": agentinfo.text})
                                            if agentinfo.tag == "connectedFrom":
                                                foundhost.update({"connectedFrom": agentinfo.text})
                                            if agentinfo.tag == "activatedModule":
                                                foundhost.update({"activatedModule": agentinfo.text})
                                            if agentinfo.tag == "platform":
                                                foundhost.update({"platform": agentinfo.text})
                                    if qualystag.tag in uniquehostlist:
                                        pass
                                    else:
                                        uniquehostlist.append(qualystag.tag)
                                hostitems.append(foundhost)
        logging.debug("Deactivated Host Items gathered")
        return hostitems

    def ca_search(self):
        logging.debug("Parsing cloud agent")
        hostitems = []
        uniquehostlist = []
        #hasmore = "false"

        # Check for filters
        if self.filters and "tags.name" in self.filters:
            tags = self.filters["tags.name"]
        else:
            tags = ["all"]

        if "updated" in self.filters:
            logging.debug("Date Filter: {}".format(self.filters["updated"]))
            self.checkdate(self.filters["updated"])
        else:
            logging.debug("NO date filter")
        #input("Wait before you leap")

        for tag in tags:
            lastid = 0
            rtemplate = Environment(
                loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)) + "/templates")).get_template(
                "{}.xml".format(self.call))
            xml = rtemplate.render(lastid=lastid, call=self.call, tag=tag, filters=self.filters)
            logging.debug("XML: {}".format(xml))

            output = self.connect(xml=xml)
            if output.status_code == 200:
                tree = ET.ElementTree(ET.fromstring(output.content))
                root = tree.getroot()
                for child in root:
                    if child.tag != "data":
                        # Good for debug
                        logging.debug("Tag {}: {}".format(child.tag, child.text))
                        pass
                    if child.tag == "responseCode":
                        logging.debug("Tag {}: {}".format(child.tag, child.text))
                    if child.tag == "count":
                        logging.debug("Tag {}: {}\nType: {}".format(child.tag, child.text, type(child.text)))
                    if child.tag == "hasMoreRecords":
                        hasmore = child.text
                    if child.tag == "lastId":
                        lastid = child.text
                    if child.tag == "data":
                        for hostasset in child:
                            # Parse each tag and store attributes in dictionary
                            if hostasset.tag == "HostAsset":
                                foundhost = {}
                                # Located in List Agents from CLoud Agent API page 22
                                for qualystag in hostasset:
                                    if qualystag.tag == "id":
                                        foundhost.update({"id": qualystag.text})
                                    if qualystag.tag == "os":
                                        foundhost.update({"os": qualystag.text})
                                    if qualystag.tag == "address":
                                        foundhost.update({"address": qualystag.text})
                                    if qualystag.tag == "modified":
                                        foundhost.update({"modified": qualystag.text})
                                    if qualystag.tag == "created":
                                        foundhost.update({"created": qualystag.text})
                                    if qualystag.tag == "name":
                                        foundhost.update({"name": qualystag.text})
                                    if qualystag.tag == "type":
                                        foundhost.update({"type": qualystag.text})
                                    if qualystag.tag == "lastSystemBoot":
                                        foundhost.update({"lastSystemBoot": qualystag.text})
                                    if qualystag.tag == "agentInfo":
                                        for agentinfo in qualystag:
                                            if agentinfo.tag == "agentVersion":
                                                foundhost.update({"agentVersion": agentinfo.text})
                                            if agentinfo.tag == "status":
                                                foundhost.update({"status": agentinfo.text})
                                            if agentinfo.tag == "lastCheckedIn":
                                                foundhost.update({"lastCheckedIn": agentinfo.text})
                                            if agentinfo.tag == "connectedFrom":
                                                foundhost.update({"connectedFrom": agentinfo.text})
                                            if agentinfo.tag == "activatedModule":
                                                foundhost.update({"activatedModule": agentinfo.text})
                                            if agentinfo.tag == "platform":
                                                foundhost.update({"platform": agentinfo.text})
                                    if qualystag.tag in uniquehostlist:
                                        pass
                                    else:
                                        uniquehostlist.append(qualystag.tag)
                                hostitems.append(foundhost)
        logging.debug("Host Items gathered")
        return hostitems






    def report(self, data, name):
        """Generates a CSV report using the keys from the dictionaries of lists has the header

        :param data - A list of dictionaries
        :param name - The prefix of the file name
        :return:
        """
        # Build header from list of dictionary keys
        keys = []
        for d in data:
            for i,v in d.items():
                if i in keys:
                    pass
                else:
                    keys.append(i)

        #newkey = [i for d in data for i,v in d.items() if i not in keys]

        fname = "{}_{}.csv".format(name,str(datetime.datetime.now().date()))
        logging.debug("Filename will be: {}".format(fname))
        with open(fname, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, keys)
            writer.writeheader()
            writer.writerows(data)
            csvfile.flush()
            csvfile.close()


    #TODO Review and possibly delete everything below if not needed soon

    # how to return the session
    def loginrequest(self, api = '/api/2.0/fo/session/'):
        logindata = {"action": "login", "username": self.username, "password": self.password}
        login = self.session.post(url="https://" + self.url + api, data=logindata, headers=self.headers)
        return login.status_code

    def logoutrequest(self, api = '/api/2.0/fo/session/'):
        #Logout Request. You may get concurrent login requests error. Always have logout request.
        logoutdata = {'action': 'logout'}
        logout = self.session.post(url="https://" + self.url + api, data=logoutdata, headers=self.headers)
        return logout.status_code

    # Get portal version for debug purposes
    def getportalversion(self):
        api = "/qps/rest/portal/version"
        headers = {'Accept': 'application/xml'}
        output = requests.get("https://"+ self.url + api, headers=headers, auth=(self.username, self.password))
        logging.debug("Portal version headers: {}".format(output.headers))
        logging.debug("Portal version content: {}".format(output.content))

    # Count tags
    def gettagcount(self):
        api = "/qps/rest/1.0/count/am/tag"
        headers = {'Content-Type': 'text/xml', 'Cache-Control': 'no-cache'}
        output = requests.post("https://" + self.url + api, headers=headers,
                               auth=(self.username, self.password))
        if output.status_code == 200:
            tree = ET.ElementTree(ET.fromstring(output.content))
            root = tree.getroot()
            for child in root:
                if child.tag == "count":
                    logging.debug("Count is: {}".format(child.text))
        else:
            logging.debug("Agent count query was not successful\nHeaders: {}\nContent: {}".format(output.headers,
                                                                                          output.content))

    # Get all tags
    def gettaglist(self):
        tagitems = []
        uniquetaglist = []
        hasmore = "false"
        lastid = 0
        while True:
            xml = '''<?xml version="1.0" encoding="UTF-8" ?> 
            <ServiceRequest>     
                <filters>         
                    <Criteria field="id" operator="GREATER">{}</Criteria>     
                </filters> 
            </ServiceRequest>'''.format(lastid)
            api = "/qps/rest/1.0/search/am/tag"
            headers = {'Content-Type': 'text/xml', 'Cache-Control': 'no-cache'}
            output = requests.post("https://" + self.url + api, data=xml, headers=headers,
                                   auth=(self.username, self.password))
            if output.status_code == 200:
                tree = ET.ElementTree(ET.fromstring(output.content))
                root = tree.getroot()
                for child in root:

                    if child.tag == "responseCode":
                        pass
                        # May need this for error handling
                    if child.tag == "count":
                        pass
                    if child.tag == "hasMoreRecords":
                        hasmore = child.text
                    if child.tag == "lastId":
                        lastid = child.text
                    if child.tag == "data":
                        for tagdata in child:
                            # Parse each tag and store attributes in dictionary
                            if tagdata.tag == "Tag":
                                foundtag = {}
                                for qualystag in tagdata:
                                    if qualystag.tag == "id":
                                        foundtag.update({"id": qualystag.text})
                                    if qualystag.tag == "uuid":
                                        foundtag.update({"uuid": qualystag.text})
                                    if qualystag.tag == "name":
                                        foundtag.update({"name": qualystag.text})
                                    if qualystag.tag in uniquetaglist:
                                        pass
                                    else:
                                        uniquetaglist.append(qualystag.tag)
                                tagitems.append(foundtag)

            else:
                logging.debug("Agent count query was not successful\nHeaders: {}\nContent: {}".format(output.headers,
                                                                                              output.content))

            if hasmore == "false":
                break

        # Returns list of dictionaries with id, uuid, and name included
        logging.debug("Finished processing all pages")
        logging.debug("Creating Report...")
        logging.debug("Total tags: {}".format(len(tagitems)))
        self.report(tagitems, "tags")
        return tagitems


    def testcreds(self):
        """
        Ensure creds authenticate to Qualys
        :return:
        """
        wait = 3
        logging.debug("Testing creds")
        login_code = self.loginrequest()
        if login_code == 200:
            logging.debug("Successful login")
        else:
            logging.debug("Failed login")
        logging.debug("Waiting for {} seconds".format(wait))
        time.sleep(wait)
        logout_code = self.logoutrequest()
        if logout_code == 200:
            logging.debug("Succesful logout")
        else:
            logging.debug("Failed logout")
