# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## リポジトリの目的

`halkn/skills` は、Claude Code用のAgent Skillを `gh skill`(GitHub CLIのAgent Skills配布機能)経由で
複数端末に配布・同期するためのリポジトリ。バージョニング・検証・配布は `gh skill` 自身の機能
(タグ/リリース・`publish`・`install`/`update`/`--pin`)に任せ、リポジトリ側では再実装しない。

## ディレクトリの使い分け

- `skills/<name>/SKILL.md` — 配布対象。`gh skill install`/`gh skill publish` が発見する。
  frontmatterの `name` はディレクトリ名と完全一致させる。
- `.claude/skills/<name>/SKILL.md` — このリポジトリ専用のツール(例: `skill-development`)。
  `gh skill` は既定でこのような隠しディレクトリをスキップするため配布物には含まれない
  (`--allow-hidden-dirs` を付けない限り)。
- `scripts/` (リポジトリ直下) — Claude Codeのhookなど、特定のskillに属さないリポジトリ全体の
  ツール置き場。skill固有のスクリプトは`skills/<name>/scripts/`や
  `.claude/skills/<name>/scripts/`に置く。

新しいskillの作成・改善・リリース手順は `.claude/skills/skill-development/SKILL.md` に集約している。
この手の作業を頼まれたら、まずそちらを参照する。開発フローを別立てのDEVELOPMENT.mdや
CONTRIBUTING.mdに分離しない方針(単一skillへの集約が意図的な設計)。

skill品質をevalで検証したい場合は `skills/<name>/evals/evals.json` に配置する(例:
`skills/github-flow/evals/evals.json`)。実行・評価は`empirical-prompt-tuning`スキルに委ねる。

## gh skill CLIの構文(要注意)

ドキュメントやIssue上の想定と、実際の `gh skill`(2.95系で確認)は以下が異なる。想定で書かない。

- `--scope` の値は `project` または `user`(`repository` ではない)
- バージョン指定は `skill-path@version` の形(例: `skills/foo@v1.0.0`)。`owner/repo@version` ではない
- `gh skill preview` に `--ref` フラグは存在しない。同様に `skill@branch` 形式で指定する

## PRのマージ方針

`main` へのマージは squash merge(`gh pr merge --squash`)。`skills/github-flow` スキルの既定
(通常merge)をこのリポジトリでは上書きする。

## CI

ローカル検証には `gh`(2.90+)・`yq`・`rumdl`・`shellcheck`・`shfmt` が必要。

`.github/workflows/validate-skills.yml` は `skills/**` の変更のみを対象に、SKILL.mdのfrontmatter
(`name`のディレクトリ名一致・`description`必須)を検証する。`.claude/skills/` は対象外(意図的)。

`.github/workflows/lint.yml` は全PRを対象に、Markdown(`rumdl`)・shellscriptの静的検査
(`shellcheck`)・shellscriptのフォーマット(`shfmt`, Google Shell Style Guide準拠)を検証する。
`.rumdl.toml` でMD013(行長制限)は無効化している(日本語の文章は1行1段落で書く方針のため)。

ローカルで同じ検証をする場合:

```bash
rumdl check .
shellcheck scripts/*.sh .claude/skills/*/scripts/*.sh
shfmt -i 2 -ci -bn -d scripts/*.sh .claude/skills/*/scripts/*.sh
```

新しいshellscriptを書いたら `shfmt -i 2 -ci -bn -w <file>` で整形してからコミットする。

## ローカルでのフック

`skills/*/SKILL.md` を編集すると、`scripts/validate-skill-frontmatter.sh` がPostToolUseフック
(`.claude/settings.json`)経由で自動実行され、frontmatterの不整合をその場で検知する。

このスクリプトと`.github/workflows/validate-skills.yml`内のロジックは共有されておらず、
別々に実装されている。検証ルール(name一致・description必須など)を変更する際は両方を
同期させること。
