:::goal
- Linuxのサーバーで、ファイルの操作、権限の確認、ログの検索、プロセスと待ち受けポートの確認ができる
- 失敗したときに止まるシェルスクリプトを書き、終了コードで成否を判定できる
- Gitで、ブランチを切って変更し、コミットし、PRに出す流れを一人で回せる
- 衝突（コンフリクト）を解消し、共有済みの変更を安全に取り消せる
:::

この付録は、第2部に進む前に必要な、LinuxとGitの操作をまとめたものです。クラウドのサーバー、コンテナ、CI/CDの実行環境、AWS CloudShell は、ほとんどがLinuxで動いています。コードとインフラの定義は、Gitで管理し、PR（プルリクエスト）でレビューを受けてから反映します。どちらも、案件に入った初日から使います。

ここに載せたコマンドは、すべて、この本のリポジトリの [labs/basics](https://github.com/KazuoMiya/cloud-practice-textbook/tree/main/labs/basics) のスクリプトで、変更のたびに最初から最後まで実行して確かめています。

## 練習の場所

料金のかからない、次のどちらかで練習します。どちらも Amazon Linux 2023 で、この本で作るEC2のサーバーと同じ種類のLinuxです。

| 場所 | 用意のしかた | 向いている人 |
|---|---|---|
| AWS CloudShell | AWSの管理画面の上部にある、端末の形のアイコンを押す。料金はかからない | 学習用のAWSアカウントを用意した人 |
| Dockerのコンテナ | 下のコマンドで起動する。抜けるとコンテナごと消えるので、何を壊しても困らない | 手元のPCにDockerを入れた人 |

```bash
docker run --rm -it public.ecr.aws/amazonlinux/amazonlinux:2023 bash
dnf install -y git-core procps-ng iproute findutils less tar gzip python3
```

CloudShell でもコンテナでも、管理者（root）の権限が要る操作には、先頭に `sudo` を付けます（コンテナの中は、最初から管理者なので不要）。

## Linuxの基本操作

### 場所とファイル

Linuxでは、すべてのファイルが `/` から始まる1つの木の形に並んでいます。`/` から書く場所を絶対パス、今いる場所から書く場所を相対パスといいます。`~` は自分のホームディレクトリ、`.` は今いる場所、`..` は1つ上です。

```bash
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
ls -la logs
```

| コマンド | 意味 |
|---|---|
| `pwd` | 今いる場所を表示する |
| `ls -la` | ファイルの一覧を、隠しファイル（`.` で始まるもの）と詳しい情報つきで表示する |
| `cd 場所` | 移動する。`cd -` で直前の場所に戻る |
| `mkdir -p` | ディレクトリを作る。途中の階層もまとめて作る |
| `cp`、`mv` | 複製する、移動する（名前の変更も `mv`） |
| `rm` | 削除する。ごみ箱はなく、元に戻せない。`rm -r` はディレクトリごと消すので、実行する前に `pwd` と `ls` で場所を確かめる |
| `>`、`>>` | コマンドの出力を、ファイルに書く（`>` は上書き、`>>` は追記） |
| `cat`、`less` | ファイルの中身を表示する。長いものは `less` で開き、`q` で閉じる |

### 権限

`ls -l` の左端の10文字が、ファイルの種類と権限です。

```text
-rw-r--r--  1 ec2-user ec2-user  23 ... notes.txt
```

先頭の1文字は種類（`-` はファイル、`d` はディレクトリ）です。残りの9文字を3文字ずつ、持ち主、グループ、その他の人の順に読みます。`r` は読む、`w` は書く、`x` は実行する（ディレクトリなら中に入る）権限です。数字で書くときは、r=4、w=2、x=1 を足します。

```bash
echo 'secret' > key.pem
chmod 600 key.pem
ls -l key.pem
stat -c '%a %U %n' key.pem
echo 'echo hello from script' > hello.sh
chmod +x hello.sh
./hello.sh
id
```

`chmod 600` は「持ち主だけが読み書きできる」です。SSHの秘密鍵は、ほかの人が読める権限になっていると、`UNPROTECTED PRIVATE KEY FILE` というエラーで使えません。`id` は、今の自分が誰で、どのグループに属しているかを表示します。管理者（root）の番号は0です。

### 探す、絞り込む、つなぐ

ログの調査で、いちばん使う操作です。`|`（パイプ）で、前のコマンドの出力を、次のコマンドの入力に渡します。

```bash
printf '%s\n' '10:00 INFO start' '10:01 ERROR db timeout' '10:02 INFO retry' '10:03 ERROR db timeout' '10:04 ERROR disk full' > logs/app.log
grep ERROR logs/app.log
grep -c ERROR logs/app.log
grep -n 'db timeout' logs/app.log
grep ERROR logs/app.log | cut -d ' ' -f 3- | sort | uniq -c | sort -rn
grep -ri 'error' logs/
find ~/practice -name '*.log' -mmin -60
tail -n 2 logs/app.log
wc -l logs/app.log
```

| コマンド | 意味 |
|---|---|
| `grep 文字 ファイル` | 文字を含む行だけを表示する。`-n` 行番号、`-c` 件数、`-i` 大文字と小文字を区別しない、`-r` ディレクトリの中を全部 |
| `cut -d ' ' -f 3-` | 空白で区切り、3つ目以降の項目を取り出す |
| `sort`、`uniq -c` | 並べ替える。続けて同じ行を数える（`sort` してから使う） |
| `find 場所 -name 名前` | ファイルを探す。`-mmin -60` は60分以内に変更されたもの |
| `tail -n 2`、`head` | 末尾、先頭の何行かを表示する。`tail -f` は、追記される行を表示し続ける（止めるのは Ctrl+C） |
| `wc -l` | 行数を数える |

4つ目のコマンドは「どのエラーが、何回起きたか」を、多い順に並べます。障害の調査で、最初に全体像をつかむ定番の形です。

### プロセスと待ち受けポート

```bash
python3 -m http.server 8080 --bind 127.0.0.1 > /tmp/web.log 2>&1 &
sleep 1
ps aux | grep '[h]ttp.server'
ss -tlnp
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/
kill %1
```

| コマンド | 意味 |
|---|---|
| `コマンド &` | 後ろで動かす。`kill %1` で止める |
| `ps aux` | 動いているプロセスの一覧。`grep '[h]ttp.server'` のように書くと、grep 自身が結果に混ざらない |
| `ss -tlnp` | 待ち受けているTCPのポートと、そのプロセス。`127.0.0.1:8080` は「このサーバーの中からだけ受け付ける」、`0.0.0.0:8080` は「どこからでも受け付ける」 |
| `kill 番号` | プロセスを止める。止まらないときの `kill -9` は、後始末をさせずに止めるので、最後の手段にする |

アプリに外からつながらないとき、`ss -tlnp` で「待ち受けているか」と「127.0.0.1 だけで待ち受けていないか」を確かめるのは、{{ch:net}}の確認順の6番目にあたります。

### サービスとログ（サーバーの場合）

EC2のサーバーでは、常に動かすプログラムを systemd というしくみで管理します。コンテナや CloudShell では systemd が動いていないため、ここは読むだけにし、{{ch:s3}}のサーバーで試します。

```bash
sudo systemctl status nginx
sudo systemctl restart nginx
sudo systemctl enable --now nginx
sudo journalctl -u nginx --since '10 min ago'
sudo journalctl -u nginx -f
```

| コマンド | 意味 |
|---|---|
| `systemctl status` | 動いているか、最後に止まった理由、直近のログ |
| `systemctl restart`、`enable --now` | 再起動する。起動時に自動で動くようにして、今すぐ起動する |
| `journalctl -u 名前` | そのサービスのログ。`--since` で期間を絞り、`-f` で追い続ける |

### ディスクとメモリ

```bash
df -h /
du -sh ~/practice
free -m
```

`df -h` はディスクの空き、`du -sh` はディレクトリの使用量、`free -m` はメモリの使用量です。ディスクが一杯になると、ログが書けずにアプリが止まるといった、わかりにくい障害になります。

### 環境変数と終了コード

```bash
export APP_ENV=practice
echo "$APP_ENV"
env | grep APP_ENV
echo "$PATH"
ls /nothing
echo $?
ls ~
echo $?
```

`export` で設定した変数は、そこから起動したコマンドにも引き継がれます。AWS CLI の `AWS_PROFILE` や `AWS_REGION` も環境変数です。`$?` は、直前のコマンドの終了コードで、0が成功、それ以外が失敗です。スクリプトやCIは、この数字で成否を判定します。

### 失敗したら止まるスクリプト

コマンドを並べただけのスクリプトは、途中で失敗しても、次の行に進みます。「バックアップに失敗したのに、元のデータを消してしまった」という事故の原因になります。

```bash
cat > ~/practice/backup.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

src=${1:?バックアップするディレクトリを指定します}
dest="/tmp/backup-$(date +%Y%m%d%H%M%S).tar.gz"
tar -czf "$dest" -C "$src" .
echo "作成しました：$dest"
EOF
chmod +x ~/practice/backup.sh
~/practice/backup.sh ~/practice/logs
~/practice/backup.sh /nothing || echo "失敗を検知しました（終了コード $?）"
```

| 書き方 | 意味 |
|---|---|
| `#!/usr/bin/env bash` | このファイルを bash で実行する（1行目に書く） |
| `set -e` | 失敗したコマンドがあれば、そこで止まる |
| `set -u` | 設定していない変数を使ったら、止まる（変数名の打ち間違いで、空の値のまま進むのを防ぐ） |
| `set -o pipefail` | パイプの途中のコマンドの失敗も、失敗として扱う |
| `"$変数"` | 変数は、必ず `"` で囲む。値に空白が入っても、1つの値として扱われる |
| `${1:?説明}` | 1つ目の引数がなければ、説明を表示して止まる |

この本の参考実装のスクリプトは、すべてこの形で書いています。

## Gitの基本操作

### 用語

| 用語 | 意味 |
|---|---|
| リポジトリ | 変更の履歴をまるごと持った、プロジェクトの入れ物。手元のもの（ローカル）と、GitHubなどに置いた共有のもの（リモート）がある |
| コミット | 変更のまとまりを、説明をつけて履歴に記録したもの。後から、いつでもその時点に戻れる |
| ステージ | 次のコミットに入れる変更を選んで置いておく場所。`git add` で置く |
| ブランチ | 履歴の分かれ道。main を壊さずに、別の道で変更を進める |
| プルリクエスト（PR） | 自分のブランチの変更を、main に取り込んでほしいという依頼。レビューと自動テストの場になる |

### 最初の設定

```bash
git config --global user.name 'Taro Yamada'
git config --global user.email 'taro@example.com'
git config --global init.defaultBranch main
git config --global --list
```

コミットには、ここで設定した名前とメールアドレスが記録され、公開のリポジトリでは誰でも見られます。個人のアドレスを公開したくない場合は、GitHub の設定にある、公開用のアドレス（noreply）を使います。

### 変更して、コミットする

```bash
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
```

ふだんの作業は、次の繰り返しです。

1. main を最新にする（共有のリポジトリがあるときは `git switch main` のあと `git pull`）
2. 作業用のブランチを作る（`git switch -c ブランチ名`）
3. 変更し、`git status` と `git diff` で中身を確かめてから、`git add` と `git commit`
4. `git push -u origin ブランチ名` で共有のリポジトリに送り、PRを作る
5. レビューと自動テストを通ったら、main に取り込む（マージ）。取り込んだブランチは消す

コミットは、1つの目的ごとに小さく分けます。「設定の追加」と「関係のない誤字の修正」を1つのコミットに混ぜると、後から片方だけを取り消せません。説明（コミットメッセージ）には、何を変えたかより、なぜ変えたかを書きます。

### 衝突（コンフリクト）を解消する

2つのブランチで、同じファイルの同じ場所を別々に変えると、取り込むときに、どちらを採るかをGitが決められず、衝突になります。

```bash
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
```

衝突したファイルには、両方の内容が、目印つきで書き込まれます。

```text
<<<<<<< HEAD
region = ap-northeast-3
=======
region = ap-northeast-1 # Tokyo
>>>>>>> feature/tokyo
```

`<<<<<<< HEAD` から `=======` までが今いるブランチ（main）、`=======` から `>>>>>>>` までが取り込もうとしたブランチの内容です。どちらを採るか（または両方を合わせるか）を、変更した人と話して決め、目印を消して正しい内容にしてから、コミットします。

```bash
echo 'region = ap-northeast-3 # Osaka' > config.txt
git add config.txt
git commit -m '衝突を解消する：大阪を採る'
git log --oneline --graph
```

### 取り消す

どの取り消し方を使うかは、その変更が、もう共有のリポジトリに送ってあるかで決まります。

| 状況 | 使うコマンド | 結果 |
|---|---|---|
| ファイルを変えたが、まだ add していない | `git restore ファイル` | 最後のコミットの状態に戻す（変更は消える） |
| add したが、まだコミットしていない | `git restore --staged ファイル` | ステージから外す（変更は残る） |
| コミットしたが、まだ push していない | `git commit --amend`、`git reset` | 直前のコミットを直す、なかったことにする |
| push 済み（ほかの人が持っているかもしれない） | `git revert コミット` | 打ち消す変更を、新しいコミットとして加える。履歴は書き換えない |

```bash
echo 'instance_type = t3.micro' >> config.txt
git commit -am 'サーバーの種類を追加する'
echo 'broken' > config.txt
git restore config.txt
cat config.txt
git revert --no-edit HEAD
cat config.txt
git log --oneline -n 3
```

push 済みの履歴を `git reset` や `git push --force` で書き換えると、ほかの人の手元の履歴と食い違い、作業を失わせることがあります。共有した後は `git revert` を使います。

### 載せてはいけないものを除く

```bash
cd ~/repo
printf '%s\n' '.terraform/' '*.tfstate' '*.tfstate.*' '.env' '*.pem' > .gitignore
echo 'AWS_SECRET_ACCESS_KEY=example' > .env
git status --short
git add .gitignore
git commit -m '載せないファイルを指定する'
git check-ignore -v .env
```

`.gitignore` に書いた名前のファイルは、`git add` しても登録されません。Terraform のステート（資源の情報を含む）、`.env`（秘密情報を置くことが多い）、秘密鍵は、最初に除外しておきます。

:::warn 秘密情報をコミットしてしまったら
履歴から消すより先に、その秘密情報を無効にします（アクセスキーなら無効化して作り直す、パスワードなら変える）。公開のリポジトリに載ったキーは、数分で見つけられて悪用されることがあります。履歴から消しても、すでに誰かの手元に複製されているかもしれないため、「無効にする」が唯一の確実な対策です。そのうえで、履歴からの削除と、使われた形跡の確認（{{ch:sec}}）を行います。
:::

## 確認ポイント

- 権限 `-rw-------` を数字で書くと何になるかと、SSHの秘密鍵にその権限が必要な理由を説明できる
- ログから、エラーの種類ごとの件数を、多い順に並べるコマンドを書ける
- アプリにつながらないとき、プロセスが動いているか、どのアドレスとポートで待ち受けているかを確かめられる
- `set -euo pipefail` の3つが、それぞれ何を防ぐかを説明できる
- push 済みの変更を取り消すとき、`git reset` ではなく `git revert` を使う理由を説明できる

## 章末問題

:::q 調査 | エラーの多いものから並べる
`/var/log/app/` の下に、日付ごとのログファイル（`app-20261112.log` など）がたくさんあります。すべてのファイルから「ERROR」を含む行を探し、行の4つ目以降（空白区切り）が同じものを数え、多い順に上から5つを表示するコマンドを書いてください。
:::a
```bash
grep -h ERROR /var/log/app/*.log | cut -d ' ' -f 4- | sort | uniq -c | sort -rn | head -n 5
```

`grep -h` は、結果の行の先頭にファイル名を付けない指定です（複数のファイルを検索すると、既定ではファイル名が付き、同じエラーでも別の行として数えられてしまう）。`uniq -c` は隣り合った同じ行しかまとめないため、先に `sort` で並べます。最後の `sort -rn` は、数として（`-n`）、大きい順に（`-r`）並べます。
:::

:::q 切り分け | 外からつながらない
EC2のサーバーで動かしたアプリに、ALB経由でつながりません。サーバーに入って `ss -tlnp` を実行すると、次の行がありました。原因と直し方を説明してください。

```text
LISTEN 0  128  127.0.0.1:8080  0.0.0.0:*  users:(("python3",pid=2140,fd=3))
```
:::a
アプリは動いていて、8080番で待ち受けていますが、待ち受けているアドレスが 127.0.0.1 です。これは「このサーバーの中からの接続だけを受け付ける」という意味で、ALBのように外から来る接続は受け付けません。セキュリティグループやルートテーブルが正しくても、つながりません。

直し方は、アプリの設定で、待ち受けるアドレスを 0.0.0.0（すべてのアドレス）か、サーバーのプライベートIPアドレスにすることです。外からの接続の制限は、アプリではなくセキュリティグループで行います（ALBからの8080番だけを許可する）。
:::

:::q 説明 | 止まらないスクリプト
次のスクリプトを実行したところ、`/data` がまだ残っているべき日に消えていました。原因と、直したスクリプトを示してください。

```bash
#!/usr/bin/env bash
tar -czf /backup/data.tar.gz /data
rm -rf /data
```
:::a
原因：`set -e` がないため、`tar` が失敗しても（`/backup` が一杯、または存在しない、など）、次の `rm -rf /data` が実行されます。バックアップがないまま、元のデータを消してしまいます。

```bash
#!/usr/bin/env bash
set -euo pipefail
archive=/backup/data.tar.gz
tar -czf "$archive" /data
tar -tzf "$archive" > /dev/null   # 作ったものが読めることを確かめる
rm -rf /data
```

`set -e` で、失敗したところで止まるようにします。さらに、消す前に、作ったバックアップが読めることを確かめます。消す操作の前には「消してよい状態であることの確認」を置く、というのが、スクリプトに限らない原則です。
:::

:::q 判断 | 取り消し方を選ぶ
main に取り込んで push 済みのコミットに、誤った設定が入っていたことがわかりました。チームの3人が、すでにその後の作業を始めています。どう取り消しますか。`git reset` と `git push --force` を使ってはいけない理由も説明してください。
:::a
`git revert 誤ったコミット` で、打ち消す変更を新しいコミットとして作り、PRを通して main に取り込みます。履歴は書き換わらず、「誤った設定が入り、それを打ち消した」ことが記録に残ります。

`git reset` で履歴からコミットを消し、`git push --force` で共有のリポジトリを上書きすると、3人の手元の履歴と、共有のリポジトリの履歴が食い違います。次に3人が push や pull をしたときに、消したはずのコミットが戻ってきたり、他人の作業を上書きして失わせたりします。共有した後の履歴は書き換えない、が原則です。
:::
