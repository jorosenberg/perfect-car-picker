variable "aws_region" {
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  default     = "perfect-car-picker"
}

variable "db_name" {
    type        = string
}

variable "db_username" {
  type        = string
}

variable "db_password" {
  type        = string
  sensitive   = true
}

variable "github_repo_url" {
  type        = string
}

# network
variable "vpc_cidr" {
  type        = string
}

variable "public_subnet_cidr" {
  type        = string
}

variable "public_subnet_2_cidr" {
  type        = string
  default     = "10.0.4.0/24"
}

variable "private_subnet_1_cidr" {
  type        = string
}

variable "private_subnet_2_cidr" {
  type        = string
}

# remember to use github var since i make this public repo
variable "app_port" {
  description = "streamlit port"
  type        = number
}

variable "ssh_port" {
  type        = number
}

variable "db_port" {
  type        = number
}
