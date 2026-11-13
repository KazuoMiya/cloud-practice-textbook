# イメージの置き場。同じタグでの上書きを禁止し、登録のたびに既知の脆弱性を検査する
resource "aws_ecr_repository" "app" {
  name                 = "${local.name}-app"
  image_tag_mutability = "IMMUTABLE"

  # 学習用：terraform destroy で、中のイメージごと消す（本番では false のままにする）
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# 古いイメージを、新しい10個だけ残して消す（戻し先として、少し前の版まで残しておく）
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "keep the latest 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      },
    ]
  })
}
