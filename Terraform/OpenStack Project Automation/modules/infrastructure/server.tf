# Create a keypair
resource "openstack_compute_keypair_v2" "nextcloud-keypair" {
  name       = "nextcloud-key"
  public_key = file("nextcloud.pub")
  depends_on = [var.user_id]
}

resource "openstack_objectstorage_container_v1" "container_1" {
  name       = "keypair"
  depends_on = [var.user_id]
}

resource "openstack_objectstorage_object_v1" "keypair" {
  container_name = openstack_objectstorage_container_v1.container_1.name
  name           = "nextcloud.pem"
  source         = "./nextcloud"
  content_type   = "text/plain"
}


# Create a Nextcloud server
resource "openstack_compute_instance_v2" "nextcloud" {
  name            = "nextcloud"
  depends_on      = [var.user_id]
  image_id        = var.os_image_id
  flavor_id       = var.os_flavor_id
  key_pair        = "nextcloud-key"
  security_groups = ["default", "SSH", "Nextcloud"]
  block_device {
    uuid                  = var.os_image_id
    source_type           = "image"
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
    volume_size           = 50
  }
  network {
    uuid = var.network_id
  }

  user_data = <<-EOT
    #!/bin/bash
    # Setup Docker
    curl -fsSL https://get.docker.com | sudo sh

    # For Linux and without a web server or reverse proxy (like Apache, Nginx, Caddy, Cloudflare Tunnel and else) already in place:
    sudo docker run \
    --init \
    --sig-proxy=false \
    --name nextcloud-aio-mastercontainer \
    --restart always \
    --publish 80:80 \
    --publish 8080:8080 \
    --publish 8443:8443 \
    --volume nextcloud_aio_mastercontainer:/mnt/docker-aio-config \
    --volume /var/run/docker.sock:/var/run/docker.sock:ro \
    nextcloud/all-in-one:latest
  EOT
}

# Associate Floating IP
resource "openstack_compute_floatingip_associate_v2" "fip-associate" {
  floating_ip = var.floating_ip
  instance_id = openstack_compute_instance_v2.nextcloud.id
}