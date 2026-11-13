#!/usr/bin/env bash
# 第6章「手元で確かめる」と付録Fのコマンドを、Amazon Linux 2023 のコンテナで、最初から最後まで実行する。
#   使い方：bash labs/basics/verify.sh
set -euo pipefail
cd "$(dirname "$0")"
image=public.ecr.aws/amazonlinux/amazonlinux:2023
docker run --rm -v "$PWD/inside.sh:/lab/inside.sh:ro" "$image" bash /lab/inside.sh
