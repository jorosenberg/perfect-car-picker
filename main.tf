terraform {
  backend "s3" {
    bucket = "perfect-car-picker-tf-state"
    key = "terraform.tfstate"
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "perfect-car-picker-tf-locks"
  }
}

provider "aws" {
  region = var.aws_region
}