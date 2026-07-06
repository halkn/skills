---
name: data-platform-architecture
description: >
  データ基盤・DWH・データパイプラインのアーキテクチャを新規設計・構成検討・図示する、
  または既存のアーキテクチャ設計をレビューして問題点を指摘したいときに使う。
  Snowflakeを中核とする構成に特に詳しいが、他のデータ基盤にも適用できる。
  「データ基盤を設計して」「DWHのアーキテクチャを考えて」「Snowflakeのウェアハウス構成/
  RBAC設計を考えて」「データパイプラインの構成を検討して」「この設計/構成をレビューして」
  「このアーキテクチャを評価して」「medallionのレイヤリングを設計して」のような依頼で使う。
---

# data-platform-architecture

データ基盤(DWH・データパイプライン・周辺エコシステム)のアーキテクチャ設計とレビューを
支援する。成果物は、C4図(Mermaid)を埋め込んだMarkdown設計書、または構造化された
レビューコメント。どちらのワークフローにも、設計者のバイアスを構造的に排除して品質を
検証するプロセスを組み込んでいる。

Snowflakeを中核とする構成の知識(`references/snowflake-platform.md`)を重点的に持つが、
設計プロセス自体はプラットフォーム非依存。Git操作(ブランチ・commit・PR)はこのskillの
範囲外であり、既存の運用(github-flow等)に委ねる。

## ワークフローの選択

- 新規設計・構成変更・技術選定の依頼 → [Design workflow](#design-workflow)
- 既存の設計書・構成・図に対する評価の依頼 → [Review workflow](#review-workflow)
- 特定領域だけの相談(例: RBAC設計、ウェアハウスサイジング)→ Design workflowの
  該当ステップだけを実施し、成果物もその範囲に絞る。ただしバイアス排除検証は省略しない

## Design workflow

- [ ] 1. **要件ヒアリング**: ワークロード種別・データ量・鮮度SLO・性能目標・
      コンプライアンス・チームスキル・予算を確認する。不明点はまとめて一度に質問する
      (逐次質問しない)。得られない情報は妥当な前提を置き、設計書に
      `{要確認: ...}` として明示する
- [ ] 2. **プラットフォーム・構成決定**: Snowflake中心なら
      `references/snowflake-platform.md`(内部設計)と `references/ecosystem.md`
      (周辺ツール選定)を読んで構成を決める。他プラットフォームなら
      `references/review-lens.md` の汎用原則で進め、固有機能の詳細知識は
      持ち合わせていない旨を成果物に明示する
- [ ] 3. **C4図生成**: `references/c4-mermaid-guide.md` に従い、
      Context図 → Container図の順に作る。Component図は価値がある場合だけ
- [ ] 4. **設計書出力**: `assets/design-doc-template.md` をコピーして埋める。
      主要設計判断ごとに、根拠(確信度ラベル付き)・失敗条件・却下した代替案を
      必ず記載する(書けない判断は検討不足)
- [ ] 5. **バイアス排除検証**: `references/bias-elimination.md` のプロトコルを実施する
      (下記「バイアス排除検証プロセス」参照)
- [ ] 6. **検証結果の反映**: 指摘ごとに対応/見送りを理由付きで設計書の検証記録に残す。
      CRITICALを未対応のまま成果物を確定しない

## Review workflow

- [ ] 1. **対象の把握**: 設計書・図・dbtプロジェクト・Terraform等、渡された資料を読む。
      資料に書かれていない意図を好意的に推測して補完しない
- [ ] 2. **観点照合**: `references/review-lens.md` の5柱+チームスキル適合性で評価する
- [ ] 3. **アンチパターン検出**: `references/antipatterns.md` と照合する
- [ ] 4. **出力**: `assets/review-comment-template.md` の形式で出力する。
      スコアカード、Severity順の指摘(Finding/Impact/Recommendation/Effort)、
      Strengths(必須)、総合判定(承認/条件付き承認/差し戻し)を含める。
      指摘は該当箇所を引用し、指示なく設計書全体を書き換えない

## バイアス排除検証プロセス

設計成果物には設計者自身の認知バイアス(確証バイアス・アンカリング・流行追従など)が
必ず混入する前提に立ち、次の3層で構造的に排除する。詳細な手順・サブエージェントへの
指示文テンプレート・指摘への対応ルールは `references/bias-elimination.md` にある。

1. **層1: チェックリスト自己検証**(設計中に常時): `references/review-lens.md` と
   `references/antipatterns.md` の全項目と照合する。自信のある領域ほど省略しない
2. **層2: 反証の明文化**(設計書に記録): 主要設計判断ごとに「失敗条件」と
   「却下した代替案」を書く。設計を支持する根拠だけを並べることを構造的に防ぐ
3. **層3: 独立レビュー**(成果物確定前に1回以上): 設計の経緯・会話の文脈を持たない
   サブエージェントに、設計書とレビュー観点ファイルだけを渡してレビューさせる。
   設計者の意図説明を渡さないことが確証バイアス排除の要。
   サブエージェント(Taskツール)が使えない環境では、`references/bias-elimination.md`
   記載のコールドリビュー(設計書のみを対象にした手順分離レビュー)にフォールバックする

Review workflowで既存設計をレビューする場合、レビュー自体が独立視点なので層3は不要。
代わりにステップ1の「意図を推測して補完しない」ルールを守る。

## references/

- `review-lens.md`: レビュー観点チェックリスト(WAF 5柱+チームスキル適合性)。
  設計の自己検証とレビューの両方で使う背骨
- `antipatterns.md`: 既知のアンチパターン集(症状/なぜ起きるか/対策)
- `bias-elimination.md`: バイアス排除検証プロトコル(3層の詳細、独立レビュー指示文
  テンプレート、指摘への対応ルール、フォールバック手順)
- `snowflake-platform.md`: Snowflake内部設計(ウェアハウス/RBAC/medallion/
  パイプライン方式の使い分け/環境分離/データ共有)
- `ecosystem.md`: 周辺エコシステム選定(ingestion/dbt/オーケストレーション/IaC/カタログ。
  デフォルト+エスケープハッチ形式)
- `c4-mermaid-guide.md`: C4×Mermaid作図ガイド(記法の注意とデータ基盤向けサンプル)

## assets/

- `design-doc-template.md`: 設計書テンプレート(主要設計判断の反証セクション・
  検証記録セクション込み)
- `review-comment-template.md`: レビューコメントテンプレート(スコアカード/
  Severity付き指摘/Strengths/総合判定)

## 出典

このskillが土台にしている一次情報。ユーザーに聞かれたら提示してよい。

- Snowflake Well-Architected Framework(レビュー観点の背骨):
  <https://www.snowflake.com/en/engineering-blog/well-architected-framework/>
- Snowflake公式ドキュメント(Warehouse considerations、Access control best practices、
  Dynamic tables decision guide、Data sharing等): <https://docs.snowflake.com/>
- C4 model: <https://c4model.com/>
- Mermaid C4記法(実験的): <https://mermaid.js.org/syntax/c4.html>
