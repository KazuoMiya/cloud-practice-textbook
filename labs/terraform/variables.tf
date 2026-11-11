variable "project" {
  description = "資源の名前とタグに使う、システムの名前"
  type        = string
  default     = "cloudbook"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,14}$", var.project))
    error_message = "project は、英小文字で始まる2〜15文字（英小文字、数字、ハイフン）にしてください。"
  }
}

variable "env" {
  description = "環境の名前。同じコードから別の環境を作るときに変える"
  type        = string
  default     = "lab"

  validation {
    condition     = contains(["lab", "dev", "stg", "prod"], var.env)
    error_message = "env は lab、dev、stg、prod のいずれかにしてください。"
  }
}

variable "region" {
  description = "作成先のリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "allowed_http_cidr" {
  description = "ALBへのHTTPを許可する送信元。自分のIPアドレスだけに絞るときは 203.0.113.10/32 の形で指定する"
  type        = string
  default     = "0.0.0.0/0"

  validation {
    condition     = can(cidrhost(var.allowed_http_cidr, 0))
    error_message = "allowed_http_cidr は、203.0.113.10/32 のようなCIDRの形で指定してください。"
  }
}

variable "instance_type" {
  description = "アプリサーバーのインスタンスタイプ"
  type        = string
  default     = "t3.micro"
}

variable "app_min_size" {
  description = "アプリサーバーの最小台数。2つのAZに置くため、2以上にする"
  type        = number
  default     = 2

  validation {
    condition     = var.app_min_size >= 2
    error_message = "app_min_size は2以上にしてください。1台では、AZの障害に耐えられません。"
  }
}

variable "app_max_size" {
  description = "アプリサーバーの最大台数"
  type        = number
  default     = 4
}

variable "db_instance_class" {
  description = "データベースのインスタンスクラス"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_engine_version" {
  description = "PostgreSQLのメジャーバージョン"
  type        = string
  default     = "17"
}

variable "db_multi_az" {
  description = "マルチAZ構成にするか。料金がほぼ倍になるため、切り替えを試すときだけ true にする"
  type        = bool
  default     = false
}
