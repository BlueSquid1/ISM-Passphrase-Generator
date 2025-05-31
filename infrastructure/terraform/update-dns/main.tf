# Use the DigitalOcean terraform provider.
terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
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

# domain name time to live in seconds
variable "domain_ttl" {
  default = 120
}

# Configure the DigitalOcean Provider to use my personal access token.
provider "digitalocean" {
  token = var.do_token
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
  value  = var.ip_address
  ttl    = var.domain_ttl
}