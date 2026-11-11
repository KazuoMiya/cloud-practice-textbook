# 第18章の参考実装（Terraform）

「クラウド実践テキスト」第18章（ステップ7：IaC）の完成形です。第13〜15章で手で作った構成（VPC、ALB、Auto Scaling、RDS）を、Terraformで定義しています。本文に載せたコードは、すべてここからの抜粋です。

先に自分で書き、動かしてから、答え合わせとして読み、自分のコードと見比べてください。

## 作られるもの

| ファイル | 資源 |
|---|---|
| `network.tf` | VPC（10.0.0.0/16）、サブネット6つ、インターネットゲートウェイ、NATゲートウェイ1つ、ルートテーブル3つ |
| `security.tf` | セキュリティグループ3つ（ALB、アプリ、DB） |
| `compute.tf` | サーバー用のロール、起動テンプレート、ALB、ターゲットグループ、Auto Scalingグループ（2台） |
| `database.tf` | RDS for PostgreSQL（単一AZ）。パスワードは Secrets Manager が管理する |

NATゲートウェイ、ALB、サーバー、データベースは、置いてあるだけで時間料金がかかります。その日のうちに `terraform destroy` で消してください。

## 動かして確かめる（保守する人向け）

このリポジトリを保守する人が、参考実装の動作を確かめるときの手順です。確認する項目と期待する結果は、[VERIFY.md](VERIFY.md) にまとめてあります。第12章の方法で、学習用のアカウントの一時的な認証情報を用意してから実行します。

```bash
export AWS_PROFILE=cloudbook-lab
aws sts get-caller-identity   # 学習用のアカウントであることを確かめる

terraform init
terraform plan
terraform apply
curl -s "$(terraform output -raw alb_url)"

terraform destroy
```

値を変えるときは、`terraform.tfvars.example` を `terraform.tfvars` という名前で複製して書き換えます。

## 検査していること、していないこと

このリポジトリのCI（`.github/workflows/labs.yml`）は、変更のたびに次を実行します。

| 検査 | 内容 |
|---|---|
| `terraform fmt -check` | 書式 |
| `terraform validate` | 文法と、項目の名前や型（プロバイダーの定義との照合） |
| `terraform test` | `tests/design.tftest.hcl` の設計の決まり。AWSには接続しない |

CIは、実際のAWSアカウントに資源を作りません。`apply` が最後まで通ること、作られた資源が本文の説明どおりに動くことは、[VERIFY.md](VERIFY.md) の手順で、人が確かめます。Terraformやプロバイダーの版を上げたときも、同じ確認をしてください。

検証した版は、Terraform 1.17.2、AWSプロバイダー 6.72.0（`.terraform.lock.hcl` に記録）です。

## 利用の条件

リポジトリの `LICENSE.md` に従います。複製や改変についての許諾は、現在定めていません。
