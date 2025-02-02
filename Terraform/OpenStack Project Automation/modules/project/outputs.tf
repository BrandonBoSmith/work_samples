output "project_id" {
  value = openstack_identity_project_v3.beta_project_1.id
}

output "user_id" {
  value = openstack_identity_user_v3.project_user.id
}

output "network_id" {
  value = openstack_networking_network_v2.internal_network.id
}

output "floating_ip" {
  value = openstack_networking_floatingip_v2.nextcloud-fip.address
}