# Use the DigitalOcean terraform provider.
terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
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

# Use the base image to create VPS with
variable "use_base_image" {
  description = "use the base image to create VPS with"
  default = false
}

# ssh key name already created in DigitalOcean to install into VPS
variable "ssh_registered_key_name" {
  default = "terraform"
}

# domain name time to live in seconds
variable "domain_ttl" {
  default = 120
}

# Configure the DigitalOcean Provider to use my personal access token.
provider "digitalocean" {
  token = var.do_token
}

# Tell DigitalOcean provider to allow SSH connections with the "terraform" public key
data "digitalocean_ssh_key" "terraform" {
  name = var.ssh_registered_key_name
}

# Create a private network for kubernetes to talk over
resource "digitalocean_vpc" "k8s_network" {
  name     = "k8s-network"
  region   = "syd1"
  ip_range = "10.0.0.0/24"
}

# Restore from an existing snapshot
data "digitalocean_droplet_snapshot" "k8s_snapshot" {
  name = "k8s_snapshot"
  count = var.use_base_image ? 0 : 1
}

# Create the VPS
resource "digitalocean_droplet" "k8s" {
  name = "k8s"
  image = var.use_base_image ? "ubuntu-24-04-x64" : data.digitalocean_droplet_snapshot.k8s_snapshot[0].id
  region = "syd1"
  size = "s-2vcpu-2gb"
  vpc_uuid = digitalocean_vpc.k8s_network.id
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
      "sudo apt update",
      "sudo apt install python3 -y"
    ]
  }
}

# Create a reserved IP address
resource "digitalocean_reserved_ip" "kubernetes_ip" {
  region = digitalocean_droplet.k8s.region
  droplet_id = digitalocean_droplet.k8s.id
}

# Create a domain
resource "digitalocean_domain" "pagepress_domain" {
  name       = "pagepress.com.au"
}

# Assign it to VPS
resource "digitalocean_record" "default_record" {
  domain = digitalocean_domain.pagepress_domain.id
  type   = "A"
  name   = "@"
  value  = digitalocean_reserved_ip.kubernetes_ip.ip_address
  ttl    = var.domain_ttl
}

# add www subdomain
resource "digitalocean_record" "www" {
  domain = digitalocean_domain.pagepress_domain.id
  type   = "A"
  name   = "www"
  value  = digitalocean_reserved_ip.kubernetes_ip.ip_address
  ttl    = var.domain_ttl
}

# Print json output with ip address of VPS(s)
output "node_details" {
  description = "Details of the VPS in JSON list format"
  value = jsonencode([
    {
      name       = digitalocean_droplet.k8s.name
      ip_address = digitalocean_droplet.k8s.ipv4_address
    }
  ])
}