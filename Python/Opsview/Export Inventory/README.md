# Export Inventory

## Overview
This script was built to export all of the hosts and service checks in an Opsview monitoring environment.  This was often a business needs for clients, operations and engineering teams alike.

## How
This script uses the `requests` module to make api calls to Opsview.
These calls retrieve the hosts and service checks assigned to each host.
Once this information is retrieved, the script dumpts this information into a spreadsheet using the `xlsxwriter` module.