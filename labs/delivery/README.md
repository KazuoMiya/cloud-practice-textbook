# 第19章の参考実装：アプリを自動で届ける

「クラウド実践テキスト」第19章（ステップ8：コンテナとCI/CD）の完成形です。本文の Dockerfile とワークフローは、ここにあるファイルをそのまま載せています。

| 置き場所 | 中身 |
|---|---|
| `app/` | 題材のアプリ（画面と `/health` を返すだけ）、そのテスト、Dockerfile、Makefile |
| `deploy.sh` | イメージを作ってECRに登録し、タスク定義の新しい版を登録して、サービスを入れ替える |
| `render-taskdef.jq` | 今のタスク定義から、イメージだけを差し替えた新しい版を作る |
| `rollback.sh` | サービスを、指定した版のタスク定義に戻す |
| `workflow/app-delivery.yml` | GitHub Actions のワークフロー。自分のリポジトリの `.github/workflows/` に置く |
| `infra/` | AWS側の資源（VPC、ALB、ECR、ECS、GitHub Actions 用のロール）を作るTerraform |

このリポジトリのCIでは、毎回次のことを確かめています。AWSのアカウントは使いません。

- アプリのテストが通る
- イメージが作れて、管理者以外のユーザー（UID 1000）で動き、中身がアプリのファイルだけである
- ファイルシステムを読み取り専用にしても動き、`/health` と画面が正しく返る
- `deploy.sh` と `rollback.sh` を、偽の `aws` と `docker` で通しで動かし、正しい順番と引数で呼ぶ。ECSが自動で前の版に戻したときは、失敗として止まる
- タスク定義の項目のうち、登録のときに指定できないものだけを、`render-taskdef.jq` が取り除いている（AWS CLI が持つAPIの定義と照合）
- Terraform の書式、文法、設計の決まりごと（AWSに接続しないテスト）

実際のアカウントでの確認：未実施（2026年11月13日時点）。実行して気づいた点は、Issue で知らせてください。

## 無料で進める部分

AWSを使わずに、ここまでは費用をかけずに進められます。

```bash
cd labs/delivery/app
make test                 # テスト
make run                  # http://localhost:8080/ で動かす（読み取り専用で起動する）
```

GitHub に自分のリポジトリを作り、`app/` とワークフローを置けば、PRのたびにテストが動くところまでも無料です（公開リポジトリの GitHub Actions は無料。非公開でも、毎月の無料枠の範囲で足ります）。テストが失敗するPRが、マージできないことも確かめられます。デプロイのジョブは、main に入ったときだけ動くため、AWS側を作るまでは、ワークフローの `deploy` を消しておくか、失敗するのを確かめるだけにします。

## AWSで動かす（費用がかかる。任意）

ALB、Fargate のタスク、パブリックIPv4アドレス（ALBとタスクに付く）は、置いてあるだけで時間料金がかかります。その日のうちに、最後の「片付け」まで行ってください。

前提：Terraform 1.11 以上、AWS CLI v2、Docker、jq。第12章の方法で、学習用のアカウントの一時的な認証情報を用意してから実行します。

```bash
export AWS_PROFILE=cloudbook-lab
aws sts get-caller-identity   # 学習用のアカウントであることを確かめる
```

### 1. 自分のリポジトリを用意する

`labs/delivery` の中身を、新しいリポジトリの直下に置き、ワークフローを決まった場所に移します。

```bash
mkdir my-app && cd my-app && git init
cp -r ../cloud-practice-textbook/labs/delivery/. .
mkdir -p .github/workflows && mv workflow/app-delivery.yml .github/workflows/ && rmdir workflow
```

GitHub の画面で、次の2つを設定します。

- ブランチ保護（Settings → Rules または Branches）：main への直接の push を禁止し、PRと、ワークフローの `test` の合格を必須にする
- 環境（Settings → Environments）：`production` を作り、承認者（Required reviewers）に自分を入れ、デプロイできるブランチを main だけにする

### 2. AWS側を作る（サービスはまだ作らない）

```bash
cd infra
terraform init
terraform apply -var 'github_repository=自分の組織名/リポジトリ名'
```

アカウントに、GitHub の OIDC プロバイダーがすでにある場合は、`-var create_github_oidc_provider=false` を加えます（1つのアカウントに1つだけ作れるため）。

最初は、動かすイメージがまだないため、サービスとタスク定義は作りません。ECR、クラスター、ALB、ロールまでを作ります。

### 3. 最初のイメージを登録し、サービスを作る

```bash
cd ..
export AWS_REGION=ap-northeast-1 ECR_REPOSITORY=cloudbook-app IMAGE_TAG=first
bash deploy.sh --push-only
cd infra
terraform apply -var 'github_repository=自分の組織名/リポジトリ名' -var image_tag=first
curl -s "$(terraform output -raw url)"
```

タスクが起動してALBのヘルスチェックに合格するまで、1〜2分かかります。画面に「版：first」と出れば成功です。

### 4. GitHub Actions から届ける

`terraform output -raw deploy_role_arn` の値を、GitHub のリポジトリの変数（Settings → Secrets and variables → Actions → Variables）に `AWS_DEPLOY_ROLE_ARN` という名前で登録します。秘密情報ではないため、Secrets ではなく Variables に置きます。

`app/app.py` の `MESSAGE` を変え、PRを作ります。`test` が通ったらマージし、`production` 環境の承認をすると、`deploy` のジョブが動きます。画面の文言と、「版：」のコミットIDが変われば成功です。

### 5. 戻す

`deploy.sh` は、最後に戻し方を表示します。前の版のタスク定義を指定して戻します。

```bash
export ECS_CLUSTER=cloudbook ECS_SERVICE=cloudbook-app
aws ecs list-task-definitions --family-prefix cloudbook-app --sort DESC --max-items 3
bash rollback.sh cloudbook-app:1
```

戻した後に、main に新しい変更を入れると、また新しい版が届きます。戻した理由を直す変更を、PRで入れます。

### 6. 片付け

```bash
cd infra
terraform destroy -var 'github_repository=自分の組織名/リポジトリ名' -var image_tag=first
for arn in $(aws ecs list-task-definitions --family-prefix cloudbook-app --query 'taskDefinitionArns[]' --output text); do
  aws ecs deregister-task-definition --task-definition "$arn" --query 'taskDefinition.status' --output text
done
```

ECRのリポジトリは、中のイメージごと消えます（学習用に `force_delete` を有効にしています）。GitHub Actions が登録したタスク定義の版は、Terraform の管理外のため、上のコマンドで登録を解除します（料金はかかりませんが、一覧に残ります）。GitHub の変数 `AWS_DEPLOY_ROLE_ARN` も消しておきます。
