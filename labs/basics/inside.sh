#!/usr/bin/env bash
# 第6章「手元で確かめる」と付録F（LinuxとGitの基礎）のコマンドを、本に載せた順に実行し、結果を確かめる。
# Amazon Linux 2023 のコンテナの中で動かす（verify.sh から呼ぶ）。本文のコマンドは、この中にそのまま書いてある。
# 本文と同じ書き方を確かめるため、ps と ls の出力をそのまま grep や tee に渡している
# shellcheck disable=SC2009,SC2012
set -eu
cd ~

pass=0
ok() { pass=$((pass + 1)); echo "ok $pass - $1"; }
fail() { echo "NG - $1" >&2; exit 1; }
contains() { grep -qE -- "$2" "$3" || { echo "--- $3" >&2; cat "$3" >&2; fail "$1"; }; ok "$1"; }
equals() { [ "$2" = "$3" ] || fail "$1：期待 [$2] 実際 [$3]"; ok "$1"; }
# 失敗するはずのコマンドを実行し、終了コードを確かめる
fails() { local want=$1 name=$2; shift 2; set +e; "$@" > /tmp/fails.out 2>&1; local rc=$?; set -e
  cat /tmp/fails.out; [ "$rc" = "$want" ] || fail "$name：終了コード $want のはずが $rc"; ok "$name（終了コード $rc）"; }

echo '== 準備'
dnf install -y bind-utils openssl iproute procps-ng python3 > /tmp/dnf1.log
dnf install -y git-core procps-ng iproute findutils less tar gzip python3 > /tmp/dnf2.log
ok 'パッケージを入れた'

echo '== 第6章：HTTP'
(
  mkdir -p ~/web && cd ~/web && echo hello > index.html
  python3 -m http.server 8080 --bind 127.0.0.1 > ~/web.log 2>&1 &
  sleep 1
  curl -v http://127.0.0.1:8080/index.html > /tmp/curl-v.txt 2>&1
  cat /tmp/curl-v.txt
  contains 'リクエストの行が見える' '^> GET /index.html HTTP/1.1' /tmp/curl-v.txt
  contains 'ステータスコード200が返る' '^< HTTP/1.0 200 OK' /tmp/curl-v.txt
  contains '本文が返る' '^hello$' /tmp/curl-v.txt
  equals '存在しないパスは404' 404 "$(curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/nothing)"
  equals 'POSTは501' 501 "$(curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8080/index.html)"
  ss -tln | tee /tmp/ss.txt
  contains '8080番で待ち受けている' '127\.0\.0\.1:8080' /tmp/ss.txt

  echo '== 第6章：拒否と時間切れ'
  fails 7 '待ち受けていないポートは、すぐに拒否される' curl -sS http://127.0.0.1:8081/
  contains '拒否のメッセージ' '[Cc]onnection refused|[Cc]ouldn.t connect' /tmp/fails.out
  started=$SECONDS
  fails 28 'どこにも届かない宛先は、時間切れになる' curl -sS --connect-timeout 5 http://192.0.2.10/
  [ $((SECONDS - started)) -ge 4 ] || fail '時間切れまで待っていない'
  ok '5秒ほど待ってから失敗した'

  echo '== 第6章：TLS'
  cd ~/web
  openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost' -keyout key.pem -out cert.pem 2> /tmp/req.log
  openssl s_server -accept 8443 -cert cert.pem -key key.pem -www > ~/tls.log 2>&1 &
  sleep 1
  fails 60 '自分で作った証明書は、そのままでは信頼されない' curl -sS https://localhost:8443/
  contains '理由は自己署名' 'self[- ]signed certificate' /tmp/fails.out
  curl -sS --cacert cert.pem https://localhost:8443/ | head -n 3 | tee /tmp/tls-ok.txt
  contains '信頼を指定すれば、つながる' '<pre>|s_server' /tmp/tls-ok.txt
  fails 60 '名前が一致しなければ、信頼していてもつながらない' curl -sS --cacert cert.pem https://127.0.0.1:8443/
  contains '理由は名前の不一致' '127\.0\.0\.1' /tmp/fails.out
  openssl s_client -connect localhost:8443 -servername localhost < /dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName | tee /tmp/cert.txt
  contains '証明書の名前' 'subject=CN ?= ?localhost' /tmp/cert.txt
  contains '証明書の有効期限' 'notAfter=' /tmp/cert.txt
  contains '証明書の別名' 'DNS:localhost' /tmp/cert.txt

  echo '== 第6章：DNS'
  dig +noall +answer example.com A | tee /tmp/dig-a.txt
  contains 'Aレコードと残りのTTL' '^example\.com\.[[:space:]]+[0-9]+[[:space:]]+IN[[:space:]]+A[[:space:]]' /tmp/dig-a.txt
  dig +noall +answer example.com NS | tee /tmp/dig-ns.txt
  contains 'NSレコード' 'IN[[:space:]]+NS[[:space:]]' /tmp/dig-ns.txt
  dig +short example.com AAAA
  getent hosts localhost | tee /tmp/getent.txt
  contains 'localhost を引ける' 'localhost' /tmp/getent.txt
  kill %1 %2
  ok 'サーバーを止めた'
  echo "$pass" > /tmp/web.count
)
pass=$(cat /tmp/web.count)

