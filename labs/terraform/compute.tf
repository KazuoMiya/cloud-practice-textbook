# Amazon Linux 2023 の最新のAMIを、AWSが公開しているパラメータから調べる
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# サーバーが使うロール。Session Manager で入るための権限だけを付ける
resource "aws_iam_role" "app" {
  name = "${local.name}-app"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_ssm" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "app" {
  name = "${local.name}-app"
  role = aws_iam_role.app.name
}

resource "aws_launch_template" "app" {
  name_prefix            = "${local.name}-app-"
  image_id               = nonsensitive(data.aws_ssm_parameter.al2023.value)
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.app.id]
  user_data              = filebase64("${path.module}/user_data.sh")
  update_default_version = true

  iam_instance_profile {
    arn = aws_iam_instance_profile.app.arn
  }

  # サーバーの中から認証情報を取り出す経路（IMDS）は、v2だけを許可する
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # default_tags は、Auto Scaling が起動するサーバーには付かない。ここで付ける
  tag_specifications {
    resource_type = "instance"

    tags = merge(local.tags, {
      Name = "${local.name}-app"
    })
  }
}

resource "aws_lb" "main" {
  name                       = "${local.name}-alb"
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.alb.id]
  subnets                    = [aws_subnet.this["public-a"].id, aws_subnet.this["public-c"].id]
  drop_invalid_header_fields = true

  # インターネット向けのALBは、インターネットゲートウェイのないVPCには作れない
  depends_on = [aws_internet_gateway.main]
}

resource "aws_lb_target_group" "app" {
  name                 = "${local.name}-app"
  vpc_id               = aws_vpc.main.id
  protocol             = "HTTP"
  port                 = 80
  deregistration_delay = 30

  health_check {
    path                = "/"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

# 学習用にHTTPで受ける。本番では、証明書を付けてHTTPSで受ける
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  protocol          = "HTTP"
  port              = 80

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "${local.name}-app"
  min_size            = var.app_min_size
  max_size            = var.app_max_size
  vpc_zone_identifier = [aws_subnet.this["app-a"].id, aws_subnet.this["app-c"].id]
  target_group_arns   = [aws_lb_target_group.app.arn]

  # ALBが異常と判断したサーバーを入れ替える。猶予期間は、起動にかかる時間より長くする
  health_check_type         = "ELB"
  health_check_grace_period = 120

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  # 起動テンプレートを変えたら、サーバーを半分ずつ入れ替える
  instance_refresh {
    strategy = "Rolling"

    preferences {
      min_healthy_percentage = 50
    }
  }

  # サーバーは起動時に外へ出て、ソフトウェアを取得する。経路ができる前に起動させない
  depends_on = [aws_route_table_association.this]
}
