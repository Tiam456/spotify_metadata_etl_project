terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "spotify-metadata-etl-project-terraform-state"
    key            = "tf-state-setup"
    region         = "eu-west-2"
    encrypt        = true
    dynamodb_table = "spotify-metadata-etl-project-terraform-state-lock"
  }
}

provider "aws" {
  region = "eu-west-2"
}