echo '== 付録F：場所とファイル'
cd ~
pwd
mkdir -p practice/logs
cd practice
echo 'first line' > notes.txt
echo 'second line' >> notes.txt
cat notes.txt
cp notes.txt notes.bak
mv notes.bak logs/
ls -la
ls -la logs | tee /tmp/ls.txt
contains '移動したファイルがある' 'notes\.bak' /tmp/ls.txt
equals '追記で2行になる' 2 "$(wc -l < notes.txt)"

echo '== 付録F：権限'
echo 'secret' > key.pem
chmod 600 key.pem
ls -l key.pem
equals '持ち主だけが読み書きできる' '600 root key.pem' "$(stat -c '%a %U %n' key.pem)"
echo 'echo hello from script' > hello.sh
chmod +x hello.sh
equals '実行の権限を付けると動く' 'hello from script' "$(./hello.sh)"
id | tee /tmp/id.txt
contains '管理者の番号は0' '^uid=0\(root\)' /tmp/id.txt

echo '== 付録F：探す、絞り込む、つなぐ'
printf '%s\n' '10:00 INFO start' '10:01 ERROR db timeout' '10:02 INFO retry' '10:03 ERROR db timeout' '10:04 ERROR disk full' > logs/app.log
grep ERROR logs/app.log
equals 'ERRORの件数' 3 "$(grep -c ERROR logs/app.log)"
grep -n 'db timeout' logs/app.log
grep ERROR logs/app.log | cut -d ' ' -f 3- | sort | uniq -c | sort -rn | tee /tmp/count.txt
equals '多い順に並ぶ' '2 db timeout' "$(head -n 1 /tmp/count.txt | sed 's/^ *//')"
grep -ri 'error' logs/
equals '最近変更したログが見つかる' "$HOME/practice/logs/app.log" "$(find ~/practice -name '*.log' -mmin -60)"
tail -n 2 logs/app.log
equals '行数' '5 logs/app.log' "$(wc -l logs/app.log)"

echo '== 付録F：プロセスと待ち受けポート'
python3 -m http.server 8080 --bind 127.0.0.1 > /tmp/web.log 2>&1 &
sleep 1
ps aux | grep '[h]ttp.server' | tee /tmp/ps.txt
contains 'プロセスが見える（grep 自身は混ざらない）' 'python3 -m http.server' /tmp/ps.txt
equals 'grep の行は1つだけ' 1 "$(wc -l < /tmp/ps.txt)"
ss -tlnp | tee /tmp/ss2.txt
contains '待ち受けのアドレスとプロセス' '127\.0\.0\.1:8080.*python3' /tmp/ss2.txt
equals 'つながる' 200 "$(curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/)"
kill %1
ok 'サーバーを止めた'

echo '== 付録F：ディスクとメモリ'
df -h /
du -sh ~/practice
free -m
ok 'ディスクとメモリを表示した'

echo '== 付録F：環境変数と終了コード'
export APP_ENV=practice
echo "$APP_ENV"
env | grep APP_ENV
echo "$PATH"
set +e
ls /nothing
echo $? > /tmp/rc-fail
ls ~
echo $? > /tmp/rc-ok
set -e
equals '失敗した直後の終了コード' 2 "$(cat /tmp/rc-fail)"
equals '成功した直後の終了コード' 0 "$(cat /tmp/rc-ok)"

