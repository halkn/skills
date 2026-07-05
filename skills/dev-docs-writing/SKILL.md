---
name: dev-docs-writing
description: >
  開発チーム内のWiki・Design Doc・ADR・Runbook・README・アーキテクチャ図や
  データフロー図・APIドキュメント・オンボーディング資料/ハンドブックを新規作成する、
  または既存のそれらをレビューして構成・文体上の問題を指摘したいときに使う。
  「ADR書いて」「この決定をADRとして残して」「設計書を書いて」「デザインドックの
  レビュー」「RFC書いて」「Runbookのテンプレート欲しい」「このアラート対応の
  手順書作って」「Wikiページ作って」「READMEを整えて」「このシステムのアーキテクチャ図
  を残したい」「APIドキュメントを整備したい」「エンドポイントの仕様を書いて」
  「オンボーディング資料作って」「新メンバー向けのハンドブックを作って」
  「この文書、文体おかしいところ見て」のような依頼で使う。
---

# dev-docs-writing

開発チーム内で書かれる Wiki・Design Doc・ADR・Runbook・README・アーキテクチャ図/
データフロー図・APIドキュメント・オンボーディング資料/ハンドブックの8種を対象に、
新規作成とレビューの両方を支援する。Docs as Code運用(Git管理・PRレビュー・
オーナー明記)がすでに前提としてあることを想定し、ここでは文書の構成・文体のみを
扱う。ブランチ作成・commit・PR作成といったGit操作そのものはこのskillの範囲外であり、
[github-flow](../github-flow/SKILL.md) など既存の運用に委ねる(車輪の再発明をしない)。

## 対象文書と使い分け

| 種類 | 使うタイミング | テンプレート | 詳細ガイド |
|---|---|---|---|
| Wiki | 手順・FAQなど、繰り返し参照される非決定情報 | `assets/wiki-page-template.md` | `references/wiki-guide.md` |
| Design Doc(別名: RFC、Proposal、Tech Spec) | 実装前に設計・トレードオフの合意を得たい。複数チーム/PRにまたがる、後戻りコストが高い判断 | `assets/design-doc-template.md` | `references/design-doc-guide.md` |
| ADR | 個別の技術選定・アーキテクチャ判断とその文脈を短く記録する | `assets/adr-template.md` | `references/adr-guide.md` |
| Runbook | 特定のアラート・インシデントへの対応手順 | `assets/runbook-template.md` | `references/runbook-guide.md` |
| README | リポジトリ/プロジェクトの入口 | `assets/readme-template.md` | `references/readme-guide.md` |
| アーキテクチャ図・データフロー図 | システム構成やデータの流れを図示する | `assets/architecture-diagram-template.md` | `references/architecture-diagram-guide.md` |
| APIドキュメント | APIのエンドポイント仕様・使い方を文書化する | `assets/api-doc-template.md` | `references/api-doc-guide.md` |
| オンボーディング/ハンドブック | 新メンバー向けの参加手順・チームの働き方をまとめる | `assets/onboarding-template.md` | `references/onboarding-guide.md` |

迷ったときの目安: 未来の設計合意(RFC・Proposalと呼ばれる場合も含む)→Design Doc /
過去の個別判断の記録→ADR / 使い方→README・APIドキュメント / 決まった作業の手順→
Runbook / システム構成やデータの流れの図示→アーキテクチャ図・データフロー図 /
新メンバー向けの参加手順→オンボーディング/ハンドブック / それ以外の繰り返し参照情報→
Wiki。

1文書1目的を守る。依頼が複数の目的にまたがる場合(例: 「設計判断とRunbookを1ページに」)は、
文書を分けることを提案してから進める。ただし、依頼が複数の文書種別のキーワードを含んで
いても、該当する詳細ガイド側にすでに統合の扱いが明記されている場合(例:
アーキテクチャ図をWikiページに掲載する際の`architecture-diagram-guide.md`の記述)は、
それに従い分割を提案せず単一の成果物として進める。

## 全文書共通のメタデータ

Wiki・Design Doc・ADR・Runbook・オンボーディング/ハンドブックの冒頭には次を必須で置く。

- オーナー: 保守責任を持つ個人またはチーム
- 最終レビュー日

Design DocとADRはさらにステータス(Design Doc: Draft/In Review/Approved/Obsolete、
ADR: Proposed/Accepted/Superseded)を明記する。オーナーのない文書は陳腐化する。日付は
四半期レビューやインシデント後更新のトリガーになる。Wikiはさらに、冒頭2段落でWHO
(誰が読むか)/WHAT(目的)/WHEN(作成・レビュー日)/WHERE(置き場所)/WHYを明示する。
README・アーキテクチャ図・APIドキュメントは性質上オーナー行のみで足りることが多い。

## 新規作成のワークフロー

1. 文書種別を確認する。依頼が曖昧なら上表の「使うタイミング」列を手がかりに質問する。
   読者・目的・スコープなど複数の情報が不明な場合も、質問はまとめて一度に行う
   (逐次質問しない)。それでも得られない情報は妥当な前提を置いて進め、その前提を
   成果物の該当箇所か会話で明示する。文書種別を問わず、Context/Decision/Consequences・
   Goals/Non-Goals・実際のシステム構成情報など、その文書の核心的な内容そのものが
   情報不足で埋まらない場合は、それらしい内容を創作せず `<要確認: 何を確認すべきか>`
   の形でその位置に明示し、末尾に要確認箇所を一覧化する。
