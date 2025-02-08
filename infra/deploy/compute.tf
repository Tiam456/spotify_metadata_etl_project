# Security group for EC2
resource "aws_security_group" "ec2" {
  name        = "ec2-security-group"
  description = "Security group for EC2 instance allowing airflow, ssh"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Airflow webserver
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Consider restricting this to your IP
  }

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Consider restricting this to your IP
  }
}

# Update EC2 Instance
resource "aws_instance" "airflow_server" {
  ami           = "ami-0cbf43fd299e3a464"
  instance_type = "t3.medium"

  subnet_id              = aws_subnet.private_1.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = "Ec2tutorial"

  user_data = file("${path.module}/bootstrap_airflow.sh")

  tags = {
    Name = "airflow-server"
  }
}
