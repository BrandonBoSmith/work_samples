# AWS-TAG-BY-VPC
## Why
This code was written for a fairly unique situation where there was a need to tag a certain VPC with a lot of EC2 instances.  The uniqueness of the situation created a scenario that was both urgent and had limited options.

## How
The code uses the `boto3` module to interact with AWS and retrieve the list of EC2 instances that are contained in a given VPC.

From there the code, assigns the tag that was provided via arguments to each ec2 instance.

## Script Flow
1. Retrieve arguments with argparse
2. Instantiate boto3 `client` object
3. Retrieve the list of ec2 instances contained in the VPC provided in the arguments
4. For each ec2 instance, evaludate if the tag exists or not (idempotency)
5. If the tag does not exist, add the tag.