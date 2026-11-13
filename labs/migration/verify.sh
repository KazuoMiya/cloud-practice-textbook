#!/usr/bin/env bash
# 第29章「手元で通す：移行のリハーサル」を、最初から最後まで自動で通して確かめる。
# 使い方：Docker を入れた端末で、 bash labs/migration/verify.sh
# 旧環境と新環境を作り、終わったら（途中で失敗しても）消す。
set -euo pipefail
cd "$(dirname "$0")"

say() { printf '\n== %s\n' "$*"; }
fail() {
  echo "FAIL: $*" >&2
  exit 1
}
cleanup() { docker compose down -v >/dev/null 2>&1 || true; }
trap cleanup EXIT

old() { docker compose exec -T old-db psql -U postgres -d shop -At "$@"; }
new() { docker compose exec -T new-db psql -U postgres -d shop -At "$@"; }
same() {
  diff <(docker compose exec -T old-db psql -U postgres -d shop -At -f /checks.sql) \
       <(docker compose exec -T new-db psql -U postgres -d shop -At -f /checks.sql)
}

say "1. 旧環境と新環境を立てる"
docker compose up -d --wait

say "2. 棚卸し：旧環境に何があるかを調べる"
docker compose exec -T old-db psql -U postgres -d shop -c 'select version()'
docker compose exec -T old-db psql -U postgres -d shop -c '\dt+'
docker compose exec -T old-db psql -U postgres -d shop -f /checks.sql
grep -q '^PostgreSQL 13\.' <<<"$(old -c 'select version()')" || fail "旧環境が PostgreSQL 13 でない"
grep -q '^PostgreSQL 17\.' <<<"$(new -c 'select version()')" || fail "新環境が PostgreSQL 17 でない"
[ "$(old -c 'select count(*) from orders')" = 2000 ] || fail "旧環境の注文が2000件でない"

say "3. リハーサル：新しい版の道具で取り出し、新環境に入れる（時間を測る）"
time docker compose exec -T new-db pg_dump -h old-db -U postgres -d shop | docker compose exec -T new-db psql -U postgres -d shop -v ON_ERROR_STOP=1 -q -o /dev/null
same || fail "リハーサルの後、旧環境と新環境の値が一致しない"
echo "一致"

say "4. リハーサルの後も、旧環境では業務が進む：写しは古くなる"
docker compose exec -T old-db psql -U postgres -d shop -c "insert into orders (customer_id, amount) select 1 + (n % 50), 1000 from generate_series(1, 5) as n"
if same >/dev/null; then fail "旧環境に注文を足したのに、差が出ない"; fi
echo "差がある（期待どおり）"

say "5. 切り替え：旧環境への書き込みを止める"
docker compose exec -T old-db psql -U postgres -d shop -c 'alter database shop set default_transaction_read_only = on'
# 書き込みは、エラーになるのが正しい。出力を受け取ってから、内容を確かめる
result=$(docker compose exec -T old-db psql -U postgres -d shop -c "insert into orders (customer_id, amount) values (1, 100)" 2>&1 || true)
echo "$result"
grep -q 'read-only transaction' <<<"$result" || fail "旧環境に、まだ書き込める"
echo "書き込めない（期待どおり）"

say "6. 切り替え：新環境を作り直して、最後の写しを取る（時間を測る）"
docker compose exec -T new-db dropdb -U postgres shop
docker compose exec -T new-db createdb -U postgres shop
time docker compose exec -T new-db pg_dump -h old-db -U postgres -d shop | docker compose exec -T new-db psql -U postgres -d shop -v ON_ERROR_STOP=1 -q -o /dev/null

say "7. 切り替え：判断の基準を確かめる"
same || fail "最後の写しの後、旧環境と新環境の値が一致しない"
echo "一致"
[ "$(new -c 'select count(*) from orders')" = 2005 ] || fail "新環境の注文が2005件でない"
[ "$(new -c 'show default_transaction_read_only')" = off ] || fail "新環境まで読み取り専用になっている"

say "8. 切り替え：新環境で、新しい注文を受け付けられる"
docker compose exec -T new-db psql -U postgres -d shop -c "insert into orders (customer_id, amount) values (1, 100) returning id"
[ "$(new -c 'select max(id) from orders')" = 2006 ] || fail "新しい注文のIDが、続きの番号になっていない"

say "9. 切り戻しの練習：旧環境に戻すと、切り替えの後に受け付けた注文は、旧環境にない"
docker compose exec -T old-db psql -U postgres -d postgres -c 'alter database shop reset default_transaction_read_only'
docker compose exec -T old-db psql -U postgres -d shop -c "insert into orders (customer_id, amount) values (2, 200) returning id"
if same; then fail "切り戻しの後、差が出ない"; fi
[ "$(old -c 'select max(id) from orders')" = 2006 ] || fail "旧環境の新しい注文のIDが、2006でない"
[ "$(old -c 'select count(*) from orders where amount = 100')" = 0 ] || fail "新環境だけで受け付けた注文が、旧環境にある"
echo "新環境で受け付けた1件は、旧環境にない（期待どおり）"

say "10. 片付け"
docker compose down -v
[ -z "$(docker compose ps -q 2>/dev/null)" ] || fail "コンテナが残っている"
echo
echo "すべての確認が通りました。"