2. 対応する `assets/<type>-template.md` をコピーして出発点にする。
3. オーナー・最終レビュー日(該当種別はステータスも)を埋める。オーナーが不明な場合は
   依頼者本人か会話から分かる担当チームを暫定オーナーとして記入し、正式化が必要な旨を
   注記する。会話にオーナーを特定する手がかりが一切ない場合も、質問で立ち止まらず
   Owner欄を `<要確認: オーナーを確認する>` として明記し、要確認箇所の一覧に加える。
4. `references/<type>-guide.md` を見ながら、種別固有の構成ルールに沿って埋める。
5. 執筆時は下記「日本語文体の自己規律」と `references/ja-writing-style.md` に従う。
6. 完成後、`references/review-checklist.md` の該当種別セクションでセルフチェックする。

## 既存文書レビューのワークフロー

1. 文書種別を判定する(不明なら質問する)。
2. `references/review-checklist.md` の該当種別セクションで構成をチェックする。
3. オーナー・最終レビュー日の有無と陳腐化(長期間未更新でないか)をチェックする。
4. `references/ja-writing-style.md` に沿って文体をチェックする。
5. 指摘は該当箇所を引用し、問題点と改善案をセットで提示する。指示なく無断で全文を
   書き換えない。各指摘には`references/review-checklist.md`の重大度ラベル
   ([Must]/[Want]/[Nit])を付け、[Nit]のみを理由に差し戻さない(Good Over Perfect)。
6. Wikiで内容の重複が疑われる場合は、単一の真実源(canonical source)を決めて
   他方を統合または非推奨化することを提案する。陳腐化・重複した記述は、追記だけで
   なく削除や参照リンクへの置き換えも選択肢として示す。

## 日本語文体の自己規律

このskillで文書を書く・レビューするとき、次の表現を自分の出力に使わない。
根拠なくこれらを避けるだけでなく、必要な推量表現(「〜の可能性がある」等)を
理由なく削らないことにも同時に注意する。詳細な文体ルール(整形・段落構成・
論証の厳密さ・読者負荷管理・視点・演出抑制・冗長排除・見出し付け・読者への誠実さ)は
`references/ja-writing-style.md` を参照する。

- 予告・総括型: 「本章では〜を扱う」「以上、〜を見てきた」のような前置き・まとめ
- 姿勢宣言: 「正面から扱う」「〜に迫る」のような身振りの表明
- 空虚な形容: 「不可欠」「多角的」など、具体的な中身を伴わない評価語
- 空虚な動詞: 「掘り下げる」「紐解く」など、何をするか特定できない動詞
- 根拠のない緩和: 特に理由もなく「〜と言えるだろう」で言い切りを避ける言い回し
- 接続の型: 「〜において」「〜という観点から」のような新情報を運ばない接続、
  「さらに」「また」「加えて」の連打

## references/

- `design-doc-guide.md`: Design Docの書き方(Goals/Non-Goals、代替案、横断的関心事)
- `adr-guide.md`: ADRの書き方(1決定1レコード・append-only、コンテキスト/決定/結果、
  却下した代替案の記載、決定変更時の扱い)
- `runbook-guide.md`: Runbookの構成(1アラート1Runbook、判断を減らす、症状→診断→緩和→
  復旧確認→恒久対策)
- `wiki-guide.md`: Wikiの陳腐化・重複を防ぐための原則
- `azure-devops-wiki-guide.md`: Azure DevOps Wiki固有の書式規約(目次・図・ページ名)
- `readme-guide.md`: READMEの役割と構成
- `architecture-diagram-guide.md`: C4モデルとdiagram as codeの方針
- `api-doc-guide.md`: APIドキュメントの構成(仕様と実装判断の分離、動く例の優先)
- `onboarding-guide.md`: オンボーディング資料/ハンドブックの構成(handbook-first)
- `ja-writing-style.md`: 日本語文体ルールの詳細
- `review-checklist.md`: 新規作成・レビュー共通の実行チェックリスト

## assets/

- `design-doc-template.md` / `adr-template.md` / `runbook-template.md` /
  `wiki-page-template.md` / `readme-template.md` / `architecture-diagram-template.md` /
  `api-doc-template.md` / `onboarding-template.md`: 各文書種別のコピー用雛形

## 出典

このskillが土台にしている一次情報。ユーザーに聞かれたら提示してよい。

- Software Engineering at Google 第10章(Documentation): <https://abseil.io/resources/swe-book/html/ch10.html>
- Design Docs at Google(industrialempathy.com): <https://www.industrialempathy.com/posts/design-docs-at-google/>
- Google SRE Book(Postmortem Culture): <https://sre.google/sre-book/postmortem-culture/>
- GitLab Documentation Style Guide: <https://docs.gitlab.com/development/documentation/styleguide/>
- k16shikano「japanese-tech-writing」(日本語文章規範の原典、Unlicense): <https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d>
- Michael Nygard「Documenting Architecture Decisions」(ADRの原型)
