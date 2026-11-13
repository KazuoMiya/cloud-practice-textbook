#!/usr/bin/env bash
# 参考実装（labs/terraform）で作った構成に、障害を1つ入れる。
# 本文の第35章「実機で再現して調べる」で使う。
#
# 使い方：labs/terraform で terraform apply を済ませ、同じフォルダーで実行する。
#   ../faults/inject.sh list      入れられる障害の名前を表示する
#   ../faults/inject.sh random    どれか1つを、名前を伏せて入れる
#   ../faults/inject.sh reveal    random で入れた障害の名前を表示する
#   ../faults/inject.sh <名前>    指定した障害を入れる
#
# 元に戻すには、terraform apply を実行する（web-stopped は、何もしなくても元に戻る）。
# 学習用のアカウント以外では、実行しない。
set -euo pipefail

NAME="${NAME:-cloudbook-lab}"
FAULTS=(no-egress-route app-sg-closed health-path target-group-detached web-stopped)

lookup_sg() {
  aws ec2 describe-security-groups --filters "Name=group-name,Values=$NAME-$1" \
    --query 'SecurityGroups[0].GroupId' --output text
}

inject() {
  local asg tg rt id
  case "$1" in
    no-egress-route)
      asg=$(terraform output -raw app_asg_name)
      rt=$(aws ec2 describe-route-tables --filters "Name=tag:Name,Values=$NAME-app" --query 'RouteTables[0].RouteTableId' --output text)
      aws ec2 delete-route --route-table-id "$rt" --destination-cidr-block 0.0.0.0/0
      # 影響が見えるように、サーバーを1台、入れ替えさせる
      id=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$asg" --query 'AutoScalingGroups[0].Instances[0].InstanceId' --output text)
      aws ec2 terminate-instances --instance-ids "$id" >/dev/null
      ;;
    app-sg-closed)
      aws ec2 revoke-security-group-ingress --group-id "$(lookup_sg app)" --ip-permissions "IpProtocol=tcp,FromPort=80,ToPort=80,UserIdGroupPairs=[{GroupId=$(lookup_sg alb)}]" >/dev/null
      ;;
    health-path)
      tg=$(terraform output -raw target_group_arn)
      aws elbv2 modify-target-group --target-group-arn "$tg" --health-check-path /healthz >/dev/null
      ;;
    target-group-detached)
      asg=$(terraform output -raw app_asg_name)
      tg=$(terraform output -raw target_group_arn)
      aws autoscaling detach-load-balancer-target-groups --auto-scaling-group-name "$asg" --target-group-arns "$tg"
      ;;
    web-stopped)
      aws ssm send-command --document-name AWS-RunShellScript --targets "Key=tag:Name,Values=$NAME-app" --parameters 'commands=["systemctl stop nginx"]' >/dev/null
      ;;
    *)
      echo "知らない名前です：$1（list で一覧を表示できます）" >&2
      exit 2
      ;;
  esac
}

symptom() {
  case "$1" in
    no-egress-route) echo "運用の担当者から：「サーバーの1台に、Session Manager で入れません。ALBのURLを何度開いても、同じホスト名しか表示されません」（10分ほど待ってから調べ始める）" ;;
    app-sg-closed) echo "利用者から：「ページが開きません。しばらく待たされてから、エラーになります」（2分ほど待ってから調べ始める）" ;;
    health-path) echo "運用の担当者から：「利用者からの連絡はありません。ただ、サーバーの一覧を見るたびに、顔ぶれが変わっています」（10分ほど待ってから調べ始める）" ;;
    target-group-detached) echo "利用者から：「ページを開くと、すぐにエラーになります」（2分ほど待ってから調べ始める）" ;;
    web-stopped) echo "利用者から：「数分間エラーになりましたが、今は直っています。何が起きたのですか」（10分ほど待ってから調べ始める）" ;;
  esac
}

case "${1:-}" in
  list)
    printf '%s\n' "${FAULTS[@]}"
    ;;
  random)
    pick="${FAULTS[$((RANDOM % ${#FAULTS[@]}))]}"
    inject "$pick"
    echo "$pick" > .fault
    echo "障害を1つ入れました。届いた連絡は、次のとおりです。"
    symptom "$pick"
    ;;
  reveal)
    cat .fault
    ;;
  "")
    echo "使い方：inject.sh list | random | reveal | <名前>" >&2
    exit 2
    ;;
  *)
    inject "$1"
    echo "$1" > .fault
    echo "障害を入れました。届いた連絡は、次のとおりです。"
    symptom "$1"
    ;;
esac
