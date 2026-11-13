#!/usr/bin/env bash
# 第28章「手元で通す：社内とクラウドをつなぐ」を、最初から最後まで自動で通して確かめる。
# 使い方：Docker を入れた端末で、 bash labs/network/verify.sh
# 実習用のコンテナを作り、終わったら（途中で失敗しても）消す。
set -euo pipefail
cd "$(dirname "$0")"

say() { printf '\n== %s\n' "$*"; }
fail() {
  echo "FAIL: $*" >&2
  echo "--- 調査用の情報" >&2
  docker compose ps -a >&2 || true
  docker compose exec -T lab sh -c 'ip netns list; ps; tail -n 40 /var/log/frr/*.log /var/log/dns-*.log 2>/dev/null' >&2 || true
  exit 1
}
cleanup() { docker compose down -v >/dev/null 2>&1 || true; }
trap cleanup EXIT

# 実習用のコンテナの中で、コマンドを実行する。本文のコマンドは、この後ろに書いたものと同じ
run() { docker compose exec -T lab "$@"; }
# 失敗するのが正しいコマンドの出力を受け取る
try() { run "$@" 2>&1 || true; }
retry() { # retry <回数> <コマンド...>：成功するまで、1秒おきに繰り返す
  local n=$1 i
  shift
  for ((i = 0; i < n; i++)); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  return 1
}
# 機器のインターフェースを通るICMPを、指定した秒数だけ記録する
capture() { run "$1" timeout "$3" tcpdump -lnpi "$2" icmp 2>/dev/null || true; }
page() { try "$1" curl -s -m 3 "$2"; }

say "1. 実習用のコンテナを立て、静的な経路で学ぶ構成を作る"
docker compose up -d --build
run lab static
run hub ip -br addr
run pc ip route
run router-office ip route

say "2. 最初は届かない：社内のルーターが、行き先を知らない"
out=$(try pc ping -c 2 -W 1 10.210.1.10)
echo "$out"
grep -q 'From 192.168.210.254 .*Destination Net Unreachable' <<<"$out" || fail "社内のルーターが「行き先がない」と返さない"

say "3. 行きの経路を足す：届くが、返事が戻らない"
run router-office ip route add 10.210.0.0/16 via 192.168.255.2
cap=$(mktemp)
capture web-prod eth0 5 >"$cap" &
sleep 1
out=$(try pc ping -c 2 -W 1 10.210.1.10)
wait
echo "$out"
cat "$cap"
grep -q '100% packet loss' <<<"$out" || fail "行きの経路だけで、応答が返ってしまった"
grep -q '192.168.210.10 > 10.210.1.10: ICMP echo request' "$cap" || fail "web-prod に、依頼が届いていない"
if grep -q 'ICMP echo reply' "$cap"; then fail "web-prod が、経路がないのに返事を出している"; fi

say "4. サーバーに戻りの経路を足す：返事は出るが、中継点で止まる"
run web-prod ip route add default via 10.210.1.254
capture hub to-prod 5 >"$cap" &
sleep 1
out=$(try pc ping -c 2 -W 1 10.210.1.10)
wait
echo "$out"
cat "$cap"
grep -q '100% packet loss' <<<"$out" || fail "中継点に戻りの経路がないのに、応答が返ってしまった"
grep -q '10.210.1.10 > 192.168.210.10: ICMP echo reply' "$cap" || fail "web-prod の返事が、中継点に届いていない"
grep -q 'unreachable' "$cap" || fail "中継点が「行き先がない」と返していない"

say "5. 中継点にも戻りの経路を足す：つながる"
run hub ip route add 192.168.210.0/24 via 192.168.255.1
run pc ping -c 2 -W 1 10.210.1.10 || fail "行きと戻りの経路がそろったのに、届かない"
[ "$(page pc http://10.210.1.10/)" = web-prod ] || fail "社内から、本番のサーバーのページを取得できない"
[ "$(page pc http://10.210.2.10/)" = web-dev ] || fail "社内から、検証のサーバーのページを取得できない"

say "6. つないだだけでは、本番と検証も通信できてしまう"
[ "$(page web-prod http://10.210.2.10/)" = web-dev ] || fail "分ける前なのに、本番から検証へ届かない"

say "7. 中継点の経路表を分けて、本番と検証をつながない"
run hub ip route add 192.168.210.0/24 via 192.168.255.1 table 101
run hub ip route add blackhole default table 101
run hub ip rule add iif to-prod lookup 101
run hub ip route add 192.168.210.0/24 via 192.168.255.1 table 102
run hub ip route add blackhole default table 102
run hub ip rule add iif to-dev lookup 102
run hub ip rule
run hub ip route show table 101
[ -z "$(page web-prod http://10.210.2.10/)" ] || fail "経路表を分けたのに、本番から検証へ届く"
[ -z "$(page web-dev http://10.210.1.10/)" ] || fail "経路表を分けたのに、検証から本番へ届く"
[ "$(page pc http://10.210.1.10/)" = web-prod ] || fail "経路表を分けたら、社内から本番へ届かなくなった"
[ "$(page pc http://10.210.2.10/)" = web-dev ] || fail "経路表を分けたら、社内から検証へ届かなくなった"
run web-dev ping -c 1 -W 1 192.168.210.10 || fail "経路表を分けたら、検証から社内へ届かなくなった"
echo "社内からは両方に届き、本番と検証の間は届かない（期待どおり）"

