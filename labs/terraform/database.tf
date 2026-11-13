# 単一AZで動かす場合でも、サブネットグループには2つ以上のAZのサブネットを入れる
resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db"
  subnet_ids = [aws_subnet.this["db-a"].id, aws_subnet.this["db-c"].id]
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name}-db"
  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "appdb"
  username = "postgres"

  # パスワードは書かない。RDSが生成して、Secrets Manager に保管する
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  multi_az               = var.db_multi_az

  backup_retention_period = 1
  apply_immediately       = true

  # 学習用の設定。本番では、削除保護を有効にし、削除時に最終スナップショットを残す
  deletion_protection = false
  skip_final_snapshot = true
}

# アプリサーバーに、このデータベースの接続情報だけを読む権限を付ける
resource "aws_iam_role_policy" "app_read_db_secret" {
  name = "read-db-secret"
  role = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = aws_db_instance.main.master_user_secret[0].secret_arn
      },
    ]
  })
}
