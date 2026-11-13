#!/usr/bin/env bash
# 第31章「手元のクラスターで確かめる」の実習を、最初から最後まで自動で通して確かめる。
# 使い方：Docker、kind、kubectl を入れた端末で、 bash labs/k8s/verify.sh
# クラスター「cloudbook」を作り、終わったら（途中で失敗しても）消す。
set -euo pipefail
cd "$(dirname "$0")"

say() { printf '\n== %s\n' "$*"; }
fail() {
  echo "FAIL: $*" >&2
  kubectl -n cloudbook get pods -o wide >&2 || true
  kubectl -n cloudbook get events --sort-by=.lastTimestamp 2>&1 | tail -n 25 >&2 || true
  exit 1
}
cleanup() { kind delete cluster --name cloudbook >/dev/null 2>&1 || true; }
trap cleanup EXIT

# retry <回数> <コマンド...>：コマンドが成功するまで、1秒おきに繰り返す
retry() {
  local limit=$1 i=0
  shift
  until "$@"; do
    i=$((i + 1))
    [ "$i" -ge "$limit" ] && return 1
    sleep 1
  done
}

ready() { kubectl -n cloudbook get deployment web -o jsonpath='{.status.readyReplicas}'; }
ready_is() { [ "$(ready)" = "$1" ]; }
image() { kubectl -n cloudbook get deployment web -o jsonpath='{.spec.template.spec.containers[0].image}'; }
# 出力は、いったん受け取ってから調べる。パイプの途中で読むのをやめると、前の命令が失敗として扱われるため
has_reason() {
  local reasons
  reasons=$(kubectl -n cloudbook get pods -l app=web \
    -o jsonpath='{range .items[*]}{.status.containerStatuses[0].state.waiting.reason}{"\n"}{end}')
  grep -Eq "$1" <<<"$reasons"
}
running_but_not_ready() {
  local states
  states=$(kubectl -n cloudbook get pods -l app=web \
    -o jsonpath='{range .items[*]}{.status.phase}{" "}{.status.containerStatuses[0].ready}{"\n"}{end}')
  grep -q '^Running false$' <<<"$states"
}
# READY でないPodの名前を1つ返す
not_ready_pod() {
  kubectl -n cloudbook get pods -l app=web \
    -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[0].ready}{"\n"}{end}' | awk '$2 == "false" {print $1; exit}'
}
probe_failed() {
  local detail
  detail=$(kubectl -n cloudbook describe pod "$(not_ready_pod)")
  grep -m1 'statuscode: 404' <<<"$detail"
}
client_done() { [ "$(kubectl -n cloudbook get pod client -o jsonpath='{.status.phase}')" = Succeeded ]; }
# クラスターの中から、Service の名前で20回取りに行き、応答したPodの名前を、重複なしで返す
fetch() {
  kubectl -n cloudbook delete pod client --ignore-not-found >/dev/null
  # shellcheck disable=SC2016  # $(seq 20) は、Podの中のシェルで展開させる
  kubectl -n cloudbook run client --restart=Never --image=busybox:1.36 -- \
    sh -c 'for i in $(seq 20); do wget -qO- http://web; echo; done' >/dev/null
  retry 120 client_done || fail "確認用のPodが終わらない"
  kubectl -n cloudbook logs client | grep -o 'web-[a-z0-9-]*' | sort -u || true
  kubectl -n cloudbook delete pod client >/dev/null
}

say "1. クラスターを作る"
kind create cluster --config kind.yaml
kubectl wait --for=condition=Ready nodes --all --timeout=120s
kubectl get nodes
[ "$(kubectl get nodes --no-headers | awk '$2 == "Ready"' | wc -l)" -eq 3 ] || fail "ノードが3台そろっていない"

say "2. 宣言して、動かす"
kubectl apply -f web.yaml
kubectl -n cloudbook rollout status deployment/web --timeout=180s
kubectl -n cloudbook get pods -o wide
nodes=$(kubectl -n cloudbook get pods -l app=web -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | sort -u | wc -l)
[ "$nodes" -eq 2 ] || fail "Podが2つのノードに分かれていない"

say "3. Service 経由で、2つのPodに届く"
names=$(fetch)
echo "$names"
[ "$(echo "$names" | grep -c web-)" -eq 2 ] || fail "2つのPodから応答が返らない"

