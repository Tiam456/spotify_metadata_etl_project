before starting to write all the configuration files via tf, we need to create the terraform state bucket and dynamodb table for state storage and state locking.
Managing the infrastructure using terraform.
the setup folder is used to create the resources which only needs to be created once and rarely changed.
the deploy folder is used to define main application infrastructure that changes more frequently.
a seperate docker compose is used to seperate the container config to make sure code is more organised
