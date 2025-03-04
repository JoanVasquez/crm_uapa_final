provider "aws" {
  region = var.aws_region
}

# --- VPC & Networking ---
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "free-tier-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "free-tier-igw" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = element(var.availability_zones, count.index)
  map_public_ip_on_launch = true
  tags = { Name = "free-tier-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 2)
  availability_zone = element(var.availability_zones, count.index)
  tags = { Name = "free-tier-private-${count.index}" }
}

# NAT Gateway in first public subnet.
resource "aws_eip" "nat" {
  vpc = true
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  tags = { Name = "free-tier-nat" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "free-tier-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
  tags = { Name = "free-tier-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# --- ECS & ECR ---
resource "aws_ecr_repository" "app_repo" {
  name = "crm-python-simple"
}

resource "aws_ecs_cluster" "main" {
  name = "free-tier-cluster"
}

# --- RDS MySQL ---
resource "aws_db_subnet_group" "main" {
  name       = "free-tier-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags = { Name = "free-tier-db-subnet-group" }
}

resource "aws_db_instance" "mysql" {
  allocated_storage      = 20
  storage_type           = "gp2"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t2.micro"  # Free tier eligible
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  parameter_group_name   = "default.mysql8.0"
  skip_final_snapshot    = true
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}

resource "aws_security_group" "db_sg" {
  name        = "free-tier-db-sg"
  description = "Allow MySQL inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- Elasticache Redis ---
resource "aws_elasticache_subnet_group" "redis" {
  name       = "free-tier-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "free-tier-redis"
  engine               = "redis"
  node_type            = "cache.t2.micro"  # Free tier eligible
  num_cache_nodes      = 1
  parameter_group_name = "default.redis3.2"
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis_sg.id]
}

resource "aws_security_group" "redis_sg" {
  name        = "free-tier-redis-sg"
  description = "Allow Redis inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- S3 Bucket for Logs ---
resource "aws_s3_bucket" "logs" {
  bucket        = var.s3_bucket_name
  acl           = "private"
  force_destroy = true
  tags = { Name = "free-tier-logs-bucket" }
}

# --- KMS Key ---
resource "aws_kms_key" "app_key" {
  description               = "KMS key for encrypting app data"
  deletion_window_in_days   = 10
  tags = { Name = "free-tier-app-key" }
}

# --- AWS Cognito ---
resource "aws_cognito_user_pool" "user_pool" {
  name                          = "free-tier-user-pool"
  auto_verified_attributes      = ["email"]
}

resource "aws_cognito_user_pool_client" "user_pool_client" {
  name         = "free-tier-user-pool-client"
  user_pool_id = aws_cognito_user_pool.user_pool.id
  generate_secret = false
}

# --- SSM Parameters ---
resource "aws_ssm_parameter" "db_name" {
  name  = var.ssm_db_name
  type  = "String"
  value = var.db_name
}

resource "aws_ssm_parameter" "db_username" {
  name  = var.ssm_db_username
  type  = "String"
  value = var.db_username
}

resource "aws_ssm_parameter" "db_password" {
  name  = var.ssm_db_password
  type  = "SecureString"
  value = var.db_password
}

resource "aws_ssm_parameter" "db_host" {
  name  = var.ssm_db_host
  type  = "String"
  value = aws_db_instance.mysql.address
}

resource "aws_ssm_parameter" "db_port" {
  name  = var.ssm_db_port
  type  = "String"
  value = aws_db_instance.mysql.port
}

resource "aws_ssm_parameter" "redis_endpoint" {
  name  = var.ssm_redis_endpoint
  type  = "String"
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}

resource "aws_ssm_parameter" "cognito_user_pool_id" {
  name  = var.ssm_cognito_user_pool_id
  type  = "String"
  value = aws_cognito_user_pool.user_pool.id
}

resource "aws_ssm_parameter" "cognito_client_id" {
  name  = var.ssm_cognito_client_id
  type  = "String"
  value = aws_cognito_user_pool_client.user_pool_client.id
}

# --- CloudWatch Log Group for ECS ---
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/crm_python_simple"
  retention_in_days = 7
}

# --- API Gateway (HTTP API) ---
resource "aws_apigatewayv2_api" "http_api" {
  name          = "free-tier-http-api"
  protocol_type = "HTTP"
}

# (For simplicity, we assume the ECS service’s public load balancer is used by API Gateway.)
resource "aws_apigatewayv2_integration" "ecs_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "HTTP_PROXY"
  integration_uri        = aws_lb.ecs_lb.dns_name
  payload_format_version = "1.0"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.ecs_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

# --- ECS Fargate Service ---
resource "aws_lb" "ecs_lb" {
  name               = "free-tier-ecs-lb"
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.lb_sg.id]
  tags = { Name = "free-tier-ecs-lb" }
}

resource "aws_security_group" "lb_sg" {
  name        = "free-tier-lb-sg"
  description = "Allow HTTP traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb_target_group" "ecs_tg" {
  name     = "free-tier-ecs-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.ecs_lb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = aws_lb_target_group.ecs_tg.arn
    type             = "forward"
  }
}

resource "aws_security_group" "ecs_sg" {
  name        = "free-tier-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.lb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "app_task" {
  family                   = "crm-python-simple-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([
    {
      name      = "app"
      image     = aws_ecr_repository.app_repo.repository_url
      essential = true
      portMappings = [{
        containerPort = 8000
        hostPort      = 8000
        protocol      = "tcp"
      }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "app_service" {
  name            = "crm-python-simple-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  platform_version = "LATEST"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_tg.arn
    container_name   = "app"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
}
