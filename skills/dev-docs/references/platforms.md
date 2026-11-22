# 置き場所ごとの記法

文書を置く場所で変わる書き方。どちらにも当てはまらない置き場所（Confluence など）では、利用者に記法を確かめる。

## 置き場所の決め方

1. 依頼に置き場所があればそれに従う（「ADO Wiki に載せる」「GitHub の docs/ に置く」）。
2. 書く先のファイルが Wiki のリポジトリ（`.order` があるフォルダ、リポジトリ名が `<Project>.wiki`）にあれば ADO Wiki。
3. 作業ディレクトリの push 先の URL（`git remote -v` の push の行）が `dev.azure.com`・`ssh.dev.azure.com`・`*.visualstudio.com` なら ADO Wiki（コードを Wiki として公開している前提）、`github.com` なら GitHub。
4. 決まらなければ GitHub の記法で書き、置き場所を決めずに書いたと報告する。

## Azure DevOps Wiki

出典: <https://learn.microsoft.com/en-us/azure/devops/project/wiki/markdown-guidance>、<https://learn.microsoft.com/en-us/azure/devops/project/wiki/wiki-file-structure>

- **Mermaid は ```` ```mermaid ```` で書く**：docs は `::: mermaid` 〜 `:::` の形も挙げるが、GitHub と同じコードブロックの形を使う。置き場所を移しても書き直さずに済み、エディタの表示も効く。書き直す節に `::: mermaid` があれば ```` ```mermaid ```` に直す。

- **流れの図は `graph` で書く**：ADO の Mermaid は `flowchart` の構文を受け付けない（docs の制約）。`graph TD` / `graph LR` を使う。長い矢印（`---->`）、HTML タグ、Font Awesome も使わない。

- **表示できる図の種類**：`sequenceDiagram`、`gantt`、`graph`、`classDiagram`、`stateDiagram`、`journey`、`pie`、`requirementDiagram`、`gitGraph`、`erDiagram`、`timeline`。状態の図は `stateDiagram-v2` ではなく docs の挙げる `stateDiagram` で書く。これ以外（C4 系、`block-beta`、`architecture-beta`、`xychart-beta`、`packet-beta`、`mindmap` など）は docs の一覧に無く、表示を当てにできないので使わない。[figures.md](figures.md) の「図の一覧」の種類は次のように描き替える。

  | 一覧の種類 | ADO Wiki での描き方 |
  |---|---|
  | `flowchart` | `graph`（向きはそのまま。`flowchart LR` → `graph LR`） |
  | `stateDiagram-v2` | `stateDiagram` |
  | `C4Context`・`C4Container`・`C4Component`・`C4Deployment`・`architecture-beta` | `graph` と `subgraph`（境界・環境・入れ子を `subgraph` で表す） |
  | `C4Dynamic` | `graph`（矢印のラベルに呼ぶ順の番号を付ける） |
  | `block-beta` | `graph TB` と `subgraph`（層を上から積む） |
  | `xychart-beta` | 描けない。画像にして `.attachments` に置き、リンクする |

- **目次は `[[_TOC_]]`**：大文字で書く。目次が要るのは見出しが多い設計書と Runbook。

- **ページのファイル名はページの題になる**：題の空白はファイル名で `-` にする（「障害対応の手順」→ `障害対応の手順.md`、「How to deploy」→ `How-to-deploy.md`）。`/`・`\`・`#` は使えず、`.` で始めたり終えたりしない。

- **ページの順は `.order` で決まる**：新しいページを足したら、同じフォルダの `.order` に1行1ページでファイル名（拡張子なし）を足す。`.order` が無いフォルダは名前の順に並ぶ。

- **ページへのリンク**：同じ Wiki のページは相対パスで書く（`[手順](./Runbook/再起動.md)`）。

## GitHub

- **Mermaid は ```` ```mermaid ```` で囲む**。`flowchart` も C4 系も表示される。
- **目次は書かない**：GitHub が見出しから目次を作る。
- **ADR の置き場所**：既存の ADR のフォルダ（`docs/adr/`、`docs/decisions/` など）があればそれに従い、番号を続ける。無ければ `docs/adr/NNNN-<題>.md` にする。
- **README**：リポジトリ直下の `README.md`。下のフォルダの README は、そのフォルダの入口として書く。
