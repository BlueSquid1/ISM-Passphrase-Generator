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
  description = "Name of the VPS to start pointing to"
}

# Personal access token to DigitalOcean
variable "do_token" {
  sensitive = true
  description = "DigitalOcean personal access token"
}

# domain name time to live in seconds
variable "domain_ttl" {
  default = 120
}

# Configure the DigitalOcean Provider to use my personal access token.
provider "digitalocean" {
  token = var.do_token
}

# get the VPS by name
data "digitalocean_droplet" "web" {
  name = var.vps_name
}

# Create a reserved IP address
resource "digitalocean_reserved_ip" "web_reserved_ip" {
  region = digitalocean_droplet.web.region
  droplet_id = digitalocean_droplet.web.id
}

# Create a domain
resource "digitalocean_domain" "pagepress_domain" {
  name       = "pagepress.com.au"
}

# add www subdomain
resource "digitalocean_record" "www" {
  domain = digitalocean_domain.pagepress_domain.id
  type   = "A"
  name   = "www"
  value  = digitalocean_reserved_ip.web_reserved_ip.ip_address
  ttl    = var.domain_ttl
}