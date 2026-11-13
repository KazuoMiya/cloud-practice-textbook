-- 旧環境に入っている、受注のデータ。何度作り直しても、同じ内容になる
create table customers (
  id   serial primary key,
  name text not null
);

create table orders (
  id          serial primary key,
  customer_id integer not null references customers (id),
  amount      integer not null check (amount > 0),
  ordered_at  timestamptz not null default now()
);

create index orders_customer_id_idx on orders (customer_id);

create view customer_totals as
  select c.id, c.name, count(o.id) as orders, coalesce(sum(o.amount), 0) as total
  from customers c left join orders o on o.customer_id = c.id
  group by c.id, c.name;

insert into customers (name)
  select '顧客' || n from generate_series(1, 50) as n;

insert into orders (customer_id, amount, ordered_at)
  select 1 + (n % 50), 500 + (n * 37) % 9500, timestamptz '2026-01-01 00:00:00+09' + n * interval '7 minutes'
  from generate_series(1, 2000) as n;
