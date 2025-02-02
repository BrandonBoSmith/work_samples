# Create beta test project
module "os-project" {
  source = "../modules/project"
  providers = {
    openstack = openstack.admin
  }
  os_admin_user     = var.os_admin_user
  os_admin_password = var.os_admin_password
  os_project        = var.os_project
  os_user           = var.os_user
  os_password       = var.os_password
}

# Create beta server and network
module "os-infrastructure" {
  source      = "../modules/infrastructure"
  network_id  = module.os-project.network_id
  floating_ip = module.os-project.floating_ip
  user_id     = module.os-project.user_id
  providers = {
    openstack = openstack.user
  }
  depends_on = [
    module.os-project.user_id
  ]
}