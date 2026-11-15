# 命名・frontmatter規約

`.claude/skills/skill-development/SKILL.md` の詳細ルール集。プログレッシブディスクロージャの
ため、頻繁に参照しない詳細をここに切り出している。

## ディレクトリ名とfrontmatter `name`

- ディレクトリ名は `skills/<skill-name>/` の形。`<skill-name>` は小文字・数字・
  ハイフンのみ(kebab-case)。例: `pdf-fill-form`, `skill-development`。
- frontmatterの `name` は、ディレクトリ名と**完全一致**させる。この一致は
  `scripts/validate-skill-frontmatter.sh`（CIとローカルフックで共有）で検証される。
- `gh skill install owner/repo skills/<name>` はこのディレクトリ構造を前提に
  スキルを解決するため、不一致があるとインストールに失敗する。

## リポジトリ専用skill(`.claude/skills/`)

- `gh skill` は隠しディレクトリを既定でスキップするが、`npx skills` は `.claude/skills/` も探索する。
- そのため `.claude/skills/<name>/SKILL.md` には次を付け、`npx skills` の一括インストール(`--skill '*'`)の対象から外す。
  `INSTALL_INTERNAL_SKILLS=1` を付けたとき、または `--skill <name>` で名前を明示したときは入る(skills 1.8.1 の `src/add.ts` で確認)。
  名前の明示までは防げないので、リポジトリ専用skillを端末に入れないのは利用者側の運用になる。
- 値は YAML の真偽値 `true` にする。文字列の `"true"` を internal とみなさない版がある(1.7.4)。

  ```yaml
  metadata:
    internal: true
  ```

- 付け忘れは `scripts/validate-skill-frontmatter.sh`(フック・CI)で検出する。

## frontmatterのフィールド

必須は `name` と `description`。`license` は推奨。

```yaml
---
name: <skill-name>
license: MIT
description: >
  いつ使うかを具体的なトリガーフレーズで書く。
---
```

- `name`: 上記の通り、ディレクトリ名と一致。
- `description`: 「何をするか」ではなく「いつ使うか」を書く。Claude Codeは
  このdescriptionだけを見てskillをトリガーするかどうか判断するため、
  曖昧な説明はトリガー漏れ・誤トリガーの原因になる。
  - 悪い例: `description: PDFを扱うためのskill`
  - 良い例: `description: ユーザーがPDFフォームに入力・記入したいときに使う`
- `license`: 必須ではないが、`gh skill publish` が推奨項目として無いと警告する(gh 2.103.2 で確認)。
  リポジトリの LICENSE に合わせて `MIT` を書く。
- `allowed-tools` を指定する場合は文字列で書く(配列ではない)。
  `gh skill publish` はこの形式を検証する(PRのCIで `--dry-run` を実行する)。

## 行数・プログレッシブディスクロージャの目安

- `SKILL.md` 本体は約500行 / 5000語以内を目安にする。
- 超える場合は、詳細情報を `references/*.md` に切り出し、`SKILL.md` からは
  「詳細は references/xxx.md を参照」とだけリンクする。
- `SKILL.md` は常に読み込まれる前提のファイル、`references/` は必要になった
  ときだけ読みに行くファイル、という役割分担を意識する。
- 行数はCIで検証しない。強制分割がかえって読みにくくなるケースもあるため、
  最終判断はレビュアーに委ねる。

## scripts/ と assets/

- `scripts/`: 実行可能なヘルパースクリプト。シェバン行を書き、実行権限
  (`chmod +x`)を付与する。
- `assets/`: テンプレートファイルや画像など、スクリプトではない静的ファイル。
- どちらも必須ではない。使わない場合はディレクトリごと作らない
  (空の `.gitkeep` だけのディレクトリを残さない)。

## セキュリティレビューの観点

`gh skill`・`npx skills` はSKILL.md本体だけでなく `scripts/` 配下の
スクリプトも取得・実行され得る。PRレビュー時は以下を確認する。

- スクリプトが難読化されていない(人間が読んで内容を理解できる)。
- 秘密情報(トークン・APIキーなど)がハードコードされていない。
- 外部URLへの不審な通信(データ持ち出し)を行っていない。
