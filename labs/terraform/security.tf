# セキュリティグループは、通信の向きに沿って3つ作る。利用者 → ALB → アプリ → DB
# 説明（description）には、英数字と一部の記号しか使えない

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb"
  description = "ALB: HTTP from allowed clients"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name}-alb"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from allowed clients"
  cidr_ipv4         = var.allowed_http_cidr
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "alb_to_app" {
  security_group_id            = aws_security_group.alb.id
  description                  = "HTTP to app servers"
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}

resource "aws_security_group" "app" {
  name        = "${local.name}-app"
  description = "App: HTTP from ALB only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name}-app"
  }
}

# 送信元は、IPアドレスではなくALBのセキュリティグループで指定する。22番（SSH）は開けない
resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id            = aws_security_group.app.id
  description                  = "HTTP from ALB"
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}

# ソフトウェアの取得、Systems Manager、データベースへの通信のために、外向きは許可する
resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  description       = "All outbound"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# 外向きのルールは書かない。データベースから通信を始める必要がないため
resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "DB: PostgreSQL from app servers only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name}-db"
  }
}

resource "aws_vpc_security_group_ingress_rule" "db_from_app" {
  security_group_id            = aws_security_group.db.id
  description                  = "PostgreSQL from app servers"
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}
