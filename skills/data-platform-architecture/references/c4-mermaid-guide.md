# C4×Mermaid 作図ガイド

設計書に埋め込むアーキテクチャ図の作り方。C4モデルの抽象度とMermaidのC4記法を使う。

## 方針

- **Context図とContainer図で大半のケースは十分**。Component図は特定の内部構造に
  設計判断が集中しているときだけ描く。Code図は描かない。
- C4のレベルは「図の抽象度」であり、成果物を分割する単位ではない。
  1つの設計書にContext図とContainer図を順に載せる。
- 多数のシステムが関わる場合、1枚に詰め込まず焦点ごとに複数の図に分割する。
- MermaidはGitHub/多くのMarkdownビューアで直接レンダリングされるため、
  設計書(Markdown)への埋め込みに適する。

## Mermaid C4記法の注意

- `C4Context` / `C4Container` / `C4Component` 記法は**実験的**であり、
  公式が「構文・プロパティは変更されうる」「レイアウトは全自動ではなく
  記述順に依存する」と明記している。
- **図が崩れたら要素の宣言順を入れ替える**。これが主なレイアウト調整手段。
- `UpdateLayoutConfig($c4ShapeInRow="3")` で1行あたりの要素数を調整できる。
- 厳密なレイアウト制御や大規模図が必要なら、Structurizr DSLやPlantUMLへの
  切り替えを提案する。

## Context図の例(データ基盤)

登場人物: データ生産者(業務システム・SaaS)、データ基盤、データ消費者
(アナリスト・BIツール・外部共有先)。

```mermaid
C4Context
  title データ基盤 System Context
  Person(analyst, "アナリスト", "ダッシュボードとアドホック分析")
  System_Ext(saas, "業務SaaS", "CRM/会計等のデータソース")
  System_Ext(oltp, "業務DB", "自社サービスのOLTP")
  System(platform, "データ基盤", "取り込み・変換・提供を担う")
  System_Ext(bi, "BIツール", "ダッシュボード配信")
  Rel(saas, platform, "日次/準リアルタイム連携")
  Rel(oltp, platform, "CDC/バッチ抽出")
  Rel(platform, bi, "マート提供")
  Rel(analyst, bi, "参照")
  Rel(analyst, platform, "アドホックSQL")
```

## Container図の例(Snowflake中心の構成)

コンテナ粒度: 取り込み層 / DWH(レイヤー別DB・ウェアハウス群)/ 変換 /
オーケストレータ / BI / カタログ。

```mermaid
C4Container
  title データ基盤 Container図
  System_Ext(sources, "データソース群", "SaaS / 業務DB / ファイル")
  Container_Boundary(platform, "データ基盤") {
    Container(ingest, "取り込み", "Fivetran / Snowpipe", "ソース別コネクタ")
    Container_Boundary(snowflake, "Snowflake") {
      ContainerDb(raw, "RAW DB", "Bronze", "ソース忠実")
      ContainerDb(staging, "STAGING DB", "Silver", "標準化・再利用部品")
      ContainerDb(marts, "MARTS DB", "Gold", "業務向けマート")
    }
    Container(dbt, "dbt", "変換", "staging→marts、tests")
    Container(orch, "オーケストレータ", "Airflow等", "依存管理・スケジュール")
  }
  Container_Ext(bi, "BIツール", "可視化")
  Rel(sources, ingest, "抽出")
  Rel(ingest, raw, "ロード")
  Rel(dbt, staging, "変換")
  Rel(dbt, marts, "変換")
  Rel(orch, dbt, "実行制御")
  Rel(bi, marts, "参照")
```

ウェアハウス分離(ETL用/BI用等)を図で示したい場合は、Container図に詰め込まず
設計書の構成要素の表で扱うか、焦点を絞った別図にする。

## 出力時のセルフチェック

- [ ] 図の各要素が本文の構成要素と対応している(図にだけ登場する要素がない)
- [ ] 矢印に説明ラベルがある(「連携」だけの矢印を残さない)
- [ ] Context→Containerで抽象度が正しく下がっている(Contextに製品名を書きすぎない)
- [ ] レンダリングを確認した(崩れる場合は宣言順を調整した)
