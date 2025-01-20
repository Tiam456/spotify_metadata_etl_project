# create vpc
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}
# create internet gateway for internet access
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

# 2 public subnets - 1 for redundancy
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "eu-west-2a"
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "eu-west-2b"
}

resource "aws_route_table" "public_1" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public_2" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public_1.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public_2.id
}

resource "aws_route" "public_1_internet_access" {
  route_table_id         = aws_route_table.public_1.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route" "public_2_internet_access" {
  route_table_id         = aws_route_table.public_2.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# create nat for private
resource "aws_eip" "nat_1" {
  domain = "vpc"
}

resource "aws_eip" "nat_2" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat_1" {
  allocation_id = aws_eip.nat_1.id
  subnet_id     = aws_subnet.public_1.id # Public Subnet in eu-west-2a
}

resource "aws_nat_gateway" "nat_2" {
  allocation_id = aws_eip.nat_2.id
  subnet_id     = aws_subnet.public_2.id # Public Subnet in eu-west-2b
}

# create private subnets
resource "aws_subnet" "private_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.3.0/24"
  map_public_ip_on_launch = false
  availability_zone       = "eu-west-2a"
}

resource "aws_subnet" "private_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.4.0/24"
  map_public_ip_on_launch = false
  availability_zone       = "eu-west-2b"
}

resource "aws_route_table" "private_1" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "private_2" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private_1.id
}

resource "aws_route" "private_1_nat_access" {
  route_table_id         = aws_route_table.private_1.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_1.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private_2.id
}

resource "aws_route" "private_2_nat_access" {
  route_table_id         = aws_route_table.private_2.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_2.id
}

# vpc endpoints allowing EC2 to access to ecr, cloudwatch, rds, s3 and redshift

resource "aws_security_group" "vpc_endpoints" {
  vpc_id      = aws_vpc.main.id
  name        = "endpoint_access"
  description = "Security group for VPC endpoints (ECR, CloudWatch, SSM, S3)"
  ingress { # inbound access
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
}
# to review later. need more detailed security group rules for rds, redshift etc etc
# this is security group for vpc not ec2

# endpoint for ecr
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id             = aws_vpc.main.id
  service_name       = "com.amazonaws.eu-west-2.ecr.api"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id             = aws_vpc.main.id
  service_name       = "com.amazonaws.eu-west-2.ecr.dkr"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "cloudwatch" {
  vpc_id             = aws_vpc.main.id
  service_name       = "com.amazonaws.eu-west-2.logs"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.eu-west-2.s3"
  vpc_endpoint_type = "Gateway" # this is free
  route_table_ids   = [aws_route_table.private_1.id, aws_route_table.private_2.id]
}

resource "aws_vpc_endpoint" "ssm" { # for ec2
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.eu-west-2.ssm"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}
