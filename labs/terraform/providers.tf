locals {
  # 資源の名前の先頭に付ける。例：cloudbook-lab
  name = "${var.project}-${var.env}"

  # すべての資源に付けるタグ。費用の内訳と、消し忘れの確認に使う
  tags = {
    Project   = var.project
    Env       = var.env
    ManagedBy = "terraform"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}
