# Secrets Manager for Jira credentials
resource "aws_secretsmanager_secret" "jira_secrets" {
  name                    = "jira-automation-secrets"
  description             = "Jira API credentials"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "jira_secrets" {
  secret_id = aws_secretsmanager_secret.jira_secrets.id
  secret_string = jsonencode({
    JIRA_BASE      = var.jira_base
    JIRA_LOGIN     = var.jira_login
    JIRA_API_TOKEN = var.jira_api_token
    ACCOUNT_ID     = var.account_id
  })
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "jira-automation-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "jira-automation-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.jira_secrets.arn
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/jira-automation"
  retention_in_days = 14
}

# Lambda Function
resource "aws_lambda_function" "jira_automation" {
  filename         = "../lambda_function.zip"
  function_name    = "jira-automation"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  source_code_hash = filebase64sha256("../lambda_function.zip")
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 512

  # No environment variables needed - AWS_REGION is automatic

  tags = {
    Environment = var.environment
    Project     = "jira-automation"
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
    aws_iam_role_policy.lambda_policy
  ]
}

# EventBridge Rule for Scheduling
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "jira-automation-schedule"
  description         = "Trigger Jira automation"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.jira_automation.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.jira_automation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}
