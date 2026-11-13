# 実機確認の手順書

参考実装（このフォルダーのTerraformのコード）を、実際のAWSアカウントに作り、本文の説明どおりに動くことを確かめる手順です。CIは、文法と設計の決まりまでしか確かめていません。次のときに、人がこの手順を1回通します。

- 参考実装を初めて公開する前
- 参考実装、Terraform、AWSプロバイダーの版を変えたとき

所要時間は、1時間半から2時間です。作る資源（NATゲートウェイ、ALB、サーバー2台、データベース）には時間料金がかかります。2時間で片付けまで終えれば、費用の目安は1ドル未満です。途中で中断するときも、必ず「8. 片付け」まで行ってください。

## この手順書の使い方

- 上から順に実行する。飛ばさない
- 各手順の「期待する結果」と、実際の結果を見比べる
- 違っていたら、そこで止まる。自分で直そうとしない。画面の出力をそのまま保存し、「8. 片付け」を行ってから報告する。違いを見つけることが、この作業の目的である
- 最後に、「9. 報告のひな形」を埋めて、依頼した人に渡す

## 1. 準備するもの

| 用意するもの | 確かめ方 |
|---|---|
| 学習用のAWSアカウント。本番の資源や、ほかの人の資源があるアカウントでは行わない | 依頼した人に、使ってよいアカウントを確認する |
| そのアカウントで、資源を作成・削除できる権限 | 第12章の方法でログインできる |
| Git | `git --version` |
| AWS CLI 2.32.0 以降 | `aws --version` |
| Terraform 1.11 以降（検証した版は 1.17.2） | `terraform version` |
| curl | `curl --version` |

## 2. ログインして、対象のアカウントを確かめる

本文の第12章「手元の端末は一時的な認証情報で操作する」の方法でログインします。

```bash
export AWS_PROFILE=cloudbook-lab
export AWS_REGION=ap-northeast-1
aws sts get-caller-identity
```

期待する結果：`Account` が、学習用のアカウントの番号である。`Arn` の末尾が `:root` ではない。

違うアカウントが表示されたら、ここで止まります。

## 3. コードを取得する

```bash
git clone https://github.com/KazuoMiya/cloud-practice-textbook.git
cd cloud-practice-textbook
git checkout feat/terraform-lab   # PR #6 がマージされた後は、この行は要らない
cd labs/terraform
```

## 4. AWSに接続しない確認

```bash
terraform init
terraform fmt -check -recursive
terraform validate
terraform test
```

期待する結果：

- `terraform init`：`Terraform has been successfully initialized!`
- `terraform fmt`：何も表示されない
- `terraform validate`：`Success! The configuration is valid.`
- `terraform test`：`Success! 6 passed, 0 failed.`

`terraform init` で `No valid credential sources found` とは表示されません（まだAWSに接続しないため）。次の手順でこのエラーが出たら、本文の第18章「Terraformが認証情報を見つけられないとき」の設定を行います。

## 5. 作られるものを確かめる（plan）

```bash
terraform plan
```

期待する結果：最後の行が `Plan: 38 to add, 0 to change, 0 to destroy.` である。

数が違う場合は、止まって、出力を保存します。

## 6. 作る（apply）

```bash
time terraform apply
```

確認を求められたら、`yes` と入力します。データベースの作成に時間がかかるため、全体で10分から20分かかります。

期待する結果：`Apply complete! Resources: 38 added, 0 changed, 0 destroyed.` と表示され、続けて `Outputs:` に6つの値（`alb_url`、`app_asg_name`、`db_endpoint`、`db_secret_arn`、`target_group_arn`、`vpc_id`）が表示される。

かかった時間（`real` の値）を記録します。エラーで止まった場合は、エラーの全文を保存し、「8. 片付け」へ進みます。

## 7. 動作を確かめる

### 7-1. コードと実際の構成が一致している

```bash
terraform plan
```

期待する結果：`No changes. Your infrastructure matches the configuration.`

### 7-2. ALBから、2台のサーバーに振り分けられる

サーバーが起動して正常と判定されるまで、`apply` の後、3分から5分待ちます。

```bash
for i in $(seq 10); do curl -s "$(terraform output -raw alb_url)"; echo; done
aws elbv2 describe-target-health --target-group-arn "$(terraform output -raw target_group_arn)" \
  --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State]' --output table
```

期待する結果：`<h1>ip-10-0-10-…</h1>` と `<h1>ip-10-0-11-…</h1>` のように、2種類のホスト名が表示される。ターゲットが2つあり、どちらも `healthy` である。

### 7-3. SSHを使わずに、サーバーへ入れる

```bash
aws ssm describe-instance-information \
  --query 'InstanceInformationList[].[InstanceId,PingStatus]' --output table
```

期待する結果：サーバーが2台表示され、どちらも `Online` である。

### 7-4. データベースが、非公開で、暗号化されている

```bash
aws rds describe-db-instances --db-instance-identifier cloudbook-lab-db \
  --query 'DBInstances[].[DBInstanceStatus,PubliclyAccessible,StorageEncrypted,MasterUserSecret.SecretStatus,EngineVersion]' --output table
```

期待する結果：順に `available`、`False`、`True`、`active`、`17.` で始まる版。

### 7-5. アプリサーバーから、データベースに接続できる

手元の端末で、接続に使う値を表示します。

```bash
terraform output -raw db_endpoint; echo
terraform output -raw db_secret_arn; echo
```

管理画面で、Systems Manager の「セッションマネージャー」を開き、表示されたサーバーの1台でセッションを始めます。サーバーの中で、次を実行します。`<db_secret_arn>` と `<db_endpoint>` は、上で表示した値に置き換えます。

```bash
sudo dnf install -y postgresql17 || sudo dnf install -y postgresql16
aws secretsmanager get-secret-value --secret-id <db_secret_arn> --region ap-northeast-1 \
  --query SecretString --output text
psql "host=<db_endpoint> dbname=appdb user=postgres sslmode=require"
```

`psql` がパスワードを聞くので、2つ目のコマンドで表示された `password` の値を貼り付けます。接続できたら、`select version();` を実行し、`\q` で抜けます。

期待する結果：`PostgreSQL 17.` で始まる行が表示される。

表示したパスワードは、報告にも、どこにも書き写しません。

### 7-6. 手動の変更が、本文の説明どおりに見える

本文の第18章「わざと壊してみる」の内容です。手元の端末で、3つの変更を手で加えます。

```bash
SG_APP=$(aws ec2 describe-security-groups --filters Name=group-name,Values=cloudbook-lab-app \
  --query 'SecurityGroups[0].GroupId' --output text)
RT_DB=$(aws ec2 describe-route-tables --filters Name=tag:Name,Values=cloudbook-lab-db \
  --query 'RouteTables[0].RouteTableId' --output text)
IGW=$(aws ec2 describe-internet-gateways --filters Name=tag:Name,Values=cloudbook-lab-igw \
  --query 'InternetGateways[0].InternetGatewayId' --output text)

# 変更1：アプリ用のセキュリティグループに、受信ルールを足す
aws ec2 authorize-security-group-ingress --group-id "$SG_APP" \
  --ip-permissions 'IpProtocol=tcp,FromPort=8080,ToPort=8080,IpRanges=[{CidrIp=203.0.113.10/32}]'
terraform plan

# 変更2：DB用のルートテーブルに、経路を足す
aws ec2 create-route --route-table-id "$RT_DB" --destination-cidr-block 0.0.0.0/0 --gateway-id "$IGW"
terraform plan

# 変更3：VPCの Name タグを書き換える
aws ec2 create-tags --resources "$(terraform output -raw vpc_id)" --tags Key=Name,Value=changed-by-hand
terraform plan
```

期待する結果：

| 変更 | `terraform plan` の表示 |
|---|---|
| 1の後 | `No changes.`（手で足したルールは、差分に出ない） |
| 2の後 | `aws_route_table.db` が `~`（そのまま変更）で表示され、足した経路を消す差分になる。最後の行は `Plan: 0 to add, 1 to change, 0 to destroy.` |
| 3の後 | `aws_route_table.db` に加えて、`aws_vpc.main` も `~` で表示される。最後の行は `Plan: 0 to add, 2 to change, 0 to destroy.` |

ここは、本文の説明を確かめるための、いちばん大事な確認です。表と違う表示になったら、その表示をそのまま保存してください。

次に、コードを変えずに適用し、手で足したルールを消します。

```bash
terraform apply
aws ec2 describe-route-tables --route-table-ids "$RT_DB" --query 'RouteTables[0].Routes[].DestinationCidrBlock'
aws ec2 describe-security-groups --group-ids "$SG_APP" --query 'SecurityGroups[0].IpPermissions[].FromPort'
aws ec2 revoke-security-group-ingress --group-id "$SG_APP" \
  --ip-permissions 'IpProtocol=tcp,FromPort=8080,ToPort=8080,IpRanges=[{CidrIp=203.0.113.10/32}]'
```

期待する結果：`apply` の後、ルートテーブルの経路は `10.0.0.0/16` だけに戻る。セキュリティグループには `80` と `8080` の両方が残っている（手で足したルールは、Terraformでは消えない）。最後のコマンドで、`8080` のルールを手で消す。

### 7-7. 1台が壊れても、自動で元に戻る

```bash
ASG=$(terraform output -raw app_asg_name)
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG" \
  --query 'AutoScalingGroups[0].Instances[].[InstanceId,AvailabilityZone,LifecycleState,HealthStatus]' --output table
```

表示されたサーバーのIDを1つ選び、終了させます。`<instance-id>` を置き換えます。

```bash
date
aws ec2 terminate-instances --instance-ids <instance-id>
```

数分おきに、7-2のコマンド（ターゲットの状態）を実行します。

期待する結果：新しいサーバーが起動し、ターゲットが再び2つとも `healthy` になる。終了させた時刻と、2つとも `healthy` に戻った時刻を記録する。

## 8. 片付け

```bash
terraform destroy
terraform state list
aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=cloudbook \
  --query 'ResourceTagMappingList[].ResourceARN'
```

`terraform destroy` で確認を求められたら、`yes` と入力します。10分から15分かかります。

期待する結果：

- `terraform destroy`：`Destroy complete! Resources: 38 destroyed.`
- `terraform state list`：何も表示されない
- 3つ目のコマンド：`[]`。削除した直後は、消した資源がしばらく表示されることがある。10分後にもう一度実行し、まだ残っているものがあれば、そのARNを記録する

`destroy` がエラーで止まった場合は、エラーの全文を保存し、もう一度 `terraform destroy` を実行します。それでも残る資源があれば、依頼した人にすぐ伝えます。費用がかかり続けるためです。

翌日、請求の画面（Billing）で、前日の費用に見慣れない項目がないことを確かめます。

## 9. 報告のひな形

次を埋めて、依頼した人に渡します。公開されている場所（GitHubのPRのコメントなど）に書く場合は、アカウントの番号、IPアドレス、ARN、エンドポイントを書かないでください。

```text
参考実装の実機確認の報告

実施日：
実施した人：
リージョン：
版：Terraform        ／ AWS CLI        ／ AWSプロバイダー（terraform version の表示）

4. 接続しない確認     init［ ］ fmt［ ］ validate［ ］ test［ ］（ 件成功）
5. plan の最後の行    ：
6. apply の最後の行   ：
   かかった時間       ：
7-1 plan が No changes［ ］
7-2 ホスト名が2種類［ ］ ターゲット2つが healthy［ ］
7-3 2台とも Online［ ］
7-4 available / False / True / active / 17.x［ ］
7-5 データベースに接続できた［ ］ 入れたクライアントの版：
7-6 変更1の後の plan ：
    変更2の後の plan ：
    変更3の後の plan ：
    apply の後、経路は元に戻った［ ］ 8080番のルールは残っていた［ ］
7-7 終了させた時刻：        2つとも healthy に戻った時刻：
8. destroy の最後の行 ：
   残った資源         ：

期待する結果と違った点（手順の番号と、画面の出力をそのまま）：

手順書の分かりにくかった箇所、誤り：
```
