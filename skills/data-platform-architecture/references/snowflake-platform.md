# Snowflake内部設計ガイド

Snowflakeを中核に据える場合の内部設計の要点。ウェアハウス・RBAC・レイヤリング・
パイプライン方式の選択・環境分離・データ共有を扱う。周辺ツールの選定は
[ecosystem.md](ecosystem.md) を参照。

## 目次

1. [ウェアハウス設計・サイジング](#ウェアハウス設計サイジング)
2. [RBAC・アクセス制御設計](#rbacアクセス制御設計)
3. [データベース/スキーマのレイヤリング(medallion)](#データベーススキーマのレイヤリングmedallion)
4. [パイプライン方式の使い分け](#パイプライン方式の使い分け)
5. [マルチ環境・データ共有](#マルチ環境データ共有)
6. [オープンフォーマット・AI機能の設計判断](#オープンフォーマットai機能の設計判断)
7. [出典](#出典)

## ウェアハウス設計・サイジング

- **ワークロード分離が大原則**。ETL/ELT用・BI用・アドホック用・ML用でウェアハウスを
  分ける。単一巨大ウェアハウスへの集約は公式が明記するアンチパターン。
- **start small, scale as needed**。サイズを1段上げるとコンピュートと時間課金は概ね倍。
  課金は最初の60秒が最低課金、以降は秒課金。
- **スケールアップとスケールアウトの使い分け**:
  - サイズアップ = クエリの複雑性・メモリスピル対策。クエリ性能はサイズに対して
    概ね線形にスケールする(公式)
  - マルチクラスタ = 同時実行(キュー待ち)対策。遅い単体クエリは速くならない。
    キュー深度が常時2〜3を超えるならクラスタ追加が妥当
- **auto-suspend**は公式推奨で低め(5〜10分以下)。ETL系は即時〜1分、
  BI系はローカルキャッシュ温存と天秤にかけて長め。**auto-resume**は全WHで有効化
  (再開は10秒未満)。
- ワークロード特性別の目安: ETL/ELT=大きめ・短時間・即時サスペンド、
  BI=中サイズ・キャッシュ温存で長めサスペンド、アドホック=可変。
- ロード用ファイルサイズは**100〜250MB(圧縮後)**が目安。COPYの並列スレッドを
  活かしつつ、ファイルごとのオーバーヘッドを避ける。
- `WAREHOUSE_METERING_HISTORY` / `QUERY_HISTORY` で重いワークロードを特定し、
  コスト構成比の大きい順に最適化する。コスト内訳はcompute約65%・storage約25%・
  cloud services約10%が目安(確信度: 中、コンサル調べ)。cloud servicesは
  日次でWH使用量の10%を超えた分のみ課金(公式)。

## RBAC・アクセス制御設計

- **Role of Three** の3層構造:
  1. **Access Roles** — データ中心の低レベル部品(READ/READWRITE等)。
     エンドユーザ・サービスアカウントに直接付与しない
  2. **Functional Roles** — 業務中心。ユーザに付与する
  3. **Service Roles** — システム中心。サービスアカウント用
- Functional RoleはSYSADMINに付与し、オーナーシップの孤立を防ぐ。
- **ACCOUNTADMINをデフォルトロールにしない・自動化スクリプトに使わない**(公式)。
- Managed Access Schemaで権限付与を中央集権化。Future Grants + `GRANT ON ALL` で
  付与数を削減。
- **Database Roles**(単一DBスコープ、セッションでアクティブ化不可)でAccess Roleの
  肥大を抑える。PUBLICロールへの機微な権限付与を避ける。
- SELECT権限にはウェアハウスUSAGEをペアで付与する(片方だけでは使えない)。
- 環境別ロール(DEV/TEST/PROD prefix)と命名規約を徹底する。RBAC構成の複製は
  スクリプト/IaCで自動化する(データのゼロコピークローンに相当するRBAC複製機能はない)。

## データベース/スキーマのレイヤリング(medallion)

- **Bronze(raw)**: ソース忠実。変換なし。`_loaded_at` 等のメタデータ列のみ追加。
  ロードはCOPY INTO/Snowpipe/SaaSコネクタの仕事で、**dbtはBronzeをロードしない**。
- **Silver**: staging(パース・型変換・命名標準化。業務ルールのWHEREを入れない)と
  intermediate(dedup・join・業務非依存の再利用部品。joinは1回書いて参照)。
- **Gold(marts)**: 業務ロジック・KPI・メトリクス。業務部門向けの粒度で提供。
- 命名規約: `stg_<source>__<entity>`、`int_<entity>__<descriptor>`。
- **冪等性**: SilverはdbtのincrementalとuniqueキーによるMERGE、Bronzeは
  COPY INTOのファイル追跡やStreamsのオフセットで再実行を安全にする。

## パイプライン方式の使い分け

公式のdecision guideに基づく使い分け:

| 方式 | 使うとき | 制約・注意 |
|---|---|---|
| **Dynamic Tables** | 新規のマルチテーブルSQLパイプライン(join/集約/window含む)の第一候補。宣言的で、リフレッシュ・依存順序・増分処理はSnowflakeが管理 | 最小target lagは1分。読み取り専用でDML/MERGE不可。GDPRの削除要求対応には不向き。アカウントあたり上限あり(公式limitations参照) |
| **Streams & Tasks** | ストアドプロシージャ・MERGE upsert・外部関数呼び出し・カスタムリトライ・CRON・SCD Type 2・サブ分単位のカスタムロジックが必要なとき | 命令的。依存管理・冪等性は自前で設計する |
| **Materialized Views** | join無しの単一ベーステーブルのクエリ高速化(オプティマイザが自動書き換え) | joinを含む定義は不可 |
| **Snowpipe** | ファイルベースの準リアルタイム取り込み(〜30秒) | ファイルサイズ最適化(100〜250MB)の影響を受ける |
| **Snowpipe Streaming** | 行ベースの低レイテンシ取り込み(〜5秒)。Kafka経路の代替 | サーバレス。クライアント実装が必要 |

## マルチ環境・データ共有

- dev/stg/prodの分離は「同一アカウント内のnamespace+RBAC分離」か「アカウント分離」の
  いずれか。**後からの変更は困難なので初期に決める**(公式)。
- **Secure Data Sharing**: データコピーなしで共有。consumerはストレージ課金なし
  (compute課金のみ)。形態はDirect Share / Listing / Data Exchange / Clean Room。
  Reader Accountで非Snowflakeユーザにも共有可能。クロスリージョン共有には
  replication groupが必要。
- data mesh実装ではドメインをアカウント/DB/スキーマにマッピングし、
  ドメイン間の提供インターフェースをShare/Listingにする。

## オープンフォーマット・AI機能の設計判断

- **Apache Iceberg**: 外部エンジン(Spark/Trino/Flink等)との相互運用や
  ベンダーロックイン回避が要件のときに検討する。引き換えに運用複雑性
  (カタログ管理・外部ストレージ管理)が増える。要件にないなら
  ネイティブテーブルが既定。
- **カタログ**: SnowflakeネイティブはHorizon Catalog(Iceberg REST API公開・
  外部エンジンからの双方向アクセスに対応)。オープン実装としてApache Polaris系がある。
  REST API課金の扱いは公式ドキュメントで最新を確認する。
- **Cortex AI**(AISQL・Search・Analyst・Agents): RBAC・行アクセスポリシーを継承する
  ため、ガバナンス層を二重に作らない。Cortex Searchは容量ベースの常時課金があるため、
  未使用時のサスペンドを運用に組み込む。
- これらの機能はリリースサイクルが速い。設計時に公式リリースノートで
  GA/Preview状態と課金条件を確認してから採用を決める。

## 出典

- Warehouse considerations / Access control best practices /
  Dynamic tables decision guide & limitations / Data sharing / Understanding overall cost
  (いずれもSnowflake公式ドキュメント): <https://docs.snowflake.com/>
- Snowflake Well-Architected Framework:
  <https://www.snowflake.com/en/engineering-blog/well-architected-framework/>
