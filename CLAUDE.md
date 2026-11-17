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
  (`scripts/validate-internal-skills.py` が真偽値の `true` であることまで検証する)。
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

`vercel-labs/skills` 1.8.1 のREADME・docs/commands.md で確認した内容。

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

- `.github/workflows/ci.yml`(全PR): Markdown(`rumdl`)・shellscriptの静的検査とフォーマット
  (`shuck`)・YAMLの静的検査とフォーマット(`ryl`)に加え、配布経路ごとの検査を行う。
  - `frontmatter`: `uv run scripts/validate-internal-skills.py` で `.claude/skills/*/SKILL.md` のfrontmatter(YAMLとして読めること・name とディレクトリ名の一致・description の有無・`metadata.internal` が真偽値の `true` であること)を検証する。`gh skill` は隠しディレクトリを見ないため、ここだけ専用スクリプトを持つ
  - `distribution-gh`: `gh skill publish --dry-run` でagentskills.io仕様を検証する(`skills/*/SKILL.md` の name の命名規則・name とディレクトリ名の一致・name/description の有無)
  - `distribution-npx`: `scripts/check-npx-skills.sh` で、`npx skills` で入るskillが `skills/` 配下と過不足なく一致するかを見る(`.claude/skills/` の混入を検出する)
- `.github/workflows/release.yml`(`main` へのpushで `skills/**` が変わったとき、または手動。手動でも `main` 以外では動かない): `scripts/next-version.sh` で版を決め、`gh skill publish --tag` でタグとReleaseを作る(タグを先にpushすると `publish` が既存タグとして拒否する)。版はPRタイトル(squash mergeのコミット件名)の種別で決まる。

`gh` は `.github/actions/setup-gh` で版を固定して入れる(ランナー同梱の `gh` は版が固定されないため)。
版を上げるときは、同じ action の `sha256-*` もその版の `gh_<version>_checksums.txt` の値に直す。
サードパーティの gh セットアップ action はダウンロードしたバイナリのハッシュを検証しないため使わない(`release.yml` は `contents: write` のトークンで `gh` を動かす)。
uv は `astral-sh/setup-uv` の `version` で、`validate-internal-skills.py` の依存(PyYAML)はスクリプト先頭のinline metadataで版を固定する。
`rumdl`・`shuck`・`ryl` はそれぞれ公式の action(`rvben/rumdl`・`ewhauser/shuck-action`・`owenlamont/ryl-action`)で入れ、版は `ci.yml` で固定する。
`npx skills` の版は `ci.yml` の `SKILLS_CLI_VERSION` で固定する。上の「npx skills CLIの構文」節を確かめた版と揃える。

ワークフローと composite action の `uses:` は、ローカルの action(`./` で始まるもの)を除き、公式の `actions/*` も含めて40桁のコミットSHAで固定する。
タグはあとから別のコミットに付け替えられるため、タグ参照では action 本体の改ざんを防げない。
SHA の後ろには、そのコミットを指す完全な版のタグを `# vX.Y.Z` の形でコメントに残す(メジャータグ `v1` などは書かない)。
SHA は `git ls-remote --tags https://github.com/<owner>/<repo>.git` で、注釈付きタグなら `^{}` の行(タグが指すコミット)の値を使う。
更新は `.github/dependabot.yml`(`github-actions` エコシステム、週1回、全 action を1つのPRにまとめる)に任せる。Dependabot は SHA とタグのコメントを一緒に書き換える。公開から7日経っていない版は取り込まない(`cooldown`。version updates にだけ効き、security updates には効かない)。
Dependabot が上げるのは action 本体だけで、action の入力で固定したツールの版(`rvben/rumdl` の `version`、`ewhauser/shuck-action` の `shuck-version`、`astral-sh/setup-uv` の `version`)は変わらないので、必要なら手で上げる。
例外として `owenlamont/ryl-action` は `version` を指定せず action の版で ryl の版が決まるため、action の更新で ryl の版も上がる。

`.rumdl.toml` でMD013(行長制限)は無効化している(日本語の文章は1行1段落で書く方針のため)。

ローカルで同じ検証をする場合(`gh`(2.90.0以降)・`uv`・`rumdl`・`shuck`・`ryl` が必要):

```bash
gh skill publish --dry-run
uv run scripts/validate-internal-skills.py
scripts/check-npx-skills.sh   # Node.js 22.20以降が必要
rumdl check .
shuck check .
shuck format --check .
ryl check .
ryl format --check --markdown .
```

新しいshellscriptを書いたら `shuck format <file>` で整形してからコミットする。
YAMLとMarkdown内のYAML(frontmatterとyamlのコードブロック)は `ryl format --markdown .` で整形する。
`--markdown` は `ryl format` にだけ付け、`.ryl.toml` の `[files].markdown` には書かない(書くと `ryl check` の対象にもMarkdownが入る)。

`shuck.toml`(Google Shell Style Guide準拠)と`.ryl.toml`はリポジトリ直下に置く。どちらのツールも
ユーザーグローバル設定とプロジェクト設定をマージせず、設定が無いと既定のルールが空
(`ryl`)・別のスタイル(`shuck`のタブ整形)になるため、リポジトリ側に持たないとCIとローカルで
結果がずれる。

## ローカルでのフック

`.claude/settings.json` のPostToolUseフック(Write|Edit)で
`scripts/check-skills-hook.sh` が走り、編集したファイルが `SKILL.md` のときだけfrontmatterの不整合をその場で検知する。
`skills/*/SKILL.md` は `gh skill publish --dry-run`(CIの `distribution-gh` と同じ)、`.claude/skills/*/SKILL.md` は `scripts/validate-internal-skills.py`(CIの `frontmatter` と同じ)で見る。
`gh skill` を持たない `gh`(2.90.0未満)や `uv` が無い環境では、検証できなかったことをユーザーに通知して(終了コード1)編集は止めない。
