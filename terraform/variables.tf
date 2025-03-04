variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "allowed_cidrs" {
  description = "CIDR blocks allowed to access services"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "db_name" {
  description = "MySQL database name"
  type        = string
  default     = "crm_db"
}

variable "db_username" {
  description = "MySQL database username"
  type        = string
  default     = "crm_user"
}

variable "db_password" {
  description = "MySQL database password"
  type        = string
  default     = "crm_password"
}

variable "ssm_db_name" {
  description = "SSM parameter name for DB name"
  type        = string
  default     = "/crm/db/name"
}

variable "ssm_db_username" {
  description = "SSM parameter name for DB username"
  type        = string
  default     = "/crm/db/username"
}

variable "ssm_db_password" {
  description = "SSM parameter name for DB password"
  type        = string
  default     = "/crm/db/password"
}

variable "ssm_db_host" {
  description = "SSM parameter name for DB host"
  type        = string
  default     = "/crm/db/host"
}

variable "ssm_db_port" {
  description = "SSM parameter name for DB port"
  type        = string
  default     = "/crm/db/port"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for logs"
  type        = string
  default     = "crm-python-simple-logs"
}

variable "ssm_cognito_user_pool_id" {
  description = "SSM parameter name for Cognito User Pool ID"
  type        = string
  default     = "/crm/cognito/user_pool_id"
}

variable "ssm_cognito_client_id" {
  description = "SSM parameter name for Cognito Client ID"
  type        = string
  default     = "/crm/cognito/client_id"
}

variable "ssm_redis_endpoint" {
  description = "SSM parameter name for the Redis (ElastiCache) endpoint"
  type        = string
  default     = "/crm/redis_endpoint"
}
