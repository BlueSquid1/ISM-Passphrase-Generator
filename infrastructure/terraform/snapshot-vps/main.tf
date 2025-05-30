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

# Personal access token to DigitalOcean
variable "do_token" {
  sensitive = true
  description = "DigitalOcean personal access token"
}

# Configure the DigitalOcean Provider to use my personal access token.
provider "digitalocean" {
  token = var.do_token
}

# get the VPS by name
data "digitalocean_droplet" "web" {
  name = var.vps_name
}

# create a snapshot
resource "digitalocean_droplet_snapshot" "web_preprod_snapshot" {
  droplet_id = data.digitalocean_droplet.web.id
  name       = "${var.vps_name}-snapshot"
}