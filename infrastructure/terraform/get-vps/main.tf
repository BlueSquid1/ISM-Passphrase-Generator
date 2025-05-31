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

# Public IP Address of the VPS to get
variable "ip_address" {
  description = "Public IP Address of the VPS to get"
}

# Personal access token to DigitalOcean
variable "do_token" {
  sensitive = true
  description = "DigitalOcean personal access token"
}

# Configure the DigitalOcean Provider to use my personal access token.
provider "digitalocean" {
  token = var.do_token
}

# Lookup the droplet by public IP and name
data "digitalocean_droplets" "web" {
    filter {
        key    = "ipv4_address"
        values = [var.ip_address]
    }
    filter {
        key    = "name"
        values = [var.vps_name]
    }
}

# Print json output with droplet name and id 
output "node_details" {
  description = "Details of the VPS in JSON list format"
  value = jsonencode([
    for droplet in data.digitalocean_droplets.web.droplets : {
        name = droplet.name
        droplet_id = droplet.id
    }
  ])
}