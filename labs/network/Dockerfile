# 第28章の実習で使う道具をまとめたイメージ。
#   iproute2（ip）、ping、tcpdump、curl、nslookup、dnsmasq（DNSサーバー）、
#   busybox の httpd（Webサーバー）、FRR（経路を交換するソフトウェア）
FROM alpine:3.22
RUN apk add --no-cache bash bind-tools busybox-extras curl dnsmasq frr iproute2 iputils tcpdump \
 && mkdir -p /var/log/frr /lib/frr /www /etc/netns \
 && chown frr:frr /var/log/frr /lib/frr
COPY lab.sh /usr/local/bin/lab
COPY frr/ /etc/frr/
# 機器の名前のコマンドを用意する。 pc ping ... は、機器 pc の中で ping ... を実行する
RUN chmod 755 /usr/local/bin/lab \
 && chown -R frr:frr /etc/frr \
 && touch /etc/dnsmasq-office.forward \
 && for n in pc dns-office router-office hub web-prod web-dev dns-cloud; do \
      printf '#!/bin/sh\nexec ip netns exec %s "$@"\n' "$n" > "/usr/local/bin/$n" \
      && chmod 755 "/usr/local/bin/$n"; \
    done
CMD ["sleep", "infinity"]
