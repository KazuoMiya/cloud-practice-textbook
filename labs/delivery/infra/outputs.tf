output "url" {
  description = "アプリのURL（ALB）"
  value       = "http://${aws_lb.main.dns_name}/"
}

output "ecr_repository" {
  description = "イメージを登録するリポジトリの名前（deploy.sh の ECR_REPOSITORY）"
  value       = aws_ecr_repository.app.name
}

output "ecs_cluster" {
  description = "クラスターの名前（deploy.sh の ECS_CLUSTER）"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service" {
  description = "サービスの名前（deploy.sh の ECS_SERVICE）。image_tag を指定するまでは作らない"
  value       = local.run_service ? aws_ecs_service.app[0].name : null
}

output "deploy_role_arn" {
  description = "GitHub Actions が引き受けるロール。GitHubの変数 AWS_DEPLOY_ROLE_ARN に設定する"
  value       = aws_iam_role.github_deploy.arn
}
