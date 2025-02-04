#!/usr/bin/env python3


import requests
import xlsxwriter
import argparse
from configobj import ConfigObj
import urllib3
import pprint
import re
import random
import logging
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(filename="/tmp/exportallhosts.log")


config = ConfigObj(os.getenv("OPSVIEW_API_CONFIG"))
username = config['opsview']['username']
password = config['opsview']['password']
opsview_url = config['opsview']['rest_url']
opsview_base_url = opsview_url[0:len(opsview_url) - 5]
opsview_login = opsview_url + '/login'
opsview_host = opsview_url + '/config/host'
opsview_hostgroup = opsview_url + '/config/hostgroup'
opsview_service_list = opsview_url + '/status/service'
opsview_testservicecheck = opsview_url + "/testservicecheck"

host_urls = []
opsview_hosts_info = []
opsview_hosts = []

session = requests.Session()


def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-g', dest="host_groups",
                           nargs="+", action="store", default=None)
    argparser.add_argument("-f", dest="host_file",
                           action="store", default=None)
    args = argparser.parse_args()
    return args


def parse_host_file(file):
    hosts = []
    with open(file) as host_file:
        for line in host_file:
            n_line = line.rstrip("\n")
            hosts.append(n_line)
    return hosts


def get_host(name):
    nurl = opsview_url + \
        '/config/host?json_filter={"name": "' + name + '"}&cols=id,ref,name'
    try:
        req = session.get(nurl, verify=False)
        host = req.json()['list'][0]
        return host
    except Exception as err:
        print(err)


def login():
    try:
        request = session.post(opsview_login, json={
            "username": username, "password": password, "Content-Type": "application/json"}, verify=False)
        requestJSON = request.json()
        login_token = requestJSON["token"]
        session.headers.update({"Content-Type": "application/json",
                                "X-Opsview-Username": username, "X-Opsview-Token": login_token})
    except Exception as err:
        logging.error(f"There was an error: {err}")


def get_host_groups(group):

    try:
        new_opsview_url = opsview_url[0:len(opsview_url) - 5]

        newurl = new_opsview_url + group
        newurl += '&cols=id&cols=name&cols=hostattributes'

        host_groups_request = session.get(
            newurl, verify=False)
        host_group = host_groups_request.json()['object']

        host_children = host_group['children']

        children_count = len(host_children)

        if children_count > 0:
            for child in host_children:
                get_host_groups(child['ref'])
        else:
            hosts = host_group['hosts']
            if len(hosts) != 0:
                for host in hosts:
                    host_urls.append(host['ref'])
    except Exception as err:
        logging.error(f"There was an error: {err}")


def get_host_group_urls(host_groups):

    host_group_urls = []

    for group in host_groups:
        try:
            newurl = opsview_hostgroup + \
                '?json_filter={"name":"' + group + '"}'
            newurl += '&cols=id&cols=name&cols=hostattributes'
            host_groups_request = session.get(
                newurl, verify=False)
            host_groups_list_ref = host_groups_request.json()['list'][0]['ref']
            host_group_urls.append(host_groups_list_ref)

        except Exception as err:
            logging.error(f"There was an error: {err}")

    return host_group_urls


def get_opsview_hosts():
    new_opsview_url = opsview_url[0:len(opsview_url) - 5]
    for host_ref in host_urls:
        try:
            hostget = session.get(new_opsview_url + '{}?cols=id,name,ip,icon'.format(
                host_ref), verify=False)
            host = hostget.json()['object']
            opsview_hosts_info.append(host['name'])
        except Exception as err:
            logging.error(f"There was an error: {err}. Host ref: {host_ref}")
            pass


def get_service_check_list(name):
    try:
        url = '{}?host={}'.format(opsview_service_list, name)
        req = session.get(url)
        j = req.json()['list']
        d = {}
        if len(j) > 0:
            d['services'] = j[0]['services']
            d['name'] = name
            return d
        else:
            pprint.pprint(j)
            return None
    except Exception as err:
        pprint.pprint(f"Get service :{name}. Error{err}")
        logging.error(f"Get service :{name}. Error{err}")
        return None


def parse_services(data):
    try:
        obj = {}
        obj['name'] = data['name']
        obj['services'] = []
        for service in data['services']:
            obj['services'].append(service['name'])
        return obj
    except Exception as err:
        logging.error(f"There was an error: {err}")


def get_args(data):
    try:
        new_service_list = []
        name = data['name']
        for service in data['services']:
            url = f"{opsview_testservicecheck}?hostname={name}&servicename={service}&cols=args"
            req = session.get(url)
            j = req.json()
            if 'args' in j:
                serv = {service: j['args']}
                new_service_list.append(serv)
            else:
                print(j)
        data['services'] = new_service_list
        return data
    except Exception as err:
        print(err)


def write_to_sheet():
    try:
        workbook = xlsxwriter.Workbook(
            "/tmp/host_export.xlsx")
        for host in opsview_hosts:
            if host is not None:
                name = host['name']
                if len(name) > 31:
                    name = name[0:30]
                worksheet = workbook.add_worksheet(name)
                col = 0
                row = 1
                worksheet.write(0, 0, "Service Check")
                worksheet.write(0, 1, "Arguments")
                for service in host['services']:
                    for key, value in service.items():
                        worksheet.write(row, col, key)
                        worksheet.write(row, col + 1, value)
                        row += 1
        workbook.close()
    except Exception as err:
        logging.error(f"There was an error writing excel: {err}")
        pass


def main():
    args = parse_args()
    login()
    if args.host_groups:
        hg_urls = get_host_group_urls(args.host_groups)
        for h_url in hg_urls:
            get_host_groups(h_url)
        get_opsview_hosts()
    elif args.host_file:
        hosts = parse_host_file(args.host_file)
        for host in hosts:
            opsview_hosts_info.append(host)
    for host in opsview_hosts_info:
        services = get_service_check_list(host)
        if services:
            parsed_services = parse_services(services)
            all_data = get_args(parsed_services)
            opsview_hosts.append(all_data)
    write_to_sheet()


if __name__ == '__main__':
    main()
