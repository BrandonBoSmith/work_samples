variable "os_image_id" {
  type        = string
  description = "UUID of Image to build server from"
}

variable "os_flavor_id" {
  type        = string
  description = "UUID of flavor to build server from"
}

variable "network_id" {
  type        = string
  description = "UUID of Network"
}

variable "floating_ip" {
  type        = string
  description = "Floating IP to Associate"
}

variable "user_id" {
  type        = string
  description = "ID of owning User"
}