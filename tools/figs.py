"""All figures of the textbook. Each function returns a Fig; FIGS maps name -> svg string."""
from figlib import Fig

def bbox(f, x, y, w, h, n, label, kind='box', bold=False):
    f.box(x, y, w, h, kind=kind)
    f.badge(x + 18, y + h / 2, n)
    f.text(x + 34, y + h / 2 + 4.5, label, bold=bold)

# ---------------------------------------------------------------- 序章
def levels():
    f = Fig('levels', 760, 372, '基本・実践・設計・上級の4段階を、演習で確かめながら上がっていく')
    steps = [
        (24, 214, 170, 92, 'lv1', '第1部 基本編', ['クラウドの仕組みと', '用語がわかる']),
        (206, 160, 170, 146, 'lv2', '第2部 実践編', ['AWSで作って壊し、', '自分で直せる']),
        (388, 106, 170, 200, 'lv3', '第3部 設計編', ['要件から構成を決め、', '理由を説明できる']),
        (570, 52, 166, 254, 'lv4', '第4部 上級編', ['大規模・高信頼の', '設計と運用を担える']),
    ]
    for x, y, w, h, k, name, lines in steps:
        f.box(x, y, w, h, name, kind=k, lines=lines)
    f.text(38, 292, '第1〜9章', cls='fg-m')
    f.text(220, 292, '第10〜19章', cls='fg-m')
    f.text(402, 292, '第20〜26章', cls='fg-m')
    f.text(584, 292, '第27〜33章', cls='fg-m')
    f.box(24, 318, 712, 42, kind='lv5')
    f.text(38, 344, '第5部 ユースケースと演習（第34〜38章）', bold=True)
    f.text(722, 344, '各段階の力を、実務に近い題材で確かめる', cls='fg-s', anchor='end')
    f.text(24, 30, '到達レベル', cls='fg-m')
    f.arrow([(24, 196), (24, 44)])
    return f

# ---------------------------------------------------------------- 第2章
def stack4():
    f = Fig('stack4', 760, 376, '利用者の依頼がAPIで受け付けられ、仮想化層を通じて物理資源が割り当てられる')
    rows = [
        (12, 'box', '利用者（ここだけを操作する）', '管理画面・コマンド（CLI）・IaCツールから「サーバーを1台ほしい」と依頼する'),
        (108, 'acc', 'API・コントロールプレーン（事業者の管理システム）', '認証と権限チェック、空いている資源の割り当て、利用量の計測と課金'),
        (204, 'box', '仮想化層', 'ハイパーバイザーやコンテナ基盤が、1台の物理サーバーを複数の仮想サーバーに分割する'),
        (300, 'box', '物理層（データセンター）', '大量のサーバー・ストレージ・ネットワーク機器と、電源・空調・警備などの設備'),
    ]
    for y, k, name, body in rows:
        f.box(24, y, 712, 64, name, kind=k, lines=[body])
    for y, lab in [(76, 'API呼び出し'), (172, '割り当て指示'), (268, '物理資源を確保')]:
        f.arrow([(380, y), (380, y + 30)], label=lab, lpos=(394, y + 20))
    return f

def az():
    f = Fig('az', 760, 262, '1つのリージョンの中に、独立した複数のAZがあり、アプリを複数のAZに置く')
    f.box(24, 8, 712, 224, kind='zone')
    f.text(40, 34, 'リージョン（例：東京リージョン）', bold=True)
    for i, (x, name) in enumerate([(40, 'アベイラビリティゾーン A'), (272, 'アベイラビリティゾーン B'), (504, 'アベイラビリティゾーン C')]):
        f.box(x, 52, 216, 164, kind='box')
        f.text(x + 108, 76, name, anchor='middle', bold=True)
        for y in (88, 128):
            f.rect(x + 16, y, 184, 32, 'fg-soft', 6)
            f.text(x + 108, y + 20, 'データセンター', cls='fg-m', anchor='middle')
        if i < 2:
            f.rect(x + 16, 168, 184, 32, 'fg-acc', 6)
            f.text(x + 108, 189, f'アプリ（{i + 1}台目）', anchor='middle')
        else:
            f.rect(x + 16, 168, 184, 32, 'fg-dash', 6)
            f.text(x + 108, 188, '必要に応じて追加', cls='fg-m', anchor='middle')
    f.text(24, 252, 'AZ同士は物理的に離れた場所にあり、高速なネットワークで結ばれている', cls='fg-m')
    return f

