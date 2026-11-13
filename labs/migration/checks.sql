-- 切り替えの判断に使う値。旧環境と新環境で実行し、出力が一致することを確かめる
select 1 as no, 'customers の件数' as item, count(*)::text as value from customers
union all select 2, 'orders の件数', count(*)::text from orders
union all select 3, 'orders の金額の合計', sum(amount)::text from orders
union all select 4, 'orders の最大のID', max(id)::text from orders
union all select 5, 'orders のIDの採番の現在値', last_value::text from orders_id_seq
union all select 6, '顧客ごとの集計（ビュー）の件数', count(*)::text from customer_totals
order by no;
