output "alb_url" {
  description = "ブラウザや curl で開くURL"
  value       = "http://${aws_lb.main.dns_name}"
}

output "vpc_id" {
  description = "VPCのID"
  value       = aws_vpc.main.id
}

output "app_asg_name" {
  description = "アプリサーバーのAuto Scalingグループの名前"
  value       = aws_autoscaling_group.app.name
}

output "target_group_arn" {
  description = "ターゲットグループのARN。ターゲットの状態を調べるときに使う"
  value       = aws_lb_target_group.app.arn
}

output "db_endpoint" {
  description = "データベースのエンドポイント（DNS名）"
  value       = aws_db_instance.main.address
}

output "db_secret_arn" {
  description = "データベースの接続情報を保管しているシークレットのARN。値そのものは出力しない"
  value       = aws_db_instance.main.master_user_secret[0].secret_arn
}
