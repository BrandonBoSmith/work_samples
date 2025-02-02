output "public_ip" {
  value = module.os-project.floating_ip
}

output "username" {
    value = var.os_user
}

output "password" {
    value = var.os_password
}