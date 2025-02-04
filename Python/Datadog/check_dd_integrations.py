#!/usr/bin/env python3
"""
Description     Script for the purpose of identifying any integrations
                that
                - Integration discovered but not configured
                - Integration configured but no monitor exists
                This is intended to help deploy standards and not meant
                to identify a missing monitor for every unique metric.
                The idea is to automate the process of discovery by 
                leveraging Datadog's capabilities and not rely on humans
                for information.

Created:        2024-06-13
Author:         Bo Smith (bo@bosmith.tech)
Requirements:   
                - python requests module
                - python pygithub module
                - Datadog organization
                - Datadog api key
                - Datadog app key
                - Hold my beer
"""

import argparse
import csv
import github
import logging
import json
import requests
import pprint
import sys


################################################################################
# PESA Supported Integrations
################################################################################
# TODO Read this data from github 
pesa_supported = [
    "aws.apigateway.5xx",
    "aws.apigateway.latency",
    "aws.applicationelb.healthy_host_count",
    "aws.dynamodb.successful_request_latency",
    "aws.dynamodb.system_errors",
    "aws.dx",
    "aws.elb",
    "aws.lambda.throttles",
    "aws.networkelb.healthy_host_count",
    "aws.rds.database_connections",
    "aws.rds.cpuutilization",
    "aws.rds.free_storage_space",
    "aws.vpn.tunnel_state",
    "azure.dbforpostgresql_servergroupsv2.cpu_percent",
    "azure.network_virtualnetworkgateways.bgp_peer_status",
    # "azure.containerservice_managedclusters.status",
    # "azure.containerservice_managedclusters.node_memory_rss_percentage",
    # "azure.containerservice_managedclusters.node_memory_working_set_percentage",
    # "azure.containerservice_managedclusters.node_disk_usage_percentage",
    # "azure.containerservice_managedclusters.kube_node_status_condition",
    # "azure.containerservice_managedclusters.kube_pod_status_phase",
    "azure.datafactory_factories.pipeline_failed_runs",
    "azure.functions.http4xx",
    "azure.functions.http5xx",
    "azure.logic_workflows.runs_failed",
    "azure.netapp_netappaccounts_capacitypools_volumes.volume_logical_size",
    "azure.network_applicationgateways.healthy_host_count",
    "azure.network_applicationgateways.response_status",
    "azure.network_loadbalancers.backend_pool_host_count",
    "azure.network_loadbalancers.health_probe_status",
    "azure.network_loadbalancers.status",
    "azure.recoveryservices_vaults.backup_health_event",
    "gcp.router.bgp.session_up",
    "gcp.file.nfs.server.used_bytes_percent",
    "gcp.interconnect.network.attachment.received_packets_count",
    "gcp.loadbalancing.https.backend_latencies",
    "gcp.loadbalancing.https.backend_request_bytes_count",
    "gcp.loadbalancing.https.backend_response_bytes_count",
    "gcp.loadbalancing.https.backend_request_count",
    "gcp.loadbalancing.https.total_latencies.p99",
    "gcp.loadbalancing.https.request_bytes_count",
    "gcp.loadbalancing.https.response_bytes_count",
    "gcp.loadbalancing.https.request_count",
    "custom_check.gcp_ilb_healthy_hosts.healthy_percentage",
    "custom_check.gcp_compute_snapshot.failed_snapshots",
    "custom_check.gcp_compute_snapshot.missing_snapshots",
    "custom_check.gcp_compute_snapshot.no_existing_snapshots",
    "custom_check.gcp_compute_snapshot.snapshot_zone_ops_errors",
    "custom_check.gcp_compute_snapshot.snapshot_zone_ops_warnings",
    "gcp.spanner.instance.cpu.utilization",
    "gcp.spanner.query_stat.total.failed_execution_count",
    "gcp.spanner.api.request_latencies.avg",
    "gcp.spanner.api.request_latencies.avg",
    "gcp.vpn.tunnel_established",
    "iis.app_pool_up",
    "kubernetes.containers.restarts",
    "kubernetes_state.deployment.replicas_desired",
    "kubernetes_state.node.disk_pressure",
    "kubernetes_state.pod.status_phase",
    "kubernetes_state.statefulset.replicas_desired",
    "kubernetes_state.node.memory_pressure",
    "kubernetes_state.node.status",
    "kubernetes_state.container.status_report.count.waiting",
    "kubernetes_state.pod.unschedulable",
    "sftp.can_connect",
    "ssh.can_connect",
    "w3svc",
    "nagios",
    "network.ping.can_connect",
    "network.http.response_time",
    "rabbitmq.aliveness",
    "rabbitmq.node.disk_alarm",
    "rabbitmq.node.mem_alarm",
    "rabbitmq.status",
    "snmp.can_check",
    "snmp.ifOperStatus",
    "snmp.ifHCInOctets.rate",
    "synthetics.http.response.time",
    "http.ssl_cert",
    "http.ssl.days_left",
    "tcp.can_connect",
    "system.cpu",
    "system.disk",
    "kafka.consumer_lag_seconds",
    "system.mem",
    "system.uptime",
    "vsphere.disk",
    "vsphere.disk.provisioned.latest",
    "vsphere.disk.used.latest",
    "vsphere.disk.maxTotalLatency.latest",
    "vsphere.sys.uptime.latest"
]





def get_args():
    """
    Function to get all arguments from the command line

    Returns
    =======
        args    '(object)' argparse object
    """
    parser = argparse.ArgumentParser(
        description="Script to automation integration discovery"
    )
    parser.add_argument(
        '--apikey',
        required=True,
        help="Datadog API key (Required)"
    )
    parser.add_argument(
        '--appkey',
        required=True,
        help="Datadog API key (Required)"
    )
    parser.add_argument(
        '-g',
        '--github',
        default=None,
        required=False,
        help="GitHub API Token (Optional Default is unauthenticated. Use a token when hitting rate limits)"
    )
    parser.add_argument(
        '-u',
        '--url',
        default="https://app.datadoghq.com",
        required=False,
        help="Datadog URL (optional Default: app.datadoghq.com)"
    )
    parser.add_argument(
        '--debug',
        action="store_true",
        default=False,
        help="Set loglevel to DEBUG"
    )
    return(parser.parse_args())


def setup_session(args):
    """"
    Setup a requests session() object with the required headers
    in order to authenticate calls to Datadog

    Returns
    =======
        session '(object)' requests.Session() object
    """
    logging.info("Setting up Session")
    session = requests.Session()
    session.headers.update({
        "DD-API-KEY": args.apikey,
        "DD-APPLICATION-KEY": args.appkey,
        "content-type": "application/json"
    })
    return(session)


def get_integrations(args, session):
    """
    This function identifies all of the integrations that are pulling
    metrics into the organization.  The agent metrics are a given with
    our standards so we are ignore those, however any other integrations
    that are flowing.

    Returns
    =======
        integrations    '(list)' List of unique source.integrations
    """
    integrations = []

    logging.info("Getting integrations")
    try:
        i = session.get(
            f"{args.url}/api/v2/metrics"
        )
        i.raise_for_status()
        metrics = i.json()['data']
    except requests.exceptions.HTTPError as err:
        logging.error(str(err))
        sys.exit(1)
    
    # Filter metrics by their integration
    for metric in metrics:
        # Split metric into source, target and ignore the rest
        source, target, *_ = metric['id'].split('.', 2)
        integration = f"{source}.{target}"
        if integration not in integrations:
            integrations.append(integration)

    logging.debug("Current Detected Integrations")
    logging.debug(pprint.pformat(integrations))
    return(integrations)


def get_monitors(args, session):
    """
    Function to retrieve currently implemented monitors to use as 
    a source to determine missing monitors compared to implemented
    integrations

    Returns
    =======
        list    List of monitor dictionaries
    """
    logging.info("Getting monitors")
    try:
        m = session.get(
            f"{args.url}/api/v1/monitor"
        )
        m.raise_for_status()
        logging.debug("Current Monitors")
        logging.debug(pprint.pformat(m.json()))
        return(m.json())
    except requests.exceptions.HTTPError as err:
        logging.error(str(err))
        sys.exit(1)


def get_processes(args, session):
    """
    Function to query running processes in the environment for the
    purpose of identifying supported integrations that need enabled
    at the agent level and also for checking appropriate monitors.

    Note that this is a hefty function as it aks Datadog for all processes
    it has observed over the last 15m from all systems and is returned
    in multiple pages.
    """
    logging.info("Getting processes")
    processes = {}
    raw_processes = []

    # Get all processes collected by Datadog over the last 15 minutes
    more = True
    cursor = ""
    limit=1000
    while more == True:
        if cursor == "":
            url = f"{args.url}/api/v2/processes?page[limit]={limit}"
        else:
            url = f"{args.url}/api/v2/processes?page[limit]=1000&page[cursor]={cursor}"
        try:
            p = session.get(
                f"{url}"
            )
            p.raise_for_status()
            raw_processes.extend(p.json()['data'])
            cursor = p.json()['meta']['page']['after']
            size = p.json()['meta']['page']['size']
            if int(size) < limit:
                more = False
            else:
                more = True
        except requests.exceptions.HTTPError as err:
            logging.error(str(err))
            sys.exit(1)

    # Process the ... processes ... yeah
    # for process in p.json()['data']:
    for process in raw_processes:
        pcs = process.get('attributes', None)
        host = pcs.get('host', None)
        # Group our discovered integrations by host so check for a host entry
        if host not in processes.keys():
            processes[host] = []
        # Use the integration tag to identify discovered integrations
        for tag in process['attributes']['tags']:
            if "integration" in tag:
                pcs = next((i for i in pcs.get('tags') if "integration" in i), None)
                pcs = pcs.split(':')[1].lower()
                if pcs not in processes.get(host, None):
                    processes[host].append(pcs)
    logging.debug("Detected Processes")
    logging.debug(pprint.pformat(processes))
    return(processes)


def main():
    """
    I shall peer into your environment's soul
    """
    args = get_args()
    # Setup logging
    if args.debug == True:
        logging.basicConfig(
            format='[%(levelname)-8s] - %(message)s',
            level=logging.DEBUG
        )
    else:
        logging.basicConfig(
            format='[%(levelname)-8s] - %(message)s',
            level=logging.INFO
        )

    session = setup_session(args)
    integrations = get_integrations(args, session)
    monitors = get_monitors(args, session)
    # dd_integrations = get_supported_integrations(args)
    processes = get_processes(args, session)

    # Evaluate if any processes were found without integrations and/or monitors
    for host, process in processes.items():
        for pcs in process:
            # Is the process/integration not found in metrics
            # meaning it was detected but not configured?
            if pcs not in integrations:
                logging.warning(
                    f"ACTION REQUIRED: Integration {pcs} identified on host: {host}, configure integration."
                )

    # Evaluate if any configured integrations are missing monitors
    for integration in integrations:
        # If the integration metric is not found in any monitor
        if next((i for i in monitors if integration in i['query']), None) is None:
            # If the integration is supported and has no monitor
            if next((i for i in pesa_supported if integration in i), None) is not None:
                logging.warning(f"ACTION REQUIRED: {integration} has no monitor") 

    session.close()


if __name__ == '__main__':
    main()