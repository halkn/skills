---
name: skill-development
description: >
  halkn/skillsリポジトリで新しいAgent Skillを作成・改善・リリースするときの手順。
  skillを追加/編集したい、gh skillやnpx skillsで配布したい、複数端末に同期したい、というときに使う。
metadata:
  internal: true
---

# skill-development

`halkn/skills` は、`gh skill`（GitHub CLI）と `npx skills`（Vercel の Skills CLI）の2経路で
複数端末に Skill を配布・同期するためのリポジトリです。このドキュメントは、このリポジトリで
Skill を作る・育てる・配布するときの手順そのものです。人間が読む開発者向けドキュメント
としても、Claude Code がこのリポジトリで作業する際にトリガーされる Skill としても機能します。

検証・配布・更新は両CLIの機能に任せ、リポジトリ側では再実装しません。リポジトリ側が持つのは、
「両CLIで同じskillが入ること」を確かめるCIと、`skills/` の変更ごとにリリースを作るCDだけです。

## 配布の仕組み

| 段階 | 仕組み | 定義 |
|------|--------|------|
| PR | Markdown・shell・YAML の静的検査、`gh skill publish --dry-run`(frontmatter の検証を兼ねる)、`npx skills` で入るskillが `skills/` と一致するかの検査 | `.github/workflows/ci.yml` |
| main へのマージ | `skills/**` が変わったときだけ、`scripts/next-version.sh` で版を決め、`gh skill publish --tag` でタグと Release を作る | `.github/workflows/release.yml` |
| 各端末 | `gh skill update --all` または `npx skills update --global --yes` を実行したときだけ反映される | README |

- `gh skill` は版を指定しないと「最新のリリース → `main` の HEAD」、`npx skills` は `main` の HEAD を入れる。`skills/` の変更ごとにリリースするので、両者の内容は一致する。
- `skills/` 以外（README・CI・`.claude/` など）だけの変更ではリリースしない。配布物が変わらないため。
- `npx skills` は `skills/` に加えて `.claude/skills/` なども探索する。リポジトリ専用skillには frontmatter に `metadata.internal: true` を付けて配布対象から外す。付け忘れは CI の `distribution-npx` ジョブで検出する。

### 版の決め方

`scripts/next-version.sh` が、直近の `v*` タグ以降に `skills/` を変えたコミットの件名から決める。
squash merge なので、件名は PR タイトルになる。

- タグが無い: `v0.1.0`
- `feat:` / `add:` で始まる、または破壊的変更（`type!:`）を含む: minor を上げる（1.0.0 以降の破壊的変更は major）
- それ以外: patch を上げる

手動でリリースし直したいときは、Actions の Release ワークフローを `workflow_dispatch` で実行する。
前回のタグ以降に `skills/` の変更が無ければ何もしない。

## Skill の構造

Agent Skills 仕様に従い、各 Skill は次の構造を取ります。

```text
skills/<skill-name>/
├── SKILL.md          # 必須。frontmatter (name, description) + 本体
├── scripts/          # 任意。実行可能なヘルパースクリプト
├── references/       # 任意。詳細情報（プログレッシブディスクロージャ用）
└── assets/           # 任意。テンプレート・画像などの静的ファイル
```

- `SKILL.md` の frontmatter の `name` は、ディレクトリ名 `<skill-name>` と**必ず一致**させる。
- `SKILL.md` は目安として **約500行 / 5000語以内**に収める。それを超える詳細は
  `references/` 以下のファイルに逃がし、`SKILL.md` からリンクする
  （プログレッシブディスクロージャ）。
- 命名規則やfrontmatterの詳細は [references/conventions.md](references/conventions.md) を参照。

## 開発フロー

### 1. ブランチ作成と雛形生成

```bash
git switch -c skill/<name>
.claude/skills/skill-development/scripts/scaffold.sh <name>
```

生成後、`SKILL.md` の `description` には具体的なトリガーフレーズ
（「〜したいときに使う」）を書く。曖昧な description は Skill が
正しくトリガーされない原因になる。

### 2. ローカルで試す

`skills/<name>` をユーザースコープの Skill ディレクトリにシンボリックリンクし、
編集と動作確認をすばやく繰り返す。

```bash
ln -s "$(pwd)/skills/<name>" ~/.claude/skills/<name>
```

編集 → Claude Code の新規セッションでトリガー確認、を繰り返す。確認が済んだら
リンクを外す（`rm ~/.claude/skills/<name>`）。

sandbox で `~/.claude/skills` への書き込みを禁じている環境では、Claude はリンクの作成・
削除を実行できない。コマンドを提示し、ユーザーに `!` 付きで実行してもらう。

配布経路での入り方まで確かめたいときは、次を使う。

```bash
# npx skills で入るskillの一覧(CI の distribution-npx と同じ検査)
scripts/check-npx-skills.sh

# gh skill が辿る経路(provenance・メタデータ注入・ファイル取得)。ブランチの push が必要
gh skill preview halkn/skills "skills/<name>@skill/<name>"
```

### 3. PR作成・CI・マージ

`main` へ向けて PR を作成し、`PULL_REQUEST_TEMPLATE.md` のチェックリストを記入する。
PR タイトルは版の決定に使うので、`feat:`/`add:`/`fix:` などの種別を付ける（「版の決め方」参照）。
CI（`.github/workflows/ci.yml`）の内容は CLAUDE.md の「CI/CD」節にある。

レビュアーは `SKILL.md` の差分を直接読む。これがそのままセキュリティ的な内容確認になる。
確認できたら `main` に squash merge する。`skills/` が変わっていれば Release ワークフローが
タグと Release を作る。

### 4. 各端末に取り込む

各端末では、`gh skill` か `npx skills` のどちらか一方だけを使う。どちらも
`~/.claude/skills/<name>` に入れるため、混ぜると片方の更新がもう片方の管理外のファイルを上書きする。

```bash
# gh skill: 初回 / 更新
gh skill install halkn/skills --agent claude-code --scope user --all
gh skill update --all

# npx skills: 初回 / 更新
npx skills add halkn/skills --global --agent claude-code --skill '*' --yes
npx skills update --global --yes
```

`gh skill update` にスコープ/エージェントを指定するフラグは無く、既知のホスト
ディレクトリを project/user 両スコープとも自動で走査する（`gh` 2.103.2 で確認）。
どちらの経路でも、新リリースは各端末で update を実行するまで反映されない（自動pushされない）。

版を固定したいときは、`gh skill` は `skills/<name>@vX.Y.Z` または `--pin <tag-or-sha>`、
`npx skills` は `halkn/skills@vX.Y.Z` を使う。

## PRチェックリスト

- [ ] frontmatterの`name`がディレクトリ名と一致している
- [ ] `description`に具体的なトリガーフレーズが含まれる
- [ ] ローカルで動作確認済み(symlink・`scripts/check-npx-skills.sh`・`gh skill preview` のいずれか)
- [ ] `SKILL.md`が行数目安(約500行)以内、または詳細を`references/`に退避済み
- [ ] 秘密情報や難読化されたスクリプトが含まれていない(previewしても安全)
- [ ] PRタイトルに種別(`feat:`/`add:`/`fix:` など)が付いている

詳細は `.github/PULL_REQUEST_TEMPLATE.md` と連動している。
