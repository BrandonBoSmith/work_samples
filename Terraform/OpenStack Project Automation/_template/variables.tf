variable "os_project" {
  type    = string
  default = "PROJECT"
}

variable "os_user" {
  type    = string
  default = "USER"
}

variable "os_password" {
  type    = string
  default = "PASSWORD"
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
