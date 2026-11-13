data "aws_availability_zones" "available" {
  state = "available"

  # Local Zone など、別に申し込みが要る場所は除く
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# アドレス設計。第13章の表と同じ内容を、1か所にまとめて書く
locals {
  # 使えるAZのうち、先頭の2つを使う（東京リージョンでは 1a と 1c になることが多い）
  azs = slice(data.aws_availability_zones.available.names, 0, 2)

  subnets = {
    public-a = { tier = "public", az = local.azs[0], cidr = "10.0.0.0/24" }
    public-c = { tier = "public", az = local.azs[1], cidr = "10.0.1.0/24" }
    app-a    = { tier = "app", az = local.azs[0], cidr = "10.0.10.0/24" }
    app-c    = { tier = "app", az = local.azs[1], cidr = "10.0.11.0/24" }
    db-a     = { tier = "db", az = local.azs[0], cidr = "10.0.20.0/24" }
    db-c     = { tier = "db", az = local.azs[1], cidr = "10.0.21.0/24" }
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name}-vpc"
  }
}

# 表の1行が、サブネット1つになる
resource "aws_subnet" "this" {
  for_each = local.subnets

  vpc_id            = aws_vpc.main.id
  availability_zone = each.value.az
  cidr_block        = each.value.cidr

  tags = {
    Name = "${local.name}-${each.key}"
    Tier = each.value.tier
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name}-igw"
  }
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${local.name}-nat"
  }
}

# NATゲートウェイは、パブリックサブネットに置く。置いてある間、時間料金がかかる
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.this["public-a"].id

  tags = {
    Name = "${local.name}-nat"
  }

  # インターネットゲートウェイが付く前に作ると、外へ出られない
  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name}-public"
  }
}

resource "aws_route_table" "app" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "${local.name}-app"
  }
}

# DB用は、外部への経路を持たない。空であることを明示し、手で足された経路を差分として検出する
resource "aws_route_table" "db" {
  vpc_id = aws_vpc.main.id
  route  = []

  tags = {
    Name = "${local.name}-db"
  }
}

locals {
  route_table_ids = {
    public = aws_route_table.public.id
    app    = aws_route_table.app.id
    db     = aws_route_table.db.id
  }
}

# 関連付けを忘れたサブネットは、メインルートテーブルに従ってしまう。6つすべてを関連付ける
resource "aws_route_table_association" "this" {
  for_each = local.subnets

  subnet_id      = aws_subnet.this[each.key].id
  route_table_id = local.route_table_ids[each.value.tier]
}
