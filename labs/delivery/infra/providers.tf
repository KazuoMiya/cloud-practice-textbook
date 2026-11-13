locals {
  name = var.project

  # すべての資源に付けるタグ。費用の内訳と、消し忘れの確認に使う
  tags = {
    Project   = var.project
    Chapter   = "19"
    ManagedBy = "terraform"
  }

  # 最初のイメージを登録するまでは、サービスを作らない（動かすイメージがないため）
  run_service = var.image_tag != ""
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}
