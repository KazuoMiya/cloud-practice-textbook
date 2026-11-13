variable "region" {
  description = "作るリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "project" {
  description = "資源の名前に使う。ECRのリポジトリ、クラスター、サービスの名前になる"
  type        = string
  default     = "cloudbook"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project))
    error_message = "英小文字で始まる、3〜21文字の英小文字、数字、ハイフンにする"
  }
}

variable "github_repository" {
  description = "デプロイを許すGitHubのリポジトリ。組織名（またはユーザー名）/リポジトリ名"
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$", var.github_repository))
    error_message = "OWNER/REPOSITORY の形で指定する"
  }
}

variable "create_github_oidc_provider" {
  description = "GitHubのOIDCプロバイダーを作るか。アカウントにすでにある場合は false にする（1つのアカウントに1つだけ作れる）"
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "最初に動かすイメージのタグ。空のうちはサービスを作らない。2回目以降の入れ替えは、GitHub Actions が行う"
  type        = string
  default     = ""

  validation {
    condition     = var.image_tag != "latest"
    error_message = "latest は使わない。コミットIDなど、版ごとに違うタグにする"
  }
}
