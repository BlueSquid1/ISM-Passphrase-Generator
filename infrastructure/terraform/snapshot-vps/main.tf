# Use the DigitalOcean terraform provider.
terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
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
data "digitalocean_droplet" "k8s" {
  name = "k8s"
}

# create a snapshot
resource "digitalocean_droplet_snapshot" "k8s_snapshot" {
  droplet_id = data.digitalocean_droplet.k8s.id
  name       = "k8s_snapshot"
}