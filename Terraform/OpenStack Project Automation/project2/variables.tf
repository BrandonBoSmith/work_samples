variable "os_project" {
  type    = string
  default = "project2"
}

variable "os_user" {
  type    = string
  default = "project_user2"
}

variable "os_password" {
  type    = string
  default = "##########"
}

variable "os_admin_user" {
  type        = string
  description = "OS Admin User"
}

variable "os_admin_password" {
  type        = string
  description = "OS Admin User Password"
  sensitive   = true
}
