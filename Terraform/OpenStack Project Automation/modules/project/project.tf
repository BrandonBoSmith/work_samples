# Create beta test project
resource "openstack_identity_project_v3" "beta_project_1" {
  name        = var.os_project
  description = "OS Beta Test Project"
}