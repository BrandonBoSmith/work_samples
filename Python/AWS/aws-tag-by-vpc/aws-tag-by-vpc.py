#!/usr/bin/env python
"""
Lambda function to pull all ec2 instances from a given AWS VPC and tag them
with a the provided tag.

Author:     Bo Smith (bo@bosmith.tech)

Date:       2021-12-1
"""

import argparse
import boto3
import re
import sys


def get_args():
    """
    Gather CLI arguments and parse for usage in other functions

    Returns:
        ``(args)``: argparse() object
    """
    parser = argparse.ArgumentParser(
        description="Code to auto tag EC2 instances by VPC ID"
    )
    parser.add_argument(
        '-a',
        '--accesskey',
        action='store',
        required=True,
        help='AWS Access Key'
    )
    parser.add_argument(
        '-s',
        '--secretkey',
        action='store',
        required=True,
        help='AWS Secret Key'
    )
    parser.add_argument(
        '-t',
        '--tag',
        action='store',
        required=True,
        help='Tag to apply in the format of tag=value'
    )
    parser.add_argument(
        '-v',
        '--vpcid',
        action='store',
        required=True,
        help='VPC ID'
    )
    parser.add_argument(
        '--dryrun',
        action='store_true',
        default=False,
        required=False,
        help='Dry Run, will not actually apply the tag'
    )
    return(parser.parse_args())

def setup_client(args):
    """
    Setup and authenticate the boto3 client with provided creds

    Returns
        ``(client)``: boto3 authenticated client object
    """
    try:
        client = boto3.client(
            'ec2',
            aws_access_key_id=args.accesskey,
            aws_secret_access_key=args.secretkey
        )
        return(client)
    except Exception as err:
        print(str(err))


def get_instances_in_vpc(args, client):
    """
    Get list of instances in the vpc using the boto3 authenticated client

    Returns:
        ``(instances)``: dict Dictonary of instances
    """
    try:
        i = client.describe_instances(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [args.vpcid]
                }
            ]
        )
        return(i)
    except Exception as err:
        print(str(err))


def add_tag(args, client, instance, tagname, tagvalue):
    """
    Helper function to add a tag to a given instance
    """
    try:
        t = client.create_tags(
            DryRun=args.dryrun,
            Resources=[
                instance
            ],
            Tags=[
                {
                    'Key': tagname,
                    'Value': tagvalue
                }
            ]
        )
    except Exception as err:
        print(str(err))


def get_tags(args, client, instances):
    """
    Review the list of all the ec2 instances and see if the provided tag exists
    If not, add it.  Do not add tags if its not necessary (idempotency)
    
    Prints summary of actions taken
    """
    # Prep the tag, bail out if provided in wrong format
    if re.search(r'(\w+|\w+\s)=(\w+|\s\w+)', args.tag) is None:
        print('Unable to parse tag. Please provide tag in tag=value format.')
        sys.exit(1)
    else:
        tagname = args.tag.split('=')[0].strip()
        tagvalue = args.tag.split('=')[1].strip()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instanceid = instance.get('InstanceId')
            # Check all tags for the provided tag
            try:
                dt = next(
                    (i['Key'] for i in instance.get('Tags', None) if i['Key'] == args.tag),
                    None
                )
            except:
                dt = None

            # Add the tag if it is missing
            if dt == None:
                print(f"Adding tag {args.tag} to {instance.get('PrivateDnsName')}")
                add_tag(args, client, instanceid, tagname, tagvalue)


def main():
    """
    Welcome to the party pal
    Git-r-done
    """
    args = get_args()
    client = setup_client(args)
    instances = get_instances_in_vpc(args, client)
    get_tags(args, client, instances)


if __name__ == '__main__':
    main()