#!/usr/bin/env python3
'''
Script to get all alert definitions from Prometheus
'''

import argparse
import csv
import json
import pprint
import requests


def get_args():
    '''
    Get all arguments

    Returns
    =======
        args: ``object`` argparse object
    '''
    parser = argparse.ArgumentParser(
        description="Script to get all alert definitions from Prometheus"
    )
    parser.add_argument(
        '-p',
        '--port',
        action='store',
        default='9090',
        help='Prometheus api port (default 9090)'
    )
    return(parser.parse_args())


def get_alerts(args):
    '''
    Request all alert rules from the Prometheus API
    '''
    try:
        r = requests.get(
            f"http://localhost:{args.port}/api/v1/rules?type=alert",
            headers={'content-type': 'application/json'}
        )
        return(r.json())
    except Exception as err:
        print(str(err))


def write_to_csv(args, alerts):
    '''
    Write alert data out to a CSV file
    '''
    columns = ['alert', 'query']
    rows = []
    for group in alerts['data']['groups']:
        for alert in group['rules']:
            tmp = {}
            tmp['alert'] = alert['name']
            tmp['query'] = alert['query']
            rows.append(tmp)

    try:
        with open('openshift_alerts.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    except IOError as err:
        print(str(err))


def main():
    '''
    Welcome to the party pal!!
    '''
    args = get_args()
    alerts = get_alerts(args)
    write_to_csv(args, alerts)

if __name__ == '__main__':
    main()