say "8. 細かい経路が勝つ：1台分の経路を足すと、その1台へ届かなくなる"
run hub ip route add 10.210.1.10/32 via 192.168.255.1
out=$(try pc ping -c 2 -W 1 10.210.1.10)
echo "$out"
grep -q 'Time to live exceeded' <<<"$out" || fail "経路が輪になったときの表示が出ない"
run hub ip route del 10.210.1.10/32
run pc ping -c 2 -W 1 10.210.1.10 || fail "細かい経路を消したのに、届かない"

say "9. 経路はあるのに、名前で届かない"
out=$(try pc nslookup web.prod.cloud.internal)
echo "$out"
if grep -q '10\.210\.1\.10' <<<"$out"; then fail "転送の設定をする前に、社内のDNSサーバーがクラウドの名前を答えた"; fi
out=$(try pc nslookup web.prod.cloud.internal 10.210.1.53)
echo "$out"
grep -q '10\.210\.1\.10' <<<"$out" || fail "クラウド側のDNSサーバーが、名前を答えない"

say "10. 社内のDNSサーバーに、転送の設定を足す"
run sh -c "echo 'server=/cloud.internal/10.210.1.53' > /etc/dnsmasq-office.forward"
run sh -c 'kill -HUP "$(cat /run/dns-office.pid)"'
sleep 1
run pc nslookup web.prod.cloud.internal | tee "$cap"
grep -q '10\.210\.1\.10' "$cap" || fail "転送の設定をしたのに、社内のDNSサーバーがクラウドの名前を答えない"
[ "$(try pc curl -s -m 5 http://web.prod.cloud.internal/)" = web-prod ] || fail "名前で、本番のサーバーのページを取得できない"
run grep forwarded /var/log/dns-office.log || fail "社内のDNSサーバーの記録に、転送が残っていない"

say "11. 回線を2本にして、経路をBGPで交換する"
run lab bgp
established() { run router-office ip route show 10.210.1.0/24 | grep -q 'via 192.168.255.2 .*proto bgp' && run hub ip route show 192.168.210.0/24 | grep -q 'via 192.168.255.1 .*proto bgp'; }
both_paths() { [ "$(run vtysh -N router-office -c 'show ip bgp 10.210.1.0/24' | grep -c '^  *192\.168\.255\.[26] from')" = 2 ]; }
retry 60 established || fail "BGPで受け取った経路が、wan1 を通る形で入らない"
retry 30 both_paths || fail "router-office が、2本の回線の両方から経路を受け取っていない"
best_is_wan1() { run vtysh -N router-office -c 'show ip bgp 10.210.1.0/24' | grep -A1 '192\.168\.255\.2 from' | grep -q 'localpref 200.*best'; }
retry 30 best_is_wan1 || fail "router-office が、wan1 からの経路を最良に選んでいない"
run vtysh -N router-office -c 'show bgp summary'
run vtysh -N router-office -c 'show ip bgp'
run router-office ip route
[ "$(page pc http://10.210.1.10/)" = web-prod ] || fail "BGPの構成で、社内から本番のサーバーに届かない"

say "12. 通信を続けながら wan1 を切る：しばらく途切れてから、wan2 に切り替わる"
run pc ping -i 0.2 -c 60 -W 1 10.210.1.10 >"$cap" &
sleep 3
run lab cut wan1
wait || true
tail -n 3 "$cap"
received=$(sed -n 's/.* \([0-9][0-9]*\) received.*/\1/p' "$cap")
[ -n "$received" ] || fail "ping の結果を読み取れない"
lost=$((60 - received))
[ "$lost" -gt 0 ] || fail "回線を切ったのに、1つも失われていない"
[ "$lost" -lt 40 ] || fail "回線を切った後、wan2 に切り替わっていない（60回のうち ${lost}回が失われた）"
run router-office ip route show 10.210.1.0/24 | grep -q 'via 192.168.255.6 ' || fail "切り替わった後の経路が、wan2 を通っていない"
run vtysh -N router-office -c 'show bgp summary'
run pc ping -c 2 -W 1 10.210.1.10 || fail "wan2 に切り替わった後、届かない"
echo "60回のうち ${lost}回が失われた（0.2秒おきなので、途切れたのは約 $((lost / 5)) 秒）"

say "13. wan1 を戻す：自動で、元の経路に戻る"
run lab restore wan1
retry 90 established || fail "回線を戻したのに、wan1 を通る経路に戻らない"
run router-office ip route show 10.210.1.0/24
run pc ping -c 2 -W 1 10.210.1.10 || fail "元の経路に戻った後、届かない"

say "14. 片付け"
docker compose down -v
[ -z "$(docker compose ps -aq)" ] || fail "コンテナが残っている"
echo
echo "PASS: 第28章の実習を、最後まで確かめました"
