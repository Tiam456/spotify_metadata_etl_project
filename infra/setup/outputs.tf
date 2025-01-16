output "cd_user_access_key_id" {
  description = "Access key ID for CD user"
  value       = aws_iam_access_key.cd_user.id
}

output "cd_user_access_key_secret" {
  description = "Access key secret for CD user"
  value       = aws_iam_access_key.cd_user.secret
  sensitive   = true
}

output "ecr_app_repository_url" {
  description = "ECR repository URL for the app"
  value       = aws_ecr_repository.app.repository_url
}
