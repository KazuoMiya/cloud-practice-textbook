:::goal
- 主要3社の位置づけと、それぞれが選ばれやすい場面を説明できる
- 同じ役割のサービスを、AWS・Azure・Google Cloud の名前で言い換えられる
- 市場シェアの数字を、定義と時点に注意して読める
:::

世界のクラウドインフラサービス市場（IaaS・PaaS・ホスティング型プライベートクラウド）は、AWS・Microsoft Azure・Google Cloud の3社で約6割を占めます。まずこの3社の位置づけと、サービス名の対応を押さえれば、ほとんどの案件の会話についていけます。

## 市場シェア

{{fig:share|クラウドインフラサービス市場のシェアの推移（Synergy Research Group の四半期推計）。3社の差は縮まる傾向にある}}

| 時点 | AWS | Microsoft | Google |
|---|---|---|---|
| 2024年4〜6月期 | 32% | 23% | 12% |
| 2025年4〜6月期 | 30% | 20% | 13% |
| 2025年7〜9月期 | 29% | 20% | 13% |
| 2026年1〜3月期 | 28% | 21% | 14% |
| 2026年4〜6月期 | 28% | 20% | 15% |
| 2026年7〜9月期 | 26% | 19% | 16% |

Synergy Research Group の推計では、2026年7〜9月期のクラウドインフラサービス市場は約1,677億ドルで、前年同期比55%増でした。直近12か月の合計は約5,580億ドルです。成長を押し上げているのは生成AIの需要で、AI関連のサービスが市場のおよそ3分の1を占めるとされています（[TechInsights](https://www.techinsights.com/node/61958)、2026年10月）。

AWSのシェア低下は売上の減少ではなく、市場全体の伸びがAWSの伸びを上回ったためです。調査会社によって市場の定義が異なり、数字は変わります。シェアの数字を引用するときは、「どの調査会社の」「どの範囲の市場の」「いつの時点の」数字かを必ず添えてください。

## 各社の特徴

| ベンダー | 強み | よく使われる場面 |
|---|---|---|
| AWS（Amazon Web Services） | 2006年開始の先行者。サービスの種類が最も多く、技術者・情報・パートナー企業が豊富 | Webサービス、スタートアップ、基幹システム移行、日本の官公庁 |
| Microsoft Azure | Microsoft 365・Entra ID・Windows Serverなど既存のMicrosoft製品との親和性。オンプレミスとの併用に強い | Microsoft製品中心の大企業、.NETアプリ、ハイブリッド構成 |
| Google Cloud | BigQueryに代表されるデータ分析、Kubernetes発祥のコンテナ技術、Geminiと独自AIチップ | データ分析基盤、AI開発、Google Workspace利用企業 |
| Oracle Cloud Infrastructure（OCI） | Oracle Databaseを動かすのに最適化 | Oracle DBを使う基幹システム、自治体 |
| さくらのクラウド | 国産のIaaS。データを国内事業者に置ける | 国内法人、官公庁 |

日本政府が使う「ガバメントクラウド」には2026年6月時点で上記5サービスが認定されており、さくらのクラウドは国内事業者で唯一、2026年3月に正式認定されました。利用実績ではAWSが大きな割合を占めていると報じられています（[ITmedia](https://www.itmedia.co.jp/business/articles/2606/17/news021.html)）。

## サービス名の対応表

同じ役割のサービスでも、会社ごとに名前が違います。案件で知らない名前が出てきたら、次の2つの表で「どの役割か」を確認してください。表は「コンピュート・ストレージ・DB」と「ネットワーク・運用・データ活用」に分けています。

| 役割（コンピュート・ストレージ・DB） | AWS | Azure | Google Cloud |
|---|---|---|---|
| 仮想サーバー | EC2 | Virtual Machines | Compute Engine |
| オブジェクトストレージ | S3 | Blob Storage | Cloud Storage |
| サーバー用ディスク | EBS | Managed Disks | Persistent Disk |
| リレーショナルDB | RDS、Aurora | Azure SQL Database | Cloud SQL、AlloyDB |
| NoSQL DB | DynamoDB | Cosmos DB | Firestore、Bigtable |
| サーバーレス関数 | Lambda | Azure Functions | Cloud Run functions |
| コンテナ実行 | ECS、Fargate | Container Apps | Cloud Run |
| Kubernetes | EKS | AKS | GKE |

| 役割（ネットワーク・運用・データ活用） | AWS | Azure | Google Cloud |
|---|---|---|---|
| 仮想ネットワーク | VPC | Virtual Network（VNet） | VPC |
| ロードバランサー | ELB（ALB・NLB） | Load Balancer、Application Gateway | Cloud Load Balancing |
| CDN | CloudFront | Front Door | Cloud CDN |
| DNS | Route 53 | Azure DNS | Cloud DNS |
| ID・権限管理 | IAM | Entra ID、Azure RBAC | Cloud IAM |
| 監視・ログ | CloudWatch | Azure Monitor | Cloud Monitoring、Cloud Logging |
| 構成のコード化（IaC） | CloudFormation、CDK | Bicep、ARMテンプレート | Infrastructure Manager |
| データ分析（DWH） | Redshift、Athena | Microsoft Fabric | BigQuery |
| 生成AI基盤 | Bedrock、SageMaker AI | Microsoft Foundry | Gemini Enterprise Agent Platform（旧Vertex AI） |

IaCは各社専用ツールのほか、どのクラウドにも使える Terraform が広く使われています。生成AI基盤は名称変更が多いため、案件では最新の公式名を確認してください。

## 知らないサービス名に出会ったら

クラウドのサービスは数百あり、すべてを覚えることはできません。知らない名前が出てきたら、次の順で調べると短時間で位置づけがわかります。

1. 役割を特定する：{{ch:parts}}の6分野のどれに当たるか。公式ページの最初の1文に書いてあることが多い
2. 対応表で言い換える：自分が知っている事業者の、どのサービスに相当するか
3. 管理範囲を確認する：OSや台数を自分で管理するのか、事業者に任せるのか
4. 課金の単位を確認する：時間か、量か、リクエスト数か。動かしているだけで費用がかかるか
5. 上限を確認する：1回の処理時間、データの大きさ、同時に動かせる数などの制限（クォータ）

:::sum
- 市場はAWS・Microsoft・Googleの3社で約6割。差は縮まる傾向にあり、生成AIの需要が全体を押し上げている
- 事業者の選定は、技術の優劣だけでなく、既存の製品や契約、社内の技術者、案件の制約で決まることが多い
- サービス名は違っても、役割は共通している。役割で理解しておけば、別の事業者にも応用できる
:::

## 章末問題

:::q 言い換え | Azureの構成をAWSの言葉で読む
顧客から受け取った資料に、次の構成が書かれていました。それぞれAWSのどのサービスに相当するかを答えてください。

Front Door → Application Gateway → Virtual Machines → Azure SQL Database。画像は Blob Storage に保存し、監視は Azure Monitor、利用者の認証は Entra ID で行う。
:::a
| Azure | 役割 | AWSで相当するもの |
|---|---|---|
| Front Door | CDN | CloudFront |
| Application Gateway | ロードバランサー | ALB |
| Virtual Machines | 仮想サーバー | EC2 |
| Azure SQL Database | リレーショナルDB | RDS、Aurora |
| Blob Storage | オブジェクトストレージ | S3 |
| Azure Monitor | 監視・ログ | CloudWatch |
| Entra ID | ID管理 | IAM Identity Center、IAM |

つまりこの構成は、{{ch:pattern}}で学ぶWeb 3層構成そのものです。名前が違っても役割に置き換えれば、同じ読み方ができます。なお、相当するサービス同士でも機能や制限は同じではないため、設計では必ずそれぞれの公式ドキュメントを確認します。
:::

:::q 計算 | シェアが下がると売上も下がるのか
本文の数字を使って、次の問いに答えてください。

1. 2026年7〜9月期の市場が約1,677億ドルで前年同期比55%増のとき、2025年7〜9月期の市場規模は約何億ドルですか
2. シェアに市場規模を掛けて、AWSに相当する金額を2025年7〜9月期と2026年7〜9月期のそれぞれで概算してください
3. その結果から、「シェアが下がった」ことについて何が言えますか
:::a
1. 1,677 ÷ 1.55 ≒ 1,082億ドル
2. 2025年7〜9月期：1,082 × 29% ≒ 314億ドル。2026年7〜9月期：1,677 × 26% ≒ 436億ドル
3. AWSに相当する金額は約39%増えています。シェアが29%から26%に下がったのは、市場全体（55%増）がそれ以上に伸びたためです

この計算は、四捨五入されたシェアに推計の市場規模を掛けた概算で、各社が発表する売上高とは定義が異なります。「シェア低下 = 不調」と短絡せず、母数である市場全体の動きと合わせて読むことが大切です。
:::

:::q 判断 | どの事業者から検討するか
次の3つの状況で、最初に検討する事業者と理由を答えてください。あわせて、技術以外に確認すべき点を1つずつ挙げてください。

1. Microsoft 365 と Windows Server を全社で使っている企業の、社内業務システムの移行
2. 数年分のアクセスログと売上データを集めて分析する基盤の新規構築
3. Oracle Database を中心にした基幹システムの更改
:::a
1. Azure。既存のID基盤（Entra ID）やライセンスとの相性がよい。確認点：既存のMicrosoftとの契約に、クラウド利用の条件や割引が含まれているか
2. Google Cloud（BigQuery）が有力な候補。AWS（Redshift、Athena）でも実現できる。確認点：データの発生元がどの事業者にあるか。別の事業者から大量に転送すると、転送の費用と時間がかかる
3. Oracle Cloud Infrastructure が候補。AWSやAzureでも Oracle Database は動かせる。確認点：Oracle のライセンスの条件が、動かす環境によってどう変わるか

実際の選定では、社内に扱える技術者がいるか、既存システムとどうつなぐか、顧客の指定や調達の条件があるか、が決め手になることが少なくありません。
:::
