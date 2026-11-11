# AWSに接続せずに、設計の決まりごとを確かめる。
# 実行：terraform init -backend=false のあと、terraform test

mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"]
    }
  }

  mock_data "aws_ssm_parameter" {
    defaults = {
      value = "ami-0123456789abcdef0"
    }
  }
}

run "address_design" {
  command = plan

  assert {
    condition     = length(aws_subnet.this) == 6
    error_message = "サブネットは、パブリック、アプリ、DBを2つのAZに置き、6つにする"
  }

  assert {
    condition     = aws_subnet.this["app-a"].cidr_block == "10.0.10.0/24" && aws_subnet.this["db-c"].cidr_block == "10.0.21.0/24"
    error_message = "アドレス設計の表と、サブネットのCIDRが合っていない"
  }

  assert {
    condition     = length(aws_route_table.db.route) == 0
    error_message = "DB用のルートテーブルには、外部への経路を書かない"
  }

  assert {
    condition     = length(aws_route_table_association.this) == 6
    error_message = "6つのサブネットすべてを、ルートテーブルに関連付ける"
  }
}

run "traffic_is_narrowed_step_by_step" {
  command = plan

  assert {
    condition     = aws_vpc_security_group_ingress_rule.app_from_alb.from_port == 80 && aws_vpc_security_group_ingress_rule.app_from_alb.to_port == 80
    error_message = "アプリサーバーが受け付けるのは、ALBからの80番だけにする"
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.db_from_app.from_port == 5432 && aws_vpc_security_group_ingress_rule.db_from_app.to_port == 5432
    error_message = "データベースが受け付けるのは、アプリサーバーからの5432番だけにする"
  }

  assert {
    condition     = aws_lb.main.internal == false
    error_message = "ALBは、インターネット向けにする"
  }
}

run "servers_recover_by_themselves" {
  command = plan

  assert {
    condition     = aws_autoscaling_group.app.min_size >= 2
    error_message = "アプリサーバーは、2台以上にする"
  }

  assert {
    condition     = aws_autoscaling_group.app.health_check_type == "ELB"
    error_message = "Auto Scaling で、Elastic Load Balancing のヘルスチェックを有効にする"
  }

  assert {
    condition     = aws_launch_template.app.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 を必須にする"
  }
}

run "database_is_private_and_has_no_password_in_code" {
  command = plan

  assert {
    condition     = aws_db_instance.main.publicly_accessible == false
    error_message = "データベースに、パブリックアクセスを許可しない"
  }

  assert {
    condition     = aws_db_instance.main.manage_master_user_password == true
    error_message = "管理者パスワードは、Secrets Manager に管理させる"
  }

  assert {
    condition     = aws_db_instance.main.storage_encrypted == true
    error_message = "データベースの保存領域を暗号化する"
  }
}

run "rejects_unknown_environment_name" {
  command = plan

  variables {
    env = "production"
  }

  expect_failures = [var.env]
}

run "rejects_single_server" {
  command = plan

  variables {
    app_min_size = 1
  }

  expect_failures = [var.app_min_size]
}
