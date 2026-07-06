# レンダラー間の描画互換性

`mermaid-diagrams/SKILL.md` の詳細ガイド。図種・機能を選ぶ前に、その図が
どこで読まれるかを必ず確認する。

## バージョンの乖離

- Mermaid本体の最新はv11.16.0系(npm最新)。Live Editor・
  `@mermaid-js/mermaid-cli`もほぼ同期している。
- **GitHubは大きく遅れる**。公式なバージョン番号は非公表(内部レンダラー
  "Viewscreen"を使用)。コミュニティが`info`ダイアグラムで確認した最後の
  確定値はv11.4.1(2025年4月時点)。個別リポジトリでのバージョン更新手段は
  提供されておらず、アップグレードのロードマップも非公表。
- GitLabはGitHubより新しいバージョンに追従する傾向がある。VS Code拡張・
  Live Editorは最新に近い。Notionもネイティブ対応している。

「どのバージョンで動くか」は生成時に固定できないため、**ターゲットレンダラー
ごとに使える機能を絞るのが唯一堅実な戦略**になる。

## 図種別の適合表

| 図種 | 成熟度 | 最適ユースケース | 主要な制約 |
|---|---|---|---|
| flowchart / graph | 安定(コア) | システム構成図・データフロー・CI/CDパイプライン | subgraphのdirectionが無視される/逆転するバグあり。~10-15ノード超で自動レイアウトが破綻しやすい |
| architecture-beta | beta(v11.1.0+) | クラウドインフラ図・サービス/リソース関係 | GitHub等の静的レンダラーで組み込み5アイコン以外は描画されない。fcoseレイアウトの兄弟ノード重なり(#6120) |
| C4(C4Context等) | experimental | System Context/Container図 | 自動レイアウトなし。GitHubで描画されないとの報告あり(確信度は中) |
| block-beta | beta | 手動レイアウトが必要な層構造・多段構成図 | 完全手動配置。自動整列なし |
| classDiagram | 安定 | クラス構造・ドメインモデル | アーキテクチャ全体像には不向き |
| erDiagram | 安定 | DBスキーマ・データモデル | UMLカーディナリティ記法と異なる独自記法。アーキ図には限定的 |
| sequenceDiagram | 安定 | API相互作用・認証フロー・イベントフロー | 構造図ではなく相互作用図 |
| stateDiagram-v2 | 安定 | 状態遷移・ライフサイクル | 構成図には不向き |
| UMLデプロイ図 | 非対応 | — | Mermaidに存在しない。PlantUML(またはC4Deployment/architecture-beta/block-betaでの代替)を検討する |

## GitHubでの描画の実態(確信度の内訳)

- **architecture-beta**: レイアウト構造自体は描画されるが、Iconifyアイコンは
  `registerIconPacks`が呼ばれないため描画されない。複数の独立ソースで
  裏付けられており確信度が高い。
- **C4**: GitHubのビルトインMermaidレンダラーがC4を描画せず生テキストのまま
  表示されるという報告がある。ただしC4がMermaidコア機能である点から技術的には
  曖昧さが残り、確信度は中程度。「C4はGitHubで確実に描画される保証はない」と
  扱うのが安全。

## 実務判断の指針

- ターゲットがGitHub中心 → architecture-beta/C4/ELKレイアウト/Iconifyを避け
  flowchart中心にする。
- ターゲットが自前ドキュメントサイト/CI生成 → architecture-beta + Iconifyで
  高品質図に投資してよい。
- 本格的なC4モデリングが要件 → Mermaidではなく`dev-docs-writing`が挙げる
  Structurizr/PlantUMLを検討する。
- UMLコンポーネント図/デプロイ図が必要 → Mermaidでは非対応のためPlantUMLへ
  フォールバックする。
