output "vpc_id" {
  description = "The VPC ID"
  value       = aws_vpc.main.id
}

output "ecs_cluster_id" {
  description = "ECS Cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "ecs_service_name" {
  description = "ECS Service Name"
  value       = aws_ecs_service.app_service.name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app_repo.repository_url
}

output "db_endpoint" {
  description = "MySQL DB endpoint"
  value       = aws_db_instance.mysql.address
}

output "api_gateway_url" {
  description = "API Gateway URL"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}
