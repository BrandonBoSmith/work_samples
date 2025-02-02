#!/bin/bash
# Script to deploy new environment

PROJECT=$1
USER=$2
STARTDIR=$(pwd)

echo "########## Checking variables ##########"
if [ -z $PROJECT ]; then
    echo "PROJECT not provided, please provide a project"
    exit
fi

if [ -z $USER ]; then
    echo "USER not provided, please provide a user"
    exit
fi

if [ -d $PROJECT ]; then
    echo "ERROR: $PROJECT already exists, please choose a different project"
    exit
fi

if [ -z ${TF_VAR_os_admin_user} ]; then
    echo "ERROR: TF_VAR_os_admin_user is not set"
    exit
fi

if [ -z ${TF_VAR_os_admin_password} ]; then
    echo "ERROR: TF_VAR_os_admin_password is not set"
    exit
fi

echo "PROJECT: $PROJECT"
echo "USER: $USER"


echo "########## Generating Password for $USER ##########"
PASSWORD=$(date +%s | sha256sum |base64 |head -c 12; echo)
# PASSWORD=$(openssl rand -base64 12)
if [ -z $PASSWORD ]; then
    echo "ERROR: An error occurred creating the password"
    exit
fi
# echo "PASSWORD: $PASSWORD"

echo "########## Creating Terraform Assets ##########"
cp -r _template $PROJECT


echo "########## Setting Terraform Variables ##########"
sed -i "s/PROJECT/$PROJECT/" $PROJECT/variables.tf
sed -i "s/USER/$USER/" $PROJECT/variables.tf
sed -i "s/PASSWORD/$PASSWORD/" $PROJECT/variables.tf


echo "########## Building Project $PROJECT with User $USER ##########"
cd $PROJECT
make plan
make apply
cd $STARTDIR
