# 周辺エコシステム選定ガイド

データ基盤を構成する周辺ツールの選定基準。各領域とも「デフォルト+それを外れる条件
(エスケープハッチ)」の形式で書く。選択肢を網羅的に並べて選ばせるのではなく、
要件がデフォルトで足りるかを先に確認する。

## Ingestion(取り込み)

- **デフォルト**: SaaSソースはマネージドコネクタ(Fivetran/Airbyte等)、
  ファイル着地はSnowpipe(またはDWHネイティブの自動取り込み)。
- エスケープハッチ:
  - 行単位・秒オーダーの鮮度が要る → ストリーミング取り込み
    (Snowpipe Streaming / Kafkaコネクタ)
  - コネクタ費用が支配的、または特殊ソース → 自前実装(保守コストと比較してから)

## 変換(Transformation)

- **デフォルト**: dbt。staging → intermediate → marts の3層、`ref()` による依存管理、
  incremental + unique_key(MERGE生成)、tests、docs。
- エスケープハッチ:
  - SQL宣言だけで完結する単純な鮮度維持 → DWHネイティブの宣言的テーブル
    (SnowflakeならDynamic Tables。dbtとの併用は依存関係の見通しに注意)
  - Python中心のチーム・ML前処理 → Snowpark等のデータフレームAPI

## オーケストレーション

- **デフォルト**: dbt + DWH内で完結するなら専用スケジューラ(dbt Cloud scheduler)か
  DWHネイティブのスケジューラ(Snowflake Tasks)。外部依存が少ないほど運用は軽い。
- エスケープハッチ:
  - 異種システム(API・ファイル転送・ML学習)をまたぐ依存がある → Airflow
    (最大のoperatorエコシステム)または Dagster(asset指向。dbtモデルを
    ファーストクラスのassetとして扱い、lineage/freshnessがネイティブ)
  - 判断基準は「DWH外のタスクがいくつあるか」。ゼロなら外部オーケストレータは過剰。

## IaC(Infrastructure as Code)

- **デフォルト**: アカウントレベルのオブジェクト(ウェアハウス/DB/スキーマ/ロール/
  権限/インテグレーション)はTerraform(Snowflake公式Provider)。
  テーブル等スキーマ内オブジェクトはdbt等のDCMツールに任せ、**Terraformで管理しない**
  (破壊的再作成のリスク)。
- CI/CDでfmt/validate/plan/applyを回し、環境はworkspace/変数/ブランチ戦略で分離する。
- エスケープハッチ: Terraformスキルがチームにない小規模構成 → まずスクリプト化された
  SQL(再現可能な形)から始め、環境が増えた時点でIaCに移行する。

## カタログ・ガバナンス

- **デフォルト**: プラットフォームネイティブのカタログ(SnowflakeならHorizon Catalog。
  タグ・lineage・マスキングと統合)。
- エスケープハッチ: 複数プラットフォーム横断のカタログが要件 →
  外部カタログ(Atlan/Alation/Collibra等)。ただし二重管理のコストを設計書に明記する。

## 選定時の共通ルール

- 構成要素を1つ増やすごとに、運用負荷(監視・アップグレード・スキル習得)を
  設計書のチームスキル適合性の項で評価する。
- 「デフォルトで足りない理由」を主要設計判断として記録する
  (反証の明文化。[bias-elimination.md](bias-elimination.md) 層2)。
