# 命名・frontmatter規約

`.claude/skills/skill-development/SKILL.md` の詳細ルール集。プログレッシブディスクロージャの
ため、頻繁に参照しない詳細をここに切り出している。

## ディレクトリ名とfrontmatter `name`

- ディレクトリ名は `skills/<skill-name>/` の形。`<skill-name>` は小文字・数字・
  ハイフンのみ(kebab-case)。例: `pdf-fill-form`, `skill-development`。
- frontmatterの `name` は、ディレクトリ名と**完全一致**させる。この一致は
  `.github/workflows/validate-skills.yml` でCI検証される。
- `gh skill install owner/repo skills/<name>` はこのディレクトリ構造を前提に
  スキルを解決するため、不一致があるとインストールに失敗する。

## frontmatterの必須フィールド

```yaml
---
name: <skill-name>
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
- `allowed-tools` を指定する場合は文字列で書く(配列ではない)。
  `gh skill publish` はこの形式を検証する。

## 行数・プログレッシブディスクロージャの目安

- `SKILL.md` 本体は約500行 / 5000語以内を目安にする。
- 超える場合は、詳細情報を `references/*.md` に切り出し、`SKILL.md` からは
  「詳細は references/xxx.md を参照」とだけリンクする。
- `SKILL.md` は常に読み込まれる前提のファイル、`references/` は必要になった
  ときだけ読みに行くファイル、という役割分担を意識する。
- CIはこの行数を超えても失敗させない(非ブロッキング警告のみ)。強制分割が
  かえって読みにくくなるケースもあるため、最終判断はレビュアーに委ねる。

## scripts/ と assets/

- `scripts/`: 実行可能なヘルパースクリプト。シェバン行を書き、実行権限
  (`chmod +x`)を付与する。
- `assets/`: テンプレートファイルや画像など、スクリプトではない静的ファイル。
- どちらも必須ではない。使わない場合はディレクトリごと作らない
  (空の `.gitkeep` だけのディレクトリを残さない)。

## セキュリティレビューの観点

`gh skill preview`/`gh skill install` はSKILL.md本体だけでなく `scripts/` 配下の
スクリプトも取得・実行され得る。PRレビュー時は以下を確認する。

- スクリプトが難読化されていない(人間が読んで内容を理解できる)。
- 秘密情報(トークン・APIキーなど)がハードコードされていない。
- 外部URLへの不審な通信(データ持ち出し)を行っていない。
