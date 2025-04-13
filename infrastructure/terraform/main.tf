# Use the terraform provider.
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

# Configure the DigitalOcean Provider to use my personal access token.
variable "do_token" {
  sensitive = true
  description = "DigitalOcean personal access token"
}

variable "ssh_registered_key_name" {
  default = "terraform"
}

variable "ansible_main_script" {
  default = "../ansible/main.yml"
}

provider "digitalocean" {
  token = var.do_token
}

# Tell DigitalOcean provider to allow SSH connections with the "terraform" public key
data "digitalocean_ssh_key" "terraform" {
  name = var.ssh_registered_key_name
}

# Create the VPS
resource "digitalocean_droplet" "kubernetes-cluster" {
  name = "kubernetes-cluster"
  image = "ubuntu-24-04-x64"
  region = "syd1"
  size = "s-1vcpu-2gb"
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

  # Runs ansible playbook
  provisioner "local-exec" {
    # because computer hasn't connected to the VPS before need to disable key checking to prevent an interactive session
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook --user root --inventory '${self.ipv4_address},' --private-key ${var.pvt_key} ${var.ansible_main_script}"
  }
}