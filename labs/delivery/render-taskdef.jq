# 登録済みのタスク定義から、登録のときに指定できない項目を除き、
# 名前が app のコンテナのイメージだけを、新しいものに差し替える
del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities,
    .registeredAt, .registeredBy, .deregisteredAt)
| .containerDefinitions |= map(if .name == "app" then .image = $image else . end)
