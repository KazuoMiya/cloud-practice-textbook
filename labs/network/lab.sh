#!/bin/bash
# 第28章の実習で使う、手元のネットワークを組み立てる。実習用のコンテナの中で実行する。
#
#   lab static         静的な経路で学ぶ構成を作り直す（経路の一部は、わざと入れていない）
#   lab bgp            回線を2本にして、経路をBGPで交換する構成を作り直す
#   lab cut wan1       回線を切る。両端の機器には、切れたことが伝わらない
#   lab restore wan1   回線を戻す
#   lab down           すべて消す
#
# 機器1台を、ネットワーク名前空間1つで表す。機器どうしは、仮想のケーブル（veth）と
# 仮想のスイッチ（ブリッジ）でつなぐ。機器の中でコマンドを実行するには、機器の名前を
# 先頭に付ける。例： pc ping 10.210.1.10
set -euo pipefail

FORWARD=/etc/dnsmasq-office.forward
port=0

node() { # node <機器の名前> <host|router>
  ip netns add "$1"
  ip netns exec "$1" ip link set dev lo up
  # 送信元の検査（rp_filter）は止める。経路がないときの動きを、経路表だけで説明できるようにする
  ip netns exec "$1" sysctl -q -w net.ipv4.conf.all.rp_filter=0 net.ipv4.conf.default.rp_filter=0
  if [ "$2" = router ]; then
    # 転送する。「行き先がない」などの通知は、間引かずに毎回返す。「別の出口を使え」という通知は出さない
    ip netns exec "$1" sysctl -q -w net.ipv4.ip_forward=1 net.ipv4.icmp_ratelimit=0 \
      net.ipv4.conf.all.send_redirects=0 net.ipv4.conf.default.send_redirects=0
  else
    ip netns exec "$1" sysctl -q -w net.ipv4.ip_forward=0
  fi
}

segment() { # segment <名前>：機器をつなぐスイッチを1つ作る
  ip link add "sw-$1" type bridge
  ip link set dev "sw-$1" up
}

plug() { # plug <機器> <インターフェースの名前> <アドレス/長さ> <つなぐ先のスイッチ>
  port=$((port + 1))
  ip link add "port$port" type veth peer name "$2" netns "$1"
  ip link set dev "port$port" master "sw-$4"
  ip link set dev "port$port" up
  ip netns exec "$1" ip addr add "$3" dev "$2"
  ip netns exec "$1" ip link set dev "$2" up
}

web() { # web <機器>：名前を返すだけのWebサーバーを動かす
  mkdir -p "/www/$1"
  echo "$1" > "/www/$1/index.html"
  ip netns exec "$1" httpd -p 80 -h "/www/$1"
}

dns() { # dns <機器> <dnsmasqへの追加の指定...>：DNSサーバーを動かす
  local name=$1
  shift
  : > "/var/log/$name.log"
  ip netns exec "$name" dnsmasq --conf-file=/dev/null --no-resolv --no-hosts --user=root \
    --pid-file="/run/$name.pid" --log-queries --log-facility="/var/log/$name.log" "$@"
}

down() {
  local ns sw
  for ns in $(ip netns list | awk '{print $1}'); do
    if [ -d "/etc/frr/$ns" ]; then /usr/lib/frr/frrinit.sh stop "$ns" > /dev/null 2>&1 || true; fi
    ip netns pids "$ns" | xargs -r kill 2> /dev/null || true
    ip netns delete "$ns"
  done
  for sw in $(ip -o link show type bridge | awk -F': ' '{print $2}'); do ip link delete dev "$sw"; done
  rm -f /run/dns-office.pid /run/dns-cloud.pid
  : > "$FORWARD"
  port=0
}

office() { # 社内：端末、DNSサーバー、ルーター。端末とDNSサーバーは、ルーターを既定の出口にする
  segment office
  node pc host
  node dns-office host
  node router-office router
  plug pc eth0 192.168.210.10/24 office
  plug dns-office eth0 192.168.210.53/24 office
  plug router-office lan 192.168.210.254/24 office
  ip netns exec pc ip route add default via 192.168.210.254
  ip netns exec dns-office ip route add default via 192.168.210.254
  mkdir -p /etc/netns/pc
  echo 'nameserver 192.168.210.53' > /etc/netns/pc/resolv.conf
  # corp.internal の名前は、このサーバーが答える。ほかの名前の聞き先は、転送の設定（$FORWARD）で決まる
  dns dns-office --local=/corp.internal/ --host-record=files.corp.internal,192.168.210.20 \
    --servers-file="$FORWARD"
}

static() {
  down
  office
  segment wan1
  segment prod
  segment dev
  node hub router
  node web-prod host
  node dns-cloud host
  node web-dev host
  plug router-office wan1 192.168.255.1/30 wan1
  plug hub wan1 192.168.255.2/30 wan1
  plug hub to-prod 10.210.1.254/24 prod
  plug hub to-dev 10.210.2.254/24 dev
  plug web-prod eth0 10.210.1.10/24 prod
  plug dns-cloud eth0 10.210.1.53/24 prod
  plug web-dev eth0 10.210.2.10/24 dev
  # わざと入れていない経路：router-office からクラウドへ、hub から社内へ、web-prod から外へ
  ip netns exec dns-cloud ip route add default via 10.210.1.254
  ip netns exec web-dev ip route add default via 10.210.2.254
  web web-prod
  web web-dev
  dns dns-cloud --local=/cloud.internal/ --host-record=web.prod.cloud.internal,10.210.1.10 \
    --host-record=web.dev.cloud.internal,10.210.2.10
  echo '静的な経路で学ぶ構成を作りました。機器： pc dns-office router-office hub web-prod dns-cloud web-dev'
}

bgp() {
  down
  office
  segment wan1
  segment wan2
  segment prod
  node hub router
  node web-prod host
  plug router-office wan1 192.168.255.1/30 wan1
  plug hub wan1 192.168.255.2/30 wan1
  plug router-office wan2 192.168.255.5/30 wan2
  plug hub wan2 192.168.255.6/30 wan2
  plug hub to-prod 10.210.1.254/24 prod
  plug web-prod eth0 10.210.1.10/24 prod
  ip netns exec web-prod ip route add default via 10.210.1.254
  web web-prod
  # 2台のルーターで、経路を交換するソフトウェア（FRR）を動かす。設定は /etc/frr/<機器の名前>/frr.conf
  /usr/lib/frr/frrinit.sh start router-office
  /usr/lib/frr/frrinit.sh start hub
  echo '回線2本とBGPの構成を作りました。機器： pc dns-office router-office hub web-prod'
}

link_state() { # link_state <wan1|wan2> <up|down>
  case "$1" in
    wan1 | wan2) ip link set dev "sw-$1" "$2" ;;
    *)
      echo "回線の名前は wan1 か wan2 です" >&2
      exit 1
      ;;
  esac
}

case "${1:-}" in
  static) static ;;
  bgp) bgp ;;
  cut)
    link_state "${2:-}" down
    echo "$2 を切りました"
    ;;
  restore)
    link_state "${2:-}" up
    echo "$2 を戻しました"
    ;;
  down) down ;;
  *)
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