echo '== 付録F：失敗したら止まるスクリプト'
cat > ~/practice/backup.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

src=${1:?バックアップするディレクトリを指定します}
dest="/tmp/backup-$(date +%Y%m%d%H%M%S).tar.gz"
tar -czf "$dest" -C "$src" .
echo "作成しました：$dest"
EOF
chmod +x ~/practice/backup.sh
~/practice/backup.sh ~/practice/logs | tee /tmp/backup.txt
contains 'バックアップを作った' '作成しました：/tmp/backup-' /tmp/backup.txt
~/practice/backup.sh /nothing || echo "失敗を検知しました（終了コード $?）" | tee /tmp/backup-ng.txt
contains '失敗を終了コードで検知した' '終了コード 2' /tmp/backup-ng.txt
fails 1 '引数がなければ止まる' ~/practice/backup.sh
contains '理由を表示する' 'バックアップするディレクトリを指定します' /tmp/fails.out

echo '== 付録F：Gitの最初の設定'
git config --global user.name 'Taro Yamada'
git config --global user.email 'taro@example.com'
git config --global init.defaultBranch main
git config --global --list

echo '== 付録F：変更して、コミットする'
mkdir -p ~/repo && cd ~/repo
git init
echo '# 練習用のリポジトリ' > README.md
git status
git add README.md
git commit -m '最初のコミット'
git switch -c feature/add-config
echo 'region = ap-northeast-1' > config.txt
git add config.txt
git commit -m '設定ファイルを追加する'
git log --oneline --graph --all
git switch main
git merge feature/add-config
git log --oneline
equals 'main に2つのコミット' 2 "$(git rev-list --count main)"

echo '== 付録F：衝突を解消する'
cd ~/repo
git switch -c feature/tokyo
echo 'region = ap-northeast-1 # Tokyo' > config.txt
git commit -am '東京であることを明記する'
git switch main
echo 'region = ap-northeast-3' > config.txt
git commit -am '大阪に変える'
git merge feature/tokyo || true
git status
cat config.txt
equals '衝突の目印が、本文のとおりに書き込まれる' "$(printf '%s\n' '<<<<<<< HEAD' 'region = ap-northeast-3' '=======' 'region = ap-northeast-1 # Tokyo' '>>>>>>> feature/tokyo')" "$(cat config.txt)"
echo 'region = ap-northeast-3 # Osaka' > config.txt
git add config.txt
git commit -m '衝突を解消する：大阪を採る'
git log --oneline --graph
equals '解消のコミットは、2つの親を持つ' 2 "$(git rev-list --parents -n 1 HEAD | wc -w | awk '{print $1 - 1}')"

echo '== 付録F：取り消す'
echo 'instance_type = t3.micro' >> config.txt
git commit -am 'サーバーの種類を追加する'
echo 'broken' > config.txt
git restore config.txt
cat config.txt
equals 'restore で最後のコミットに戻る' "$(printf '%s\n' 'region = ap-northeast-3 # Osaka' 'instance_type = t3.micro')" "$(cat config.txt)"
git revert --no-edit HEAD
cat config.txt
git log --oneline -n 3
equals 'revert で打ち消される' 'region = ap-northeast-3 # Osaka' "$(cat config.txt)"
contains 'revert は新しいコミットとして残る' 'Revert' <(git log --oneline -n 1)

echo '== 付録F：載せてはいけないものを除く'
cd ~/repo
printf '%s\n' '.terraform/' '*.tfstate' '*.tfstate.*' '.env' '*.pem' > .gitignore
echo 'AWS_SECRET_ACCESS_KEY=example' > .env
git status --short | tee /tmp/short.txt
equals '.env は一覧に出ない' '?? .gitignore' "$(cat /tmp/short.txt)"
git add .gitignore
git commit -m '載せないファイルを指定する'
git check-ignore -v .env | tee /tmp/ignore.txt
contains 'どの行で除外されたかがわかる' '^\.gitignore:4:\.env' /tmp/ignore.txt

echo "== すべて確かめました（$pass 項目）"
