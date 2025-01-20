resource "aws_db_subnet_group" "main" {
  name       = "db-main"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_security_group" "rds" {
  description = "Allow access to the RDS database instance."
  name        = "rds-inbound-access"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol  = "tcp"
    from_port = 5432
    to_port   = 5432
  }
}


resource "aws_db_instance" "main" {
  identifier                 = "db-main"
  engine                     = "postgres"
  engine_version             = "17.2"
  instance_class             = "db.t4g.micro"
  allocated_storage          = 5
  storage_encrypted          = true
  username                   = var.db_username
  password                   = var.db_password
  db_subnet_group_name       = aws_db_subnet_group.main.name
  vpc_security_group_ids     = [aws_security_group.rds.id]
  multi_az                   = false
  backup_retention_period    = 0
  auto_minor_version_upgrade = true
  deletion_protection        = false
  skip_final_snapshot        = true
}
