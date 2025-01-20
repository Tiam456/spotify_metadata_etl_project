variable "db_username" {
  default     = "postgres"
  description = "The username for the database."
}

variable "db_password" {
  description = "The password for the database. defined in env"
}
