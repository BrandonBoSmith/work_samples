# OpenStack Hosted NextCloud Image
Here is an example of a project that was completed for a client.
This project creates
* Creates an OpenStack project
* Creates a network
* Creates a router
* Connects the internal network to the router
* Creates a server
* Deploys Nextcloud on the server with a userdata script

# Dependencies
This automation is built on a combination of tools and technologies.
* Terraform (OpenTofu)
* Makefile (make)
* ssh-keygen (Linux/Mac)
* Git (cli)

## deploy.sh Overview
The automation performs the following steps.
* Checks for a nextcloud file
    * If the file does not exist, `ssh-keygen` is executed to create a new SSH key
* Runs `tofu plan` to check for what resources exist and which need created
* Runs `tofu apply` to build necessary resources
* Outputs the public IP of the nextcloud server which is intended to be access via a nip.io address
    * Example: IP 12.205.43.250 == 12-205-43-250.nip.io

# How to Deploy
1.  Copy an existing project folder to a new directory
    Example:
    ```
    ./deploy.sh project1 project1_user
    ```
4.  Profit!  That's it

