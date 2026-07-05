# <対象システム名> アーキテクチャ図

- Owner: <個人またはチーム名>
- Last reviewed: `YYYY-MM-DD`

<!-- 更新時の注意: この図はコードと同じPRで更新する。実装と乖離した図は放置しない -->

## Context図

```mermaid
C4Context
    Person(user, "<利用者>")
    System(system, "<このシステム>")
    System_Ext(ext, "<外部システム>")

    Rel(user, system, "<やり取りの内容>")
    Rel(system, ext, "<やり取りの内容>")
```

## Container図

```mermaid
C4Container
    Container(api, "<コンテナ名>", "<技術スタック>", "<役割>")
    ContainerDb(db, "<データストア名>", "<技術スタック>", "<役割>")

    Rel(api, db, "<やり取りの内容>")
```

## 要素の説明

| 要素 | 役割 |
|---|---|
| <要素名> | <説明> |
