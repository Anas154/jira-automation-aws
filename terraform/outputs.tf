output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.jira_automation.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.jira_automation.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "secret_arn" {
  description = "Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.jira_secrets.arn
}
