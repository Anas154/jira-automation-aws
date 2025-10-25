variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "jira_base" {
  description = "Jira base URL"
  type        = string
  sensitive   = true
}

variable "jira_login" {
  description = "Jira login email"
  type        = string
  sensitive   = true
}

variable "jira_api_token" {
  description = "Jira API token"
  type        = string
  sensitive   = true
}

variable "account_id" {
  description = "Jira account ID"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge schedule expression"
  type        = string
  default     = "rate(5 minutes)"
}