# ---------------------------------------------------------------- 第3章
def resp():
    f = Fig('resp', 760, 344, '右のモデルほど事業者の担当が増えるが、データとアクセス権限は常に利用者の責任')
    cols = [(232, 'オンプレミス'), (360, 'IaaS'), (488, 'PaaS'), (616, 'SaaS')]
    rows = [('データ・アクセス権限', 'UUUU'), ('アプリケーション', 'UUUP'), ('ミドルウェア・実行環境', 'UUPP'),
            ('OS', 'UUPP'), ('仮想化', 'UPPP'), ('物理サーバー・ネットワーク', 'UPPP'), ('データセンター設備', 'UPPP')]
    for x, name in cols:
        f.text(x + 60, 26, name, anchor='middle', bold=True)
    for r, (name, who) in enumerate(rows):
        y = 40 + r * 38
        f.text(216, y + 20, name, anchor='end')
        for c, (x, _) in enumerate(cols):
            u = who[c] == 'U'
            f.rect(x, y, 120, 30, 'fg-me' if u else 'fg-them', 6)
            f.text(x + 60, y + 20, '利用者' if u else '事業者', cls='fg-s', anchor='middle')
    f.rect(232, 314, 18, 14, 'fg-me', 3)
    f.text(256, 326, '利用者が管理する', cls='fg-m')
    f.rect(392, 314, 18, 14, 'fg-them', 3)
    f.text(416, 326, '事業者が管理する', cls='fg-m')
    return f

