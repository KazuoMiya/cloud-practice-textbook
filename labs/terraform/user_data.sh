#!/bin/bash
dnf install -y nginx
echo "<h1>$(hostname)</h1>" > /usr/share/nginx/html/index.html
systemctl enable --now nginx
