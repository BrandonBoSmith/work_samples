variable "os_admin_user" {
  type        = string
  description = "OS Admin User"
}

variable "os_admin_password" {
  type        = string
  description = "OS Admin User Password"
  sensitive   = true
}

variable "os_user" {
  type        = string
  description = "OS Beta user"
}

variable "os_password" {
  type        = string
  description = "OS Beta user password"
}

variable "os_project" {
  type        = string
  description = "OS Project"
}

variable "os_public_net_id" {
  type        = string
  description = "UUID of 'public' network"
}
