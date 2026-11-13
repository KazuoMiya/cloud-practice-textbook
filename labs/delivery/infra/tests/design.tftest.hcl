# AWSに接続せずに、第19章の設計の決まりごとを確かめる。
# 実行：terraform init -backend=false のあと、terraform test

mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"]
    }
  }

  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "111122223333"
    }
  }

  mock_resource "aws_iam_openid_connect_provider" {
    defaults = {
      arn = "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com"
    }
  }

  mock_resource "aws_ecr_repository" {
    defaults = {
      arn            = "arn:aws:ecr:ap-northeast-1:111122223333:repository/cloudbook-app"
      repository_url = "111122223333.dkr.ecr.ap-northeast-1.amazonaws.com/cloudbook-app"
    }
  }

  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::111122223333:role/mock"
    }
  }
}

variables {
  github_repository = "example-org/example-app"
}

run "no_service_before_the_first_image" {
  command = plan

  assert {
    condition     = length(aws_ecs_service.app) == 0 && length(aws_ecs_task_definition.app) == 0
    error_message = "最初のイメージを登録する前（image_tag が空）は、サービスとタスク定義を作らない"
  }

  assert {
    condition     = aws_ecr_repository.app.image_tag_mutability == "IMMUTABLE" && aws_ecr_repository.app.image_scanning_configuration[0].scan_on_push
    error_message = "ECRは、同じタグでの上書きを禁止し、登録のたびに脆弱性を検査する"
  }
}

run "service_with_the_first_image" {
  command = apply

  variables {
    image_tag = "first"
  }

  assert {
    condition     = length(aws_ecs_service.app) == 1
    error_message = "image_tag を指定したら、サービスを作る"
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.app[0].container_definitions)[0].image == "111122223333.dkr.ecr.ap-northeast-1.amazonaws.com/cloudbook-app:first"
    error_message = "タスク定義のイメージは、ECRのリポジトリと、指定したタグにする"
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.app[0].container_definitions)[0].name == "app" && jsondecode(aws_ecs_task_definition.app[0].container_definitions)[0].readonlyRootFilesystem
    error_message = "コンテナの名前は app（deploy.sh が差し替える対象）にし、ファイルシステムは読み取り専用にする"
  }

  assert {
    condition     = aws_ecs_service.app[0].deployment_circuit_breaker[0].enable && aws_ecs_service.app[0].deployment_circuit_breaker[0].rollback
    error_message = "入れ替えに失敗し続けたら、自動で前の版に戻す"
  }

  assert {
    condition     = aws_ecs_service.app[0].deployment_minimum_healthy_percent == 100
    error_message = "新しい版が健全になるまで、古い版を止めない"
  }

  assert {
    condition     = aws_lb_target_group.app.target_type == "ip" && aws_lb_target_group.app.port == 8080 && aws_lb_target_group.app.health_check[0].path == "/health"
    error_message = "Fargate のタスクはIPで登録し、8080番の /health で健全性を確かめる"
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.app_from_alb.referenced_security_group_id == aws_security_group.alb.id && aws_vpc_security_group_ingress_rule.app_from_alb.from_port == 8080
    error_message = "タスクが受け付けるのは、ALBからの8080番だけにする"
  }

  assert {
    condition     = jsondecode(aws_iam_role.github_deploy.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:sub"] == "repo:example-org/example-app:environment:production"
    error_message = "ロールを引き受けられるのは、指定したリポジトリの production 環境のジョブだけにする"
  }

  assert {
    condition     = jsondecode(aws_iam_role.github_deploy.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:aud"] == "sts.amazonaws.com"
    error_message = "トークンの受け取り手（aud）を sts.amazonaws.com に限る"
  }

  assert {
    condition     = jsondecode(aws_iam_role_policy.github_deploy.policy).Statement[3].Resource == "arn:aws:ecs:ap-northeast-1:111122223333:service/cloudbook/cloudbook-app"
    error_message = "サービスの更新は、この章のサービスだけに限る"
  }

  assert {
    condition     = jsondecode(aws_iam_role_policy.github_deploy.policy).Statement[4].Condition.StringEquals["iam:PassedToService"] == "ecs-tasks.amazonaws.com"
    error_message = "ロールを渡せるのは、ECSのタスクに対してだけにする"
  }
}

run "latest_is_rejected" {
  command = plan

  variables {
    image_tag = "latest"
  }

  expect_failures = [var.image_tag]
}

run "existing_oidc_provider_is_reused" {
  command = plan

  variables {
    create_github_oidc_provider = false
  }

  assert {
    condition     = length(aws_iam_openid_connect_provider.github) == 0
    error_message = "アカウントにOIDCプロバイダーがある場合は、作らずに使う"
  }
}
