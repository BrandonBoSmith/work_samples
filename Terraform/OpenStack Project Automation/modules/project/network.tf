# Router
resource "openstack_networking_router_v2" "router1" {
  name                = "router1"
  admin_state_up      = true
  external_network_id = var.os_public_net_id
  tenant_id           = openstack_identity_project_v3.beta_project_1.id
}

# Network
resource "openstack_networking_network_v2" "internal_network" {
  name           = "internal"
  admin_state_up = "true"
  tenant_id      = openstack_identity_project_v3.beta_project_1.id
}

# Subnet
resource "openstack_networking_subnet_v2" "internal_subnet" {
  name      = "internal-subnet"
  tenant_id = openstack_identity_project_v3.beta_project_1.id
  # tenant_id  = var.os_project_id
  network_id = openstack_networking_network_v2.internal_network.id
  cidr       = "10.0.0.0/24"
  ip_version = 4
  dns_nameservers = [
    "8.8.8.8",
    "8.8.4.4",
  ]
}

# Router Subnet Interface
resource "openstack_networking_router_interface_v2" "router_interface_1" {
  router_id = openstack_networking_router_v2.router1.id
  subnet_id = openstack_networking_subnet_v2.internal_subnet.id
}

# Security Groups
# Nextcloud Security Group
resource "openstack_networking_secgroup_v2" "nextcloud-sg" {
  name        = "Nextcloud"
  description = "Nextcloud Access Port 80/443"
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# Nextcloud port 80
resource "openstack_networking_secgroup_rule_v2" "nextcloud-sg-rule-80" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nextcloud-sg.id
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# Nextcloud port 443
resource "openstack_networking_secgroup_rule_v2" "nextcloud-sg-rule-443" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nextcloud-sg.id
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# Nextcloud port 8443
resource "openstack_networking_secgroup_rule_v2" "nextcloud-sg-rule-8443" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 8443
  port_range_max    = 8443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nextcloud-sg.id
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# Nextcloud port 3478
resource "openstack_networking_secgroup_rule_v2" "nextcloud-sg-rule-3478" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 3478
  port_range_max    = 3478
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nextcloud-sg.id
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# Nextcloud port 3478
resource "openstack_networking_secgroup_rule_v2" "nextcloud-sg-rule-3478-udp" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "udp"
  port_range_min    = 3478
  port_range_max    = 3478
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nextcloud-sg.id
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# SSH Security Group
resource "openstack_networking_secgroup_v2" "ssh-sg" {
  name        = "SSH"
  description = "SSH access port 22"
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# SSH port 22
resource "openstack_networking_secgroup_rule_v2" "ssh-sg-rule-22" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.ssh-sg.id
  tenant_id   = openstack_identity_project_v3.beta_project_1.id
}

# Floating IP
resource "openstack_networking_floatingip_v2" "nextcloud-fip" {
  pool      = "public"
  tenant_id = openstack_identity_project_v3.beta_project_1.id
}