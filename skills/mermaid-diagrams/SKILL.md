---
name: mermaid-diagrams
description: >
  Mermaid.js図(フローチャート・シーケンス図・ER図・クラス図・状態遷移図・
  architecture-beta等)を新規作成する、または既存のMermaid記法をレビュー・修正
  したいときに使う。「Mermaid図を描いて」「アーキテクチャ図をMermaidで書いて」
  「シーケンス図/ER図/状態遷移図/クラス図を書いて」「この図、GitHubで表示されない」
  「このMermaidの構文エラーを直して」「Mermaidの図が崩れる/レイアウトが
  おかしい」「この図をmmdcで検証して」「Mermaidのテーマ・色を変えたい」
  「この図にアイコンを付けたい」のような依頼で使う。C4モデルやアーキテクチャ図・
  データフロー図という文書そのものの構成・使い分けについてはdev-docs-writing
  を使う。
---

# mermaid-diagrams

Mermaid.js図の記法そのもの(図種選択・構文の落とし穴・レンダラー間の描画互換性・
検証・大規模図のレイアウト・テーマ/アイコン)を扱う。C4モデルやアーキテクチャ図・
データフロー図という文書の構成・使い分けは
[dev-docs-writing](../dev-docs-writing/references/architecture-diagram-guide.md)
の管轄であり、ここでは再教育しない。

## 図種の使い分け

| 図種 | 使うタイミング | 制約・描画互換性 | 詳細ガイド |
|---|---|---|---|
| flowchart / graph + subgraph | システム構成図・データフロー・CI/CDパイプライン・マイクロサービス概観 | 安定・全レンダラーで動く。GitHub中心ならこれがデフォルト | `references/flowchart-guide.md` |
| architecture-beta | クラウドインフラ図・サービス/リソース関係 | beta。組み込み5アイコン以外はGitHub等で描画されない | `references/architecture-beta-guide.md` |
| sequenceDiagram | API相互作用・認証フロー・イベントフロー | 安定。構造図ではなく相互作用図 | `references/sequence-diagram-guide.md` |
| erDiagram | DBスキーマ・データモデル | 安定。アーキ図全体像には不向き | `references/er-diagram-guide.md` |
| classDiagram | クラス構造・ドメインモデル | 安定。アーキ図全体像には不向き | `references/class-diagram-guide.md` |
| stateDiagram-v2 | 状態遷移・ライフサイクル | 安定。構成図には不向き | `references/state-diagram-guide.md` |
| C4(Context/Container) | システムの利用者・外部システム関係、実行単位の構成 | 構造・使い分けは`dev-docs-writing`を参照。ここではMermaid記法のみ扱う | [architecture-diagram-guide.md](../dev-docs-writing/references/architecture-diagram-guide.md) |
| UMLデプロイ図・コンポーネント図 | 実行環境へのデプロイ構成、コンポーネント間インターフェース | Mermaidに存在しない。PlantUMLへフォールバック | — |

迷ったときの目安: 図種を決める前に「どこで読まれるか」を確認する。GitHub README
でインライン描画されるなら flowchart 一択に近い。ローカル/CI で SVG を生成して
ドキュメントサイトに埋め込むなら architecture-beta の高品質アイコン図も選べる。

## 描画先を先に確認する

Mermaid本体の最新版とターゲットレンダラーが実装しているバージョンには乖離がある。
GitHubの内蔵レンダラーはバージョンを公表しておらず、Mermaid本体に対して大きく
遅延することが知られている。GitLabやVS Code拡張・Live Editorはより新しい版に
追従する傾向がある。この乖離は生成時に固定できないため、「ターゲットレンダラーで
使える機能に絞る」のが唯一堅実な戦略になる。詳細な適合表は
`references/rendering-compatibility-guide.md` を参照する。

## 構文のお約束(高頻度エラーの回避)

LLMがMermaid図を生成する際に壊れやすいパターンは限られている。生成時は必ず
次を守る。

- 予約語 `end` を小文字のまま接続先やノード名に使わない。`End`/`END` など
  大文字化した名前にする。
- ノードIDに `default` をそのまま使わない。既知の未文書化の衝突がある。
  `default_node["default"]` のように安全なID(英数+アンダースコア)と
  表示用ラベルを分ける。
- ラベルに `()`・`:`・`,`・`{}` を含む場合は必ずダブルクォートで囲む
  (`A["Fuel Pellets (UO2 / MOX)"]`)。LLM生成コードで最頻出のエラー。
- ラベル内の `<`・`>` はHTMLエンティティ(`&lt;`/`&gt;`)にエスケープする。
  特に `<meta>` のような実在HTMLタグ名はレンダラーがタグと誤認する。
- 接続先が `o`/`x` で始まると `---o` が円エッジ、`---x` が交差エッジと
  誤認識される(`dev---ops` に注意)。大文字化するかスペースを空ける。
- 日本語/CJKラベルは常にダブルクォートで囲む。
- ラベル内の改行は `<br/>` かmarkdown文字列(バッククォート囲み)を使い、
  `\n` は使わない。

## 生成→検証のワークフロー

1. 上表を使って図種を決める。読者・レンダラーが不明なら質問する。
2. 生成したMermaidコードを `.mmd` ファイルとして保存する。
3. `scripts/validate.sh <file.mmd>` でパース検証する(詳細は
   `references/validation-workflow-guide.md`)。
4. 失敗したら該当する `references/*.md` とエラーメッセージを突き合わせて
   修正し、再検証する。**レンダリングが通るまで完了と言わない**。
5. ターゲットがGitHub等の静的レンダラーの場合、
   `references/rendering-compatibility-guide.md` で使用した機能
   (アイコン・ELKレイアウト・C4等)がそのレンダラーで実際に描画されるかを
   確認する。

## 既存図のレビュー・修正ワークフロー

1. 図種を判定する(不明なら質問する)。
2. 上記「構文のお約束」と該当する `references/*-guide.md` で構文上の
   問題を洗い出す。
3. `scripts/validate.sh` で実際にパース検証する。
4. ノード数(目安12個超で分割を検討、`references/large-diagram-layout.md`)、
   ターゲットレンダラーとの互換性(`references/rendering-compatibility-guide.md`)
   を確認する。
5. 指摘は該当箇所を引用し、問題点と修正案をセットで提示する。指示なく
   無断で全体を書き換えない。

## references/

- `flowchart-guide.md`: flowchart/graph + subgraph の構文と `direction` の
  既知の不安定挙動
- `architecture-beta-guide.md`: architecture-beta の構文とアイコン制約
- `sequence-diagram-guide.md`: sequenceDiagram の構文
- `er-diagram-guide.md`: erDiagram の構文
- `class-diagram-guide.md`: classDiagram の構文
- `state-diagram-guide.md`: stateDiagram-v2 の構文
- `rendering-compatibility-guide.md`: レンダラー間のバージョン乖離と
  図種別の適合表
- `large-diagram-layout.md`: ノード数の目安・分割・ELKレイアウト
- `validation-workflow-guide.md`: `mmdc` による検証ワークフローと
  `scripts/validate.sh` の使い方
- `theming-icons-guide.md`: テーマ変数・`classDef`・アイコンの制約

## 出典

- Mermaid公式ドキュメント(mermaid.js.org)
- Mermaid GitHubリポジトリのIssue/Discussion(subgraph directionのバグ報告
  #7477・#6438・#3096・#4648・#2789、architecture-betaのアイコン制限 #6120等)
- GitHubのMermaidレンダラーのバージョンに関するコミュニティ観測(確度は中程度、
  `references/rendering-compatibility-guide.md` の「確信度」節を参照)
