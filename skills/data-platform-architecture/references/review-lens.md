# レビュー観点チェックリスト(review lens)

データ基盤アーキテクチャの設計・レビューで使う観点集。Snowflake Well-Architected
Framework(WAF)の5柱を背骨に、プラットフォームを問わず適用できる汎用チェック項目と、
Snowflakeの場合のネイティブ機能マッピングを併記する。最後の「チームスキル適合性」は
WAF外の追加観点。

## 目次

1. [横断的な設計原則](#横断的な設計原則)
2. [Security and governance(セキュリティとガバナンス)](#security-and-governance)
3. [Operational excellence(運用)](#operational-excellence)
4. [Reliability(信頼性)](#reliability)
5. [Performance optimization(性能)](#performance-optimization)
6. [Cost optimization(コスト)](#cost-optimization)
7. [チームスキル適合性](#チームスキル適合性)
8. [出典](#出典)

## 横断的な設計原則

- **必要なだけ速く(as fast as necessary, not as fast as possible)**:
  性能目標はビジネス要件(SLO)から導く。目標のない高速化はオーバープロビジョニング。
- **コストの優先順位は compute > storage > data transfer > cloud services**:
  最適化の投資はコスト構成比の大きい順に行う。多くの環境でcomputeが最大のドライバ。
- **ワークロード分離**: 特性の異なるワークロード(ETL/BI/アドホック/ML)は
  コンピュートリソースを分離し、個別にサイジング・監視・課金追跡できるようにする。
- **正しさから始まる信頼性(Trustworthy data)**: リネージの検証・スキーマ整合性の
  強制・データコントラクトでドリフトを防ぐ。信頼性はインフラ冗長化だけの話ではない。

## Security and governance

「Protect confidently」— データと利用者を保護し、統制を実装で示す。

汎用チェック項目:

- [ ] アクセス制御はロールベースで、最小権限・職務分離が設計されているか
- [ ] 管理者権限(スーパーユーザ相当)が日常運用・自動化に使われていないか
- [ ] PII・機微データの分類と、列/行レベルの保護(マスキング・行アクセス制御)があるか
- [ ] 暗号化(保存時・転送時)と鍵管理の方針が明示されているか
- [ ] ネットワーク境界(プライベート接続・IP制限)の要否が検討されているか
- [ ] 監査ログの取得先と保持期間が決まっているか
- [ ] データ共有(社外・他部門)の経路が統制されているか

Snowflakeの場合: RBAC/Database Roles、Row Access Policy・Masking Policy・
Projection Policy、Tri-Secret Secure/BYOK、PrivateLink、Horizon Catalog、
Trust Center、Data Clean Rooms、Differential Privacy。

## Operational excellence

「Run intelligently」— パイプラインとプラットフォームを自動化・観測可能にする。

汎用チェック項目:

- [ ] パイプラインの実行状況・失敗を検知する監視とアラートがあるか
- [ ] インフラ・権限・パイプラインがコード管理(IaC/GitOps)され、環境再現できるか
- [ ] dev/stg/prodの環境分離方針が初期に決められているか(後からの変更は困難)
- [ ] 使用量・クエリ履歴などのメタデータを運用改善に使う仕組みがあるか
- [ ] 定型運用(リフレッシュ・バックフィル・権限付与)が手作業に依存していないか

Snowflakeの場合: Tasks & Streams、Dynamic Tables、Alerts、
ACCOUNT_USAGE/Event Tables、Resource Monitors、Terraform Provider、
Snowpark Container Services。

## Reliability

「Design for continuity」— 障害と誤操作からの回復を設計に織り込む。

汎用チェック項目:

- [ ] RPO/RTOに見合ったバックアップ・リージョン間レプリケーション方針があるか
- [ ] 誤削除・誤更新からの復旧手段(タイムトラベル・スナップショット)があるか
- [ ] パイプラインが冪等で、再実行しても重複・欠損が起きないか
- [ ] スキーマ変更(schema drift)を検知・防止する仕組み(データコントラクト・テスト)があるか
- [ ] 上流障害時の挙動(遅延許容・部分更新の扱い)が定義されているか

Snowflakeの場合: cross-region replication & failover groups、
Time Travel/UNDROP、Streams/Tasks/Dynamic Tablesの増分・自己修復リフレッシュ、
dbt tests/データコントラクト。

## Performance optimization

「Deliver at scale」— SLOを定め、それを満たす最小の構成を選ぶ。

汎用チェック項目:

- [ ] 性能目標(クエリ応答時間・データ鮮度SLO)が明文化され、測定可能か
- [ ] スケールアップ(単体性能)とスケールアウト(同時実行)を混同していないか
- [ ] データレイアウト(パーティショニング・クラスタリング・ファイルサイズ)が
      アクセスパターンに合っているか
- [ ] 重いクエリ・重いワークロードを特定して優先的に最適化する運用があるか
- [ ] キャッシュ・マテリアライズドビューなどの高速化手段を、測定に基づいて使っているか

Snowflakeの場合: ウェアハウスサイズとマルチクラスタの使い分け、
Search Optimization Service、Query Acceleration Service、Materialized Views、
Hybrid Tables、clustering keys、Query Profile。
詳細は [snowflake-platform.md](snowflake-platform.md) を参照。

## Cost optimization

「Spend with purpose」— 支出を目的に紐付け、無駄を構造的に防ぐ。

汎用チェック項目:

- [ ] コンピュートの自動停止・自動再開が設定されているか(アイドル課金の防止)
- [ ] 小さく始めて測定に基づき拡張する方針か(「念のため大きめ」になっていないか)
- [ ] コストの可視化(ワークロード別・チーム別の帰属)と予算アラートがあるか
- [ ] 一時データ・中間データに恒久ストレージ相当の保護(履歴保持)を払っていないか
- [ ] コスト最適化の対象が構成比の大きい順(通常はcompute)になっているか

Snowflakeの場合: auto-suspend/auto-resume、秒課金とright-sizing、
Budgets、Resource Monitors、Snowsight FinOpsダッシュボード、
transient/temporary tables。

## チームスキル適合性

WAF外の追加観点。技術的に優れていても、チームが運用できない設計は失敗する。

- [ ] 採用技術のスキルがチームに存在するか、習得計画があるか
- [ ] 構成要素の数がチーム規模に見合っているか(少人数に多ツールはアンチパターン)
- [ ] オンプレ・他基盤からの移行の場合、設計だけでなく運用思考の転換
      (クラウドネイティブなコスト意識・宣言的パイプライン)が計画されているか
- [ ] ベンダーロックイン回避策(オープンフォーマット等)のコストが、
      それによる運用複雑性の増加と比較衡量されているか

## 出典

- Snowflake Well-Architected Framework 発表ブログ:
  <https://www.snowflake.com/en/engineering-blog/well-architected-framework/>
- 各柱の開発者ガイド(security-and-governance / operational-excellence /
  reliability / performance / cost-optimization):
  <https://www.snowflake.com/en/developers/guides/>
