#!/usr/bin/python3
###############################################################################
'''
Description:    Rundeck script that performs automated add or remove tasks in
                Opsview.  Task is triggered by an AWS Lambda Function
Author:         Bo Smith (bo@bosmith.tech)  wassup ;)
Date:           2019-07-29
'''
###############################################################################
import argparse
import json
import requests
import pprint
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Parse Arguments
###############################################################################
def get_args():
    action_list = ['add', 'remove']
    parser = argparse.ArgumentParser(
        usage='%(prog)s -H -I -O --add --remove',
        description='Automation script to perform operations on Opsview hosts'
    )
    parser.add_argument(
        '-H', '--hostname', action='store', required=True, metavar='',
        help='Instance Hostname'
    )
    parser.add_argument(
        '-I', '--ip', action='store', nargs='*', default=None, metavar='',
        help='Instance IP'
    )
    parser.add_argument(
        '-O', '--os', action='store', required=False, metavar='',
        help='Instance OS'
    )
    parser.add_argument(
        '-S', '--slave', action='store', required=False, metavar='',
        help='Opsview Slave Cluster Name (Default is Master Monitoring Server'
    )
    parser.add_argument(
        '-g', '--hostgroup', action='store', required=False, metavar='',
        help='Opsview Hostgropu Name'
    )
    parser.add_argument(
        '--action', action='store', default=False,
        choices=action_list,
        help='Add or Remove instance'
    )
    parser.add_argument(
        '-u', '--user', action='store', required=False, metavar='',
        help='User Rundeck will use to authenticate with Opsview\'s API'
    )
    parser.add_argument(
        '-p', '--password', action='store', required=False, metavar='',
        help='User password Rundeck will use to authenticate with Opsview\'s API'
    )
    parser.add_argument(
        '--ssh_user', action='store', required=False, metavar='',
        help='SSH User account Opsview will use to monitor the instance'
    )
    parser.add_argument(
        '--ssh_key', action='store', required=False, metavar='',
        help='SSH Key Opsview will use to monitor the instance'
    )
    parser.add_argument(
        '--winrm_user', action='store', required=False, metavar='',
        help='WinRM User account Opsview will use to monitor the instance'
    )
    parser.add_argument(
        '--winrm_pass', action='store', required=False, metavar='',
        help='WinRM Password Opsview will use to monitor the instance'
    )
    parser.add_argument(
        '--url', action='store', required=True, metavar='',
        help='Opsview API URL'
    )
    args = parser.parse_args()
    return(args)


# Login to Opsview and get the auth token
###############################################################################
def get_headers(args):
    url = args.url
    headers = {'Content-Type': 'application/json'}
    try:
        ol = requests.post(
            url+'/login',
            auth=(args.user, args.password),
            headers=headers, verify=False
        )
    except Exception as err:
        print('ERROR logging in '+str(err))
        sys.exit(1)
    headers['X-Opsview-Username'] = args.user
    headers['X-Opsview-Token'] = ol.json()['token']
    return(headers)


# Get Host Template
###############################################################################
def get_template(args):
    # If this is a Linux host, grab the Linux template
    if args.os.lower() == 'linux':
        try:
            # with open('./rd_opsview_host_linux_template.json', 'r') as f:
            with open('/home/rundeck/server/data/scripts/rundeck_scripts/rd_opsview_host_linux_template.json', 'r') as f:
                tmp = json.load(f)
        except Exception as err:
            print('ERROR reading template file '+str(err))
            sys.exit(1)

    # If this is a Windows host, grab the Windows template
    elif args.os.lower() == 'windows':
        try:
            # with open('./rd_opsview_host_windows_template.json', 'r') as f:
            with open('/home/rundeck/server/data/scripts/rundeck_scripts/rd_opsview_host_windows_template.json', 'r') as f:
                tmp = json.load(f)
        except Exception as err:
            print('ERROR reading template file '+str(err))
            sys.exit(1)
    else:
        print('ERROR - Unrecognized argument.  Expecting windows or linux')
        sys.exit(1)
    return(tmp)


# Update host template
###############################################################################
def update_template(args, template):
    template['object']['name'] = args.hostname
    try:
        template['object']['ip'] = args.ip[0]
    except:
        print('Unable to get ip from '+str(args.ip))
        sys.exit(1)
    template['object']['monitored_by']['name'] = args.slave
    if args.hostgroup:
        template['object']['hostgroup']['name'] = args.hostgroup
    if args.os.lower() == 'linux':
        tmp = {}
        tmp['arg1'] = args.ssh_user
        tmp['arg3'] = args.ssh_key
        tmp['name'] = 'SSHCREDENTIALS'
        tmp['value'] = 'sshcreds'
        template['object']['hostattributes'].append(tmp)
    return(template)


# Add host to Opsview
###############################################################################
def add_host(args, headers, host):
    url = args.url+'/config/host'
    try:
        res = requests.post(
            url,
            data=json.dumps(host),
            headers=headers,
            verify=False
        )
    except Exception as err:
        print('ERROR adding host')
        print('ERROR - '+str(err))
        sys.exit(1)
    return(res)


# Remove host from Opsview
###############################################################################
def remove_host(args, headers):
    url = args.url+'/config/host'
    try:
        i = requests.get(
            url+'?json_filter={"name": "'+args.hostname+'"}&cols=id',
            headers=headers,
            verify=False
        ).json()
        host = i['list'][0]['id']
    except Exception as err:
        print('ERROR - Unable to get host id. Does the host exist?')
        print('ERROR - '+str(err))
        sys.exit(1)
    try:
        res = requests.delete(
            url+'/'+host+'?changelog=Automated host removal by Rundeck',
            headers=headers,
            verify=False
        )
    except Exception as err:
        print('ERROR - '+str(err))
        sys.exit(1)
    return(res)


# Reload Opsview
###############################################################################
def reload_opsview(args, headers):
    url = args.url+'/reload?changelog=Automated reload from Rundeck'
    try:
        rel = requests.post(
            url,
            headers=headers,
            verify=False
        )
    except Exception as err:
        print('ERROR Reloading Opsview')
        print('ERROR - '+str(err))
        sys.exit(1)
    if rel.status_code == 200:
        print('OK - Reload successful')
        pprint.pprint(rel.json())
    elif rel.json()['status'] == '1':
        print('WARNING - Reload already in progress.  Check Opsview')
        sys.exit(1)
    else:
        print('ERROR reloading Opsview')
        sys.exit(1)


# Main git-r-done ...
###############################################################################
def main():
    args = get_args()
    headers = get_headers(args)

    # Parse options and decide what to do
    if args.action == 'add':
        template = get_template(args)
        host = update_template(args, template)
        result = add_host(args, headers, host)
        pprint.pprint(result)
        pprint.pprint(result.json())
        if result.status_code == 200:
            print('Reloading Opsview')
            reload_opsview(args, headers)
        else:
            print('There was a problem adding the host')
    elif args.action == 'remove':
        result = remove_host(args, headers)
        pprint.pprint(result)
        pprint.pprint(result.content)
        if result.json()['success'] == '1':
            print('Reloading Opsview')
            reload_opsview(args, headers)
        else:
            print('There was a problem removing the host')


if __name__ == '__main__':
    main()