say "4. Podを1つ消しても、元の数に戻る"
victim=$(kubectl -n cloudbook get pods -l app=web -o jsonpath='{.items[0].metadata.name}')
kubectl -n cloudbook delete pod "$victim"
kubectl -n cloudbook rollout status deployment/web --timeout=120s
retry 60 ready_is 2 || fail "2つに戻らない"
remaining=$(kubectl -n cloudbook get pods -l app=web -o name)
if grep -q "$victim" <<<"$remaining"; then fail "消したPodが残っている"; fi

say "5. ファイルを書き換えて、数を変える"
sed 's/replicas: 2 /replicas: 4 /' web.yaml | kubectl apply -f -
kubectl -n cloudbook rollout status deployment/web --timeout=120s
retry 60 ready_is 4 || fail "4つにならない"
kubectl apply -f web.yaml
retry 60 ready_is 2 || fail "2つに戻らない"

say "6. 止めずに入れ替えて、元に戻す"
sed 's/nginx:1.27-alpine/nginx:1.28-alpine/' web.yaml | kubectl apply -f -
kubectl -n cloudbook rollout status deployment/web --timeout=180s
[ "$(image)" = nginx:1.28-alpine ] || fail "新しいイメージになっていない"
kubectl -n cloudbook rollout history deployment/web
kubectl -n cloudbook rollout undo deployment/web
kubectl -n cloudbook rollout status deployment/web --timeout=180s
[ "$(image)" = nginx:1.27-alpine ] || fail "前のイメージに戻っていない"

say "7. ノードを空けても、Podは別のノードで動く"
kubectl drain cloudbook-worker2 --ignore-daemonsets --delete-emptydir-data --timeout=120s
kubectl -n cloudbook rollout status deployment/web --timeout=120s
kubectl -n cloudbook get pods -o wide
left=$(kubectl -n cloudbook get pods -l app=web --field-selector spec.nodeName=cloudbook-worker2 --no-headers 2>/dev/null | wc -l)
[ "$left" -eq 0 ] || fail "空けたノードにPodが残っている"
retry 60 ready_is 2 || fail "2つ動いていない"
kubectl uncordon cloudbook-worker2

say "8-1. 存在しないイメージ：新しいPodは起動できず、古いPodが応答を続ける"
kubectl -n cloudbook set image deployment/web web=nginx:0.0.0-none
retry 120 has_reason 'ErrImagePull|ImagePullBackOff' || fail "イメージの取得の失敗が表示されない"
kubectl -n cloudbook get pods
ready_is 2 || fail "古いPodが減っている"
[ "$(fetch | grep -c web-)" -ge 1 ] || fail "応答が止まった"
kubectl -n cloudbook rollout undo deployment/web
kubectl -n cloudbook rollout status deployment/web --timeout=180s

say "8-2. 通らないヘルスチェック：新しいPodは動いているが、通信は古いPodにだけ届く"
kubectl -n cloudbook patch deployment web --type=json -p '[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/healthz"}]'
retry 120 running_but_not_ready || fail "Running で READY でないPodが現れない"
sleep 15
kubectl -n cloudbook get pods
ready_is 2 || fail "古いPodが減っている"
endpoints=$(kubectl -n cloudbook get endpointslices -l kubernetes.io/service-name=web \
  -o jsonpath='{range .items[*].endpoints[*]}{.conditions.ready}{"\n"}{end}' | grep -c true || true)
[ "$endpoints" -eq 2 ] || fail "通信を受けられる宛先が2つでない（$endpoints）"
retry 60 probe_failed || fail "Podの詳細のイベントに、理由が出ていない"
kubectl -n cloudbook rollout undo deployment/web
kubectl -n cloudbook rollout status deployment/web --timeout=180s

say "8-3. すぐに終了するコマンド：新しいPodは再起動を繰り返す"
kubectl -n cloudbook patch deployment web --type=json -p '[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":["sh","-c","echo starting; exit 1"]}]'
retry 180 has_reason 'CrashLoopBackOff' || fail "CrashLoopBackOff にならない"
kubectl -n cloudbook get pods
crashed=$(kubectl -n cloudbook get pods -l app=web \
  -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[0].restartCount}{"\n"}{end}' | awk '$2 > 0 {print $1; exit}')
grep -q starting <<<"$(kubectl -n cloudbook logs "$crashed" --previous)" || fail "ログに出力が残っていない"
ready_is 2 || fail "古いPodが減っている"
kubectl -n cloudbook rollout undo deployment/web
kubectl -n cloudbook rollout status deployment/web --timeout=180s
retry 60 ready_is 2 || fail "元に戻らない"

say "9. 片付け"
kind delete cluster --name cloudbook
[ -z "$(kind get clusters 2>/dev/null)" ] || fail "クラスターが残っている"
echo
echo "すべての確認が通りました。"