# ---------------------------------------------------------------- 第4章
def share():
    f = Fig('share', 760, 344, 'AWSが首位を保ちながらシェアを下げ、Googleが伸ばしている（2024年4〜6月期から2026年7〜9月期）')
    X = lambda i: 64 + i * (536 / 9)
    Y = lambda v: 290 - v * 6
    for t in (0, 10, 20, 30, 40):
        f.line(64, Y(t), 600, Y(t), 'fg-grid')
        f.text(54, Y(t) + 4, f'{t}%', cls='fg-m', anchor='end')
    idx = [0, 4, 5, 7, 8, 9]
    labs = ['24年Q2', '25年Q2', '25年Q3', '26年Q1', '26年Q2', '26年Q3']
    for i, lab in zip(idx, labs):
        f.text(X(i), 312, lab, cls='fg-m', anchor='middle')
    series = [('AWS', 'fg-s1', [32, 30, 29, 28, 28, 26]),
              ('Microsoft', 'fg-s2', [23, 20, 20, 21, 20, 19]),
              ('Google', 'fg-s3', [12, 13, 13, 14, 15, 16])]
    for name, cls, vals in series:
        d = 'M' + ' L'.join(f'{X(i):.1f} {Y(v):.1f}' for i, v in zip(idx, vals))
        f.raw(f'<path d="{d}" class="fg-line {cls}"/>')
        for i, v, lab in zip(idx, vals, labs):
            f.raw(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4.5" class="fg-pt {cls}"/>')
            f.raw(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="13" class="fg-hit"><title>{name} {lab}：{v}%</title></circle>')
        f.text(X(0), Y(vals[0]) - 10, f'{vals[0]}%', cls='fg-m', anchor='middle')
        yl = Y(vals[-1]) + 4
        f.raw(f'<line x1="614" y1="{yl - 4:.1f}" x2="632" y2="{yl - 4:.1f}" class="fg-line {cls}"/>')
        f.text(638, yl, f'{name} {vals[-1]}%', bold=True)
    f.text(64, 336, 'Q1＝1〜3月期、Q2＝4〜6月期、Q3＝7〜9月期。横軸は四半期の間隔に合わせている', cls='fg-m')
    f.text(64, 24, '世界のクラウドインフラサービス市場のシェア（売上ベース、Synergy Research Group推計）', cls='fg-m')
    return f

# ---------------------------------------------------------------- 第6章
def vpc():
    f = Fig('vpc', 760, 452, 'インターネットからの入口はIGWだけで、プライベートサブネットはNAT経由で外へ出る')
    f.box(330, 12, 260, 36, 'インターネット（利用者・外部）')
    f.box(24, 64, 712, 348, kind='zone')
    f.text(40, 88, 'VPC（10.0.0.0/16）', bold=True)
    f.box(330, 76, 260, 38, 'インターネットゲートウェイ（IGW）', kind='acc', bold=True)
    for y, n1, cidr, rt in [(132, 'パブリック', '10.0.1.0/24', '0.0.0.0/0 → IGW'), (276, 'プライベート', '10.0.2.0/24', '0.0.0.0/0 → NAT')]:
        f.rect(40, y, 680, 120, 'fg-sub', 8)
        f.text(56, y + 24, n1, bold=True)
        f.text(56, y + 40, 'サブネット', bold=True)
        f.text(56, y + 58, cidr, cls='fg-mono')
        f.text(56, y + 78, 'ルートテーブル', cls='fg-m')
        f.text(56, y + 94, '10.0.0.0/16 → local', cls='fg-mono')
        f.text(56, y + 110, rt, cls='fg-mono')
    f.arrow([(420, 48), (420, 74)])
    f.arrow([(400, 114), (400, 164), (320, 164), (320, 182)])
    f.arrow([(320, 228), (320, 308)])
    f.arrow([(410, 332), (498, 332)])
    f.arrow([(380, 310), (380, 264), (560, 264), (560, 230)], dashed=True)
    f.arrow([(590, 184), (590, 164), (520, 164), (520, 116)], dashed=True)
    f.arrow([(500, 76), (500, 50)], dashed=True)
    f.box(230, 184, 180, 44, 'ロードバランサー（ALB）')
    f.box(500, 184, 180, 44, 'NATゲートウェイ（通用口）')
    f.box(230, 310, 180, 44, 'アプリサーバー（EC2）')
    f.box(500, 310, 180, 44, 'データベース（RDS）')
    f.line(24, 432, 56, 432, 'fg-ar')
    f.text(64, 436, '外から入る通信（Webアクセスなど）', cls='fg-m')
    f.line(380, 432, 412, 432, 'fg-ar fg-ard')
    f.text(420, 436, '中から外へ出る通信（更新プログラムの取得など）', cls='fg-m')
    return f

# ---------------------------------------------------------------- 第7章
def web3():
    f = Fig('web3', 760, 456, '利用者に見えるのは入口だけで、データベースは奥のプライベートサブネットに置く')
    f.box(24, 12, 200, 40, 'DNS（Route 53）')
    f.box(320, 12, 240, 40, '利用者（ブラウザ・スマホ）')
    f.box(310, 76, 260, 44, 'CDN（CloudFront）')
    f.box(144, 140, 592, 300, kind='zone')
    f.text(160, 162, 'VPC（東京リージョン）', bold=True)
    f.rect(160, 176, 272, 252, 'fg-dash', 8)
    f.text(172, 196, 'AZ-a', cls='fg-m')
    f.rect(448, 176, 272, 252, 'fg-dash', 8)
    f.text(708, 196, 'AZ-c', cls='fg-m', anchor='end')
    f.arrow([(320, 32), (226, 32)], dashed=True, label='①名前解決', lpos=(272, 24), anchor='middle')
    f.arrow([(440, 52), (440, 74)], label='②Web通信', lpos=(452, 68))
    f.arrow([(440, 120), (440, 206)])
    f.arrow([(390, 252), (390, 266), (296, 266), (296, 278)])
    f.arrow([(490, 252), (490, 266), (584, 266), (584, 278)])
    f.arrow([(296, 324), (296, 346)])
    f.arrow([(584, 324), (584, 336), (350, 336), (350, 346)])
    f.arrow([(396, 370), (482, 370)], label='同期複製', lpos=(440, 362), anchor='middle')
    f.box(310, 208, 260, 44, 'ロードバランサー（ALB）')
    f.box(196, 280, 200, 44, 'アプリサーバー（EC2）')
    f.box(484, 280, 200, 44, 'アプリサーバー（EC2）')
    f.box(196, 348, 200, 44, 'DBプライマリ（RDS）', kind='acc', bold=True)
    f.box(484, 348, 200, 44, 'DBスタンバイ（自動切替）')
    for y, a, b in [(226, 'パブリック', 'サブネット'), (298, 'プライベート', 'サブネット（アプリ）'), (366, 'プライベート', 'サブネット（DB）')]:
        f.text(24, y, a, cls='fg-m')
        f.text(24, y + 16, b, cls='fg-m')
    return f

# ---------------------------------------------------------------- 第11章
def buildmap():
    f = Fig('buildmap', 760, 520, '8つのステップで、1つのWebシステムを少しずつ組み上げる。円の数字は作るステップの番号')
    f.box(24, 20, 140, 40, '利用者')
    bbox(f, 220, 20, 200, 40, 1, 'CloudFront（CDN）')
    bbox(f, 476, 20, 176, 40, 1, 'S3（静的ファイル）')
    f.box(24, 76, 536, 364, kind='zone')
    f.text(40, 100, 'VPC（2つのAZにまたがる）', bold=True)
    f.badge(222, 95, 2)
    for y, a, b in [(116, 'パブリック', 'サブネット'), (220, 'プライベート', '（アプリ）'), (324, 'プライベート', '（DB）')]:
        f.rect(40, y, 504, 92, 'fg-sub', 8)
        f.text(56, y + 42, a, cls='fg-m')
        f.text(56, y + 58, b, cls='fg-m')
    f.arrow([(164, 40), (218, 40)])
    f.arrow([(420, 40), (474, 40)])
    f.arrow([(300, 60), (300, 136)], label='Webアクセス', lpos=(308, 100))
    f.arrow([(232, 182), (232, 242)])
    f.arrow([(312, 182), (312, 214), (400, 214), (400, 242)])
    f.arrow([(232, 288), (232, 346)])
    f.arrow([(400, 288), (400, 318), (320, 318), (320, 346)])
    f.arrow([(336, 370), (350, 370)])
    f.arrow([(480, 244), (480, 184)], dashed=True)
    f.arrow([(450, 138), (450, 64)], dashed=True, label='外部へ', lpos=(458, 100))
    bbox(f, 152, 138, 192, 44, 3, 'ロードバランサー（ALB）')
    bbox(f, 360, 138, 168, 44, 2, 'NATゲートウェイ')
    bbox(f, 152, 244, 184, 44, 3, 'アプリ（EC2・AZ-a）')
    bbox(f, 352, 244, 176, 44, 3, 'アプリ（EC2・AZ-c）')
    bbox(f, 152, 348, 184, 44, 4, 'RDS プライマリ')
    bbox(f, 352, 348, 176, 44, 4, 'RDS スタンバイ')
    f.rect(576, 76, 160, 364, 'fg-dash', 8)
    f.text(592, 100, 'VPCの外', bold=True)
    for y, n, name, items in [(116, 5, '監視と運用', ['CloudWatch', 'CloudTrail', 'SNS（通知）']),
                              (224, 6, 'サーバーレス', ['API Gateway', 'Lambda', 'DynamoDB']),
                              (332, 8, 'コンテナ', ['ECR', 'ECS（Fargate）'])]:
        f.box(592, y, 128, 92)
        f.badge(608, y + 20, n)
        f.text(624, y + 24.5, name, bold=True)
        for i, it in enumerate(items):
            f.text(608, y + 48 + i * 17, it, cls='fg-s')
    bbox(f, 24, 456, 348, 48, 7, 'IaC：ここまでの構成をコードで作り直す')
    bbox(f, 388, 456, 348, 48, 8, 'CI/CD：コードの変更を自動でデプロイ')
    return f

# ---------------------------------------------------------------- 第20章
def designflow():
    f = Fig('designflow', 760, 172, '構成案は複数出して比べ、決めた理由を記録する。合わなければ案に戻る')
    steps = [(26, '要件を聞く', ['機能と利用者数', '期限・予算を確認'], 'box'), (172, '数字にする', ['可用性・性能を', '目標値で表す'], 'box'),
             (318, '案を出す', ['構成案を2つ', '以上つくる'], 'box'), (464, '比べて決める', ['観点ごとに比べ', '理由を記録する'], 'acc'),
             (610, '見積もりと確認', ['料金を試算し', 'レビューを受ける'], 'box')]
    for x, name, lines, k in steps:
        f.box(x, 16, 124, 72, name, kind=k, lines=lines)
    for x in (150, 296, 442, 588):
        f.arrow([(x, 52), (x + 20, 52)])
    f.arrow([(672, 88), (672, 120), (380, 120), (380, 90)])
    f.text(526, 142, '予算や要件に合わなければ、案を見直す', cls='fg-m', anchor='middle')
    return f

# ---------------------------------------------------------------- 第3部・第4部
def dr4():
    f = Fig('dr4', 760, 236, 'DRの4つの戦略。右へ行くほど復旧は速くなり、平常時の費用は高くなる')
    items = [('バックアップ＆リストア', ['データだけを別の場所へ', '復旧時に環境から作る'], '数時間'),
             ('パイロットライト', ['データは常に複製', 'サーバーは止めておく'], '数十分'),
             ('ウォームスタンバイ', ['縮小した環境を', '常に動かしておく'], '数分'),
             ('マルチサイト', ['複数の拠点で常に', '本番の通信を受ける'], 'ほぼ0')]
    for i, (name, lines, rto) in enumerate(items):
        x = 24 + i * 182
        f.box(x, 16, 166, 84, name, kind='acc' if i == 3 else 'box', lines=lines)
        f.text(x + 83, 124, '復旧の目安：' + rto, cls='fg-s', anchor='middle')
    f.arrow([(24, 160), (736, 160)])
    f.text(24, 180, '復旧までの時間・失うデータ：大きい', cls='fg-m')
    f.text(736, 180, '小さい', cls='fg-m', anchor='end')
    f.arrow([(24, 206), (736, 206)])
    f.text(24, 226, '平常時の費用と運用の手間：小さい', cls='fg-m')
    f.text(736, 226, '大きい', cls='fg-m', anchor='end')
    return f

def iameval():
    f = Fig('iameval', 760, 330, '権限の判定の流れ（同じアカウント内の簡略図）。明示的な拒否が最優先で、どこにも許可がなければ拒否')
    qs = [(16, '1', 'どこかのポリシーに、明示的な拒否（Deny）があるか', 'ある'),
          (104, '2', '上限を決めるもの（SCP・RCP、アクセス許可の境界）の', 'ない'),
          (192, '3', '許可を与えるもの（IDベース・リソースベース）の', 'ない')]
    f.box(100, 16, 420, 56, kind='box')
    f.badge(122, 44, '1')
    f.text(142, 48.5, 'どこかのポリシーに、明示的な拒否（Deny）があるか')
    f.box(100, 104, 420, 56, kind='box')
    f.badge(122, 132, '2')
    f.text(142, 127, '上限を決めるもの（SCP・RCP、アクセス許可の境界）の')
    f.text(142, 145, 'すべてで許可されているか')
    f.box(100, 192, 420, 56, kind='box')
    f.badge(122, 220, '3')
    f.text(142, 215, '許可を与えるもの（IDベース・リソースベースのポリシー）の')
    f.text(142, 233, 'いずれかで許可されているか')
    for y, lab in [(72, 'ない'), (160, 'はい'), (248, 'はい')]:
        f.arrow([(310, y), (310, y + 32)], label=lab, lpos=(320, y + 21))
    for y, lab, sub in [(26, 'ある', '拒否（最優先）'), (114, 'いいえ', '拒否'), (202, 'いいえ', '拒否（暗黙の拒否）')]:
        f.arrow([(520, y + 18), (580, y + 18)], label=lab, lpos=(550, y + 10), anchor='middle')
        f.box(580, y, 156, 36, sub, kind='soft')
    f.box(210, 280, 200, 38, '許可', kind='acc', bold=True)
    return f

def reqpath():
    f = Fig('reqpath', 760, 250, 'リクエストの通り道と、負荷を減らす場所。入口に近いところで減らすほど効果が大きい')
    chain = [(24, '利用者', None), (170, 'CDN', ['静的ファイルを返す', '応答をキャッシュする']),
             (316, 'ロードバランサー', ['複数台に振り分ける', '異常な1台を外す']),
             (462, 'アプリ', ['状態を持たせず', '台数を増減する']), (608, 'データベース', ['読み取りを', 'レプリカへ逃がす'])]
    for x, name, notes in chain:
        f.box(x, 16, 128, 44, name, kind='acc' if name == 'CDN' else 'box', bold=True)
        if notes:
            for i, n in enumerate(notes):
                f.text(x + 64, 80 + i * 16, n, cls='fg-m', anchor='middle')
    for x in (152, 298, 444, 590):
        f.arrow([(x, 38), (x + 18, 38)])
    f.box(316, 190, 128, 44, 'キャッシュ', sub='よく読むデータ', kind='box')
    f.box(462, 190, 128, 44, 'キュー', sub='依頼をためる', kind='box')
    f.box(608, 190, 128, 44, 'ワーカー', sub='自分の速さで処理', kind='box')
    f.arrow([(506, 108), (506, 150), (396, 150), (396, 188)], dashed=True)
    f.arrow([(546, 108), (546, 188)], dashed=True)
    f.arrow([(590, 212), (606, 212)])
    f.text(556, 150, 'アプリから', cls='fg-m')
    f.text(24, 204, 'すぐに返さなくてよい処理は、', cls='fg-m')
    f.text(24, 222, 'キューに入れて後ろで処理する', cls='fg-m')
    return f

def org():
    f = Fig('org', 760, 318, '組織の中をOUで分け、OUごとに上限（SCP）を決める。アカウントは役割と環境ごとに分ける')
    f.box(280, 12, 200, 40, '組織のルート', kind='acc', bold=True)
    f.box(24, 12, 216, 40, '管理アカウント', sub='請求と組織の管理だけに使う', kind='soft')
    f.arrow([(240, 32), (278, 32)], head=False, dashed=True)
    ous = [(24, 'Security OU', ['ログ集約アカウント', '監査アカウント']),
           (206, 'Infrastructure OU', ['ネットワーク', '共通サービス']),
           (388, 'Workloads OU', ['本番（システムごと）', '検証・開発']),
           (570, 'Sandbox OU', ['個人の検証用', '（支出と権限を制限）'])]
    f.line(380, 52, 380, 76, 'fg-ar')
    f.line(107, 76, 653, 76, 'fg-ar')
    for x, name, accts in ous:
        f.line(x + 83, 76, x + 83, 96, 'fg-ar')
        f.box(x, 96, 166, 150, kind='zone')
        f.text(x + 83, 120, name, anchor='middle', bold=True)
        for i, a in enumerate(accts):
            f.rect(x + 12, 134 + i * 52, 142, 40, 'fg-box', 6)
            f.text(x + 83, 159 + i * 52, a, cls='fg-s', anchor='middle')
    f.text(24, 276, 'SCPはOUに付け、配下のアカウントで「できることの上限」を決める。権限を与えるものではない', cls='fg-m')
    f.text(24, 296, '基盤のOU（SecurityとInfrastructure）を先に作り、その上に業務システムのアカウントを載せる', cls='fg-m')
    return f

def tgw():
    f = Fig('tgw', 760, 300, 'ハブ・アンド・スポーク構成。VPCと社内の接続を中央のTransit Gatewayに集め、経路を一か所で管理する')
    f.box(300, 118, 160, 60, 'Transit Gateway', sub='経路を集中管理', kind='acc', bold=True)
    f.box(24, 118, 170, 60, 'オンプレミス', sub='社内ネットワーク', kind='box', bold=True)
    f.arrow([(194, 148), (298, 148)], both=True, label='専用線・VPN', lpos=(246, 138), anchor='middle')
    for y, name in [(24, 'VPC 本番A'), (118, 'VPC 本番B'), (212, 'VPC 検証')]:
        f.box(566, y, 170, 60 if y == 118 else 56, name, kind='box')
    f.arrow([(460, 138), (510, 138), (510, 52), (564, 52)], both=True)
    f.arrow([(460, 148), (564, 148)], both=True)
    f.arrow([(460, 158), (510, 158), (510, 240), (564, 240)], both=True)
    f.box(290, 20, 180, 52, 'VPC 共通サービス', sub='認証、DNS、監視など', kind='box')
    f.arrow([(380, 72), (380, 116)], both=True)
    f.box(270, 224, 220, 52, 'VPC 出口と検査', sub='NAT、ファイアウォール', kind='box')
    f.arrow([(380, 178), (380, 222)], both=True)
    f.arrow([(270, 250), (200, 250)])
    f.text(190, 254, 'インターネット', anchor='end')
    return f

def deploy():
    f = Fig('deploy', 760, 300, '3つのデプロイ方式。四角1つがサーバー（またはタスク）1つ。色の付いた四角が新しい版')
    def group(x, y, pat, note):
        for i, c in enumerate(pat):
            if c == ' ':
                continue
            f.rect(x + i * 15, y + 2, 12, 14, 'fg-acc' if c == 'N' else 'fg-soft', 3)
        f.text(x, y + 38, note, cls='fg-m')
    rows = [(20, 'ローリング', '少しずつ入れ替える', [('OOOO', '開始'), ('NNOO', '新旧が混ざる'), ('NNNN', '完了')]),
            (112, 'ブルー/グリーン', '新しい環境を並べて切り替える', [('OOOO NNNN', '新を用意して確認'), ('OOOO NNNN', '通信を新へ切替'), ('     NNNN', '旧を片付ける')]),
            (204, 'カナリア', '一部の通信だけ先に流す', [('OOOO N', '新に10%だけ流す'), ('OOOO NNNN', '問題なければ全量'), ('     NNNN', '旧を片付ける')])]
    for y, name, sub, steps in rows:
        f.text(24, y + 14, name, bold=True)
        f.text(24, y + 32, sub, cls='fg-m')
        for i, (pat, note) in enumerate(steps):
            group(220 + i * 184, y, pat, note)
            if i < 2:
                f.arrow([(220 + i * 184 + 146, y + 9), (220 + i * 184 + 174, y + 9)])
        if y < 200:
            f.line(24, y + 68, 736, y + 68)
    f.rect(24, 276, 14, 14, 'fg-soft', 3)
    f.text(44, 288, '今の版', cls='fg-m')
    f.rect(104, 276, 14, 14, 'fg-acc', 3)
    f.text(124, 288, '新しい版', cls='fg-m')
    return f

def rag():
    f = Fig('rag', 760, 262, 'RAGの流れ。上段は事前の準備、下段は質問のたびに行う処理。回答は取り出した文書を根拠に作る')
    f.text(24, 22, '準備（文書が増えるたびに）', cls='fg-m')
    top = [(24, '社内文書', 'S3などに置く'), (268, '分割してベクトル化', '意味の近さを数値にする'), (540, 'ベクトルストア', '検索用に保存する')]
    for x, name, sub in top:
        f.box(x, 34, 196, 56, name, sub=sub, kind='box', bold=True)
    f.arrow([(220, 62), (266, 62)])
    f.arrow([(464, 62), (538, 62)])
    f.line(24, 116, 736, 116)
    f.text(24, 140, '回答（質問のたびに）', cls='fg-m')
    bot = [(24, 150, '利用者の質問', None, 'box'), (196, 150, '検索', '関連する断片を取り出す', 'box'),
           (392, 150, '生成AIモデル', '質問と断片を渡す', 'acc'), (588, 150, '回答', '出典を添える', 'box')]
    for x, w, name, sub, k in bot:
        f.box(x, 158, w - 4 if False else 148, 56, name, sub=sub, kind=k, bold=True)
    f.arrow([(172, 186), (194, 186)])
    f.arrow([(344, 186), (390, 186)])
    f.arrow([(540, 186), (586, 186)])
    f.arrow([(638, 90), (638, 104), (270, 104), (270, 156)], dashed=True)
    f.text(24, 244, '権限のない文書が検索結果に混ざらないよう、検索の段階で利用者ごとに絞り込む', cls='fg-m')
    return f

def pipeline():
    f = Fig('pipeline', 760, 190, 'イベント駆動の処理。キューを挟むことで、失敗したものをやり直せ、処理の速さも調整できる')
    chain = [(24, 'S3（元画像）', '利用者が直接置く'), (212, 'SQS（キュー）', '通知をためる'), (400, 'Lambda', 'サムネイルを作る'), (588, 'S3（保存先）', '別のバケット')]
    for x, name, sub in chain:
        f.box(x, 20, 148, 56, name, sub=sub, kind='acc' if name == 'Lambda' else 'box', bold=True)
    for x in (172, 360, 548):
        f.arrow([(x, 48), (x + 38, 48)])
    f.box(212, 116, 148, 52, 'デッドレターキュー', sub='失敗が続いたもの', kind='soft')
    f.arrow([(286, 76), (286, 114)], dashed=True)
    f.text(400, 138, '後から原因を調べ、', cls='fg-m')
    f.text(400, 156, '直してから元のキューに戻して再処理する', cls='fg-m')
    return f

FIG_FUNCS = [levels, stack4, az, resp, share, vpc, web3, buildmap, designflow, dr4, iameval, reqpath, org, tgw, deploy, rag, pipeline]

def all_figs():
    out = {}
    for fn in FIG_FUNCS:
        f = fn()
        out[f.name] = f.svg()
    return out
