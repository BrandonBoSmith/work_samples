
# Data for Role
data "openstack_identity_role_v3" "member" {
  name = "member"
}

# User
resource "openstack_identity_user_v3" "project_user" {
  default_project_id                    = openstack_identity_project_v3.beta_project_1.id
  name                                  = var.os_user
  password                              = var.os_password
  description                           = "OS Beta User"
  ignore_change_password_upon_first_use = true
  multi_factor_auth_enabled             = true
}

# Membership
resource "openstack_identity_role_assignment_v3" "os_member_role" {
  project_id = openstack_identity_project_v3.beta_project_1.id
  role_id    = data.openstack_identity_role_v3.member.id
  user_id    = openstack_identity_user_v3.project_user.id
}