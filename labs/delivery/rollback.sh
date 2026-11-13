#!/usr/bin/env bash
# 第19章：サービスを、指定したタスク定義の版に戻す。
#   使い方：bash rollback.sh <戻す先のタスク定義>   例 bash rollback.sh cloudbook-app:7
#   必要な環境変数：ECS_CLUSTER、ECS_SERVICE
set -euo pipefail
: "${ECS_CLUSTER:?}" "${ECS_SERVICE:?}"
target=${1:?戻す先のタスク定義を指定します（例 cloudbook-app:7）}
started=$SECONDS

aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" \
  --task-definition "$target" --query 'service.deployments[0].id' --output text
aws ecs wait services-stable --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"
read -r running state < <(aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].deployments[0].[taskDefinition,rolloutState]' --output text)
echo "動いている版：$running（$state）"
case "$running" in
  *"$target") ;;
  *) echo "指定した版になっていません" >&2; exit 1 ;;
esac
echo "戻しました。かかった時間：$((SECONDS - started))秒"
