# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## リポジトリの目的

`halkn/skills` は、Claude Code用のAgent Skillを複数端末に配布・同期するためのリポジトリ。
配布経路は `gh skill`(GitHub CLI)と `npx skills`(Vercelの Skills CLI、npmパッケージ `skills`)の2つ。
検証・配布・更新は両CLIの機能(`publish`・`install`/`add`・`update`・版の固定)に任せ、リポジトリ側では
再実装しない。リポジトリ側が持つのは、両CLIで同じskillが入ることを確かめるCIと、`skills/` の変更ごとに
リリースを作るCDだけ。

## ディレクトリの使い分け

- `skills/<name>/SKILL.md` — 配布対象。`gh skill install`/`gh skill publish` が発見する。
  frontmatterの `name` はディレクトリ名と完全一致させる。
- `.claude/skills/<name>/SKILL.md` — このリポジトリ専用のツール(例: `skill-development`)。
  `gh skill` は既定で隠しディレクトリをスキップするが、`npx skills` は `.claude/skills/` も探索する。
  そのためfrontmatterに `metadata.internal: true` を必ず付けて `npx skills` の配布対象から外す
  (`scripts/validate-skill-frontmatter.sh` が検証する)。
- `scripts/` (リポジトリ直下) — Claude Codeのhookなど、特定のskillに属さないリポジトリ全体の
  ツール置き場。skill固有のスクリプトは`skills/<name>/scripts/`や
  `.claude/skills/<name>/scripts/`に置く。

新しいskillの作成・改善・リリース手順は `.claude/skills/skill-development/SKILL.md` に集約している。
この手の作業を頼まれたら、まずそちらを参照する。開発フローを別立てのDEVELOPMENT.mdや
CONTRIBUTING.mdに分離しない方針(単一skillへの集約が意図的な設計)。

skill品質をevalで検証したい場合は `skills/<name>/evals/evals.json` に配置する(例:
`skills/git-flow/evals/evals.json`)。実行・評価は`skill-creator`スキル(`skill-creator:skill-creator` プラグイン)に委ねる。

## gh skill CLIの構文(要注意)

ドキュメントやIssue上の想定と、実際の `gh skill`(2.103.2で確認)は以下が異なる。想定で書かない。

- `--scope` の値は `project` または `user`(`repository` ではない)
- バージョン指定は `skill-path@version` の形(例: `skills/foo@v1.0.0`)。`owner/repo@version` ではない
- `gh skill preview` に `--ref` フラグは存在しない。同様に `skill@branch` 形式で指定する
- `gh skill update` に `--agent`/`--scope` は無い。project/user両スコープを自動走査する
- バージョン未指定時の解決順は「最新のタグ付きリリース → デフォルトブランチのHEAD」

## npx skills CLIの構文(要注意)

`vercel-labs/skills` のREADME・docs/commands.md(2026-11時点、npm最新は1.8.1)で確認した内容。

- インストール先の既定はプロジェクト(`./.claude/skills/`)。ユーザースコープは `--global`(`~/.claude/skills/`)
- skillの指定は `--skill <name>`(全部は `--skill '*'`)、エージェントは `--agent claude-code`
- 版の固定は `owner/repo@<tag-or-commit>`(`gh skill` の `skill-path@version` とは形が違う)
- 更新は `npx skills update [--global|--project] [--yes]`
- 探索対象は `skills/`・`.claude/skills/`・`.agents/skills/` などで、隠しディレクトリも含む
- 匿名の利用統計を送る。`DISABLE_TELEMETRY=1` で止まる

## PRのマージ方針

`main` へのマージは squash merge(`gh pr merge --squash`)。`skills/git-flow` スキルの既定
(通常merge)をこのリポジトリでは上書きする。

## CI/CD

ワークフローは2本。

- `.github/workflows/ci.yml`(全PR): `skills/*/SKILL.md` と `.claude/skills/*/SKILL.md` のfrontmatter検証
  (`scripts/validate-skill-frontmatter.sh`)・Markdown(`rumdl`)・shellscriptの静的検査とフォーマット
  (`shuck`)・YAML(`ryl`)に加え、配布経路ごとの検査を行う。
  - `distribution-gh`: `gh skill publish --dry-run` でagentskills.io仕様を検証する
  - `distribution-npx`: `scripts/check-npx-skills.sh` で、`npx skills` で入るskillが `skills/` 配下と過不足なく一致するかを見る(`.claude/skills/` の混入を検出する)
- `.github/workflows/release.yml`(`main` へのpushで `skills/**` が変わったとき、または手動。手動でも `main` 以外では動かない): `scripts/next-version.sh` で版を決め、`gh skill publish --tag` でタグとReleaseを作る(タグを先にpushすると `publish` が既存タグとして拒否する)。版はPRタイトル(squash mergeのコミット件名)の種別で決まる。

`gh` は `.github/actions/setup-gh` で版を固定して入れる(ランナー同梱の `gh` は版が固定されないため)。
版を上げるときは、同じ action の `sha256-*` もその版の `gh_<version>_checksums.txt` の値に直す。
`npx skills` の版は `ci.yml` の `SKILLS_CLI_VERSION` で固定する。上の「npx skills CLIの構文」節を確かめた版と揃える。

`.rumdl.toml` でMD013(行長制限)は無効化している(日本語の文章は1行1段落で書く方針のため)。

ローカルで同じ検証をする場合(`yq`(mikefarah版)・`rumdl`・`shuck`・`ryl` が必要):

```bash
scripts/validate-skill-frontmatter.sh
scripts/check-npx-skills.sh   # Node.js 22.20以降が必要
rumdl check .
shuck check .
shuck format --check .
ryl check .
```

新しいshellscriptを書いたら `shuck format <file>` で整形してからコミットする。

`shuck.toml`(Google Shell Style Guide準拠)と`.ryl.toml`はリポジトリ直下に置く。どちらのツールも
ユーザーグローバル設定とプロジェクト設定をマージせず、設定が無いと既定のルールが空
(`ryl`)・別のスタイル(`shuck`のタブ整形)になるため、リポジトリ側に持たないとCIとローカルで
結果がずれる。

## ローカルでのフック

`.claude/settings.json` のPostToolUseフック(Write|Edit)で
`scripts/validate-skill-frontmatter.sh` が走り、frontmatterの不整合をその場で検知する。
CIと同じスクリプトなので、検証ルールを変えるときの同期先はこの1ファイルだけ。
