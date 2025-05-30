# Use the DigitalOcean terraform provider.
terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# Name of the VPS in Digital Ocean
variable "vps_name" {
  description = "Name of the VPS to create"
}

# Path to private SSH key
variable "pvt_key" {
  description = "Path to SSH private key"
}

# Personal access token to DigitalOcean
variable "do_token" {
  sensitive = true
  description = "DigitalOcean personal access token"
}

# ssh key name already created in DigitalOcean to install into VPS
variable "ssh_registered_key_name" {
  default = "terraform"
}

# Configure the DigitalOcean Provider to use my personal access token.
provider "digitalocean" {
  token = var.do_token
}

# Tell DigitalOcean provider to allow SSH connections with the "terraform" public key
data "digitalocean_ssh_key" "terraform" {
  name = var.ssh_registered_key_name
}

# Create the VPS
resource "digitalocean_droplet" "web" {
  name = var.vps_name
  image = "debian-12-x64"
  region = "syd1"
  size = "s-1vcpu-1gb"
  ssh_keys = [
    data.digitalocean_ssh_key.terraform.id
  ]
  
  # Waits for VPS to boot and ensures python is installed
  provisioner "remote-exec" {
    connection {
      host = self.ipv4_address
      user = "root"
      type = "ssh"
      private_key = file(var.pvt_key)
      timeout = "3m"
    }
    inline = [
      # Wait for unattended-upgrades to finish
      "while sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do sleep 5; done",
      "apt update",
      "apt install python3 -y"
    ]
  }
}

# Print json output with ip address of VPS(s)
output "node_details" {
  description = "Details of the VPS in JSON list format"
  value = jsonencode([
    {
      name       = digitalocean_droplet.web.name
      ip_address = digitalocean_droplet.web.ipv4_address
    }
  ])
}