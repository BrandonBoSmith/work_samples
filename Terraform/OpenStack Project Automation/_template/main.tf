# Define required providers
terraform {
  required_version = ">= 0.14.0"
  required_providers {
    openstack = {
      source                = "terraform-provider-openstack/openstack"
      version               = "~> 1.53.0"
      configuration_aliases = [openstack.admin, openstack.user]
    }
  }
}

# Configure the OpenStack Provider
provider "openstack" {
  alias       = "admin"
  user_name   = var.os_admin_user
  tenant_name = "admin"
  password    = var.os_admin_password
  auth_url    = var.os_url
  region      = "us-east-1"
}


provider "openstack" {
  alias       = "user"
  user_name   = var.os_user
  tenant_name = var.os_project
  password    = var.os_password
  auth_url    = var.os_url
  region      = "us-east-1"
}