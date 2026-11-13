# 第19章：アプリのイメージ。小さな土台を使い、管理者以外のユーザーで動かす
FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 必要なファイルだけを入れる（COPY . . は、テストや手元の設定まで入れてしまう）
COPY app.py .
ARG APP_VERSION=local
ENV APP_VERSION=$APP_VERSION PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 1000
EXPOSE 8080
# ファイルシステムを読み取り専用にして動かすため、gunicorn の作業用ファイルはメモリ上（/dev/shm）に置く
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers", "2", "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-", "app:app"]
