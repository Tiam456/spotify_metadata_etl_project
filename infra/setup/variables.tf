variable "project" {
  description = "project name"
  default     = "spotify-metadata-etl-project"
}

variable "aws_region" {
  description = "region"
  type        = string
  default     = "eu-west-2"
}

variable "state_bucket_name" {
  description = "S3 bucket for Terraform state"
  default     = "spotify-metadata-etl-project-terraform-state"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table for state locking"
  default     = "spotify-metadata-etl-project-terraform-state-lock"
  type        = string
}
