#!/usr/bin/env bash
# 第19章：イメージを作ってECRに登録し、ECSのサービスを新しい版に入れ替える。
# GitHub Actions のデプロイのジョブから呼ぶ。手元で試すときも、同じ変数を設定して実行できる。
#
#   必要な環境変数：
#     AWS_REGION      例 ap-northeast-1
#     ECR_REPOSITORY  例 cloudbook-app
#     ECS_CLUSTER     例 cloudbook
#     ECS_SERVICE     例 cloudbook-app
#     IMAGE_TAG       イメージに付けるタグ。コミットIDを使う（latest は使わない）
#
#   bash deploy.sh             イメージの登録から、サービスの入れ替えまで行う
#   bash deploy.sh --push-only イメージの登録だけを行う（サービスを作る前の、最初の1回に使う）
set -euo pipefail
cd "$(dirname "$0")"

: "${AWS_REGION:?}" "${ECR_REPOSITORY:?}" "${IMAGE_TAG:?}"
push_only=false
case "${1:-}" in
  '') ;;
  --push-only) push_only=true ;;
  *) echo "使い方：bash deploy.sh [--push-only]" >&2; exit 2 ;;
esac
if [ "$push_only" = false ]; then
  : "${ECS_CLUSTER:?}" "${ECS_SERVICE:?}"
fi
if [ "$IMAGE_TAG" = latest ]; then
  echo "IMAGE_TAG に latest は使えません。コミットIDなど、版ごとに違う値を使います" >&2
  exit 1
fi

account=$(aws sts get-caller-identity --query Account --output text)
registry="$account.dkr.ecr.$AWS_REGION.amazonaws.com"
image="$registry/$ECR_REPOSITORY:$IMAGE_TAG"
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

echo "== 1. イメージを作り、ECRに登録する：$image"
aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$registry"
# Fargate は x86_64 で動かす設定。Apple シリコンのMacで作るときも、x86_64 用に作る
docker build --platform linux/amd64 --build-arg APP_VERSION="$IMAGE_TAG" -t "$image" app
docker push "$image"
if [ "$push_only" = true ]; then
  echo "登録しました：$image"
  exit 0
fi

echo "== 2. 今のタスク定義を元に、イメージだけを差し替えた新しい版を登録する"
current=$(aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].taskDefinition' --output text)
aws ecs describe-task-definition --task-definition "$current" --query taskDefinition \
  > "$work/current.json"
jq --arg image "$image" -f render-taskdef.jq "$work/current.json" > "$work/next.json"
next=$(aws ecs register-task-definition --cli-input-json "file://$work/next.json" \
  --query 'taskDefinition.taskDefinitionArn' --output text)
echo "前の版：$current"
echo "新しい版：$next"

echo "== 3. サービスを新しい版に入れ替え、安定するまで待つ"
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" \
  --task-definition "$next" --query 'service.deployments[0].id' --output text
aws ecs wait services-stable --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"

# 安定しただけでは成功とは限らない。新しい版が起動に失敗し続けると、
# ECSが前の版に自動で戻し（サーキットブレーカー）、その状態でも「安定」になるため
read -r running state < <(aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].deployments[0].[taskDefinition,rolloutState]' --output text)
echo "動いている版：$running（$state）"
if [ "$running" != "$next" ] || [ "$state" != COMPLETED ]; then
  echo "新しい版に入れ替わりませんでした。サービスのイベントと、停止したタスクの理由を確かめます" >&2
  exit 1
fi
echo "反映しました。戻すときは：bash rollback.sh $current"
