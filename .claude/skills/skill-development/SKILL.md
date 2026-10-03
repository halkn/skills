---
name: skill-development
description: >
  halkn/skillsリポジトリで新しいAgent Skillを作成・改善・リリースするときの手順。
  skillを追加/編集したい、gh skillで配布したい、複数端末に同期したい、というときに使う。
---

# skill-development

`halkn/skills` は、`gh skill`（GitHub CLI の Agent Skills 配布機能）経由で複数端末に
Skill を配布・同期するためのリポジトリです。このドキュメントは、このリポジトリで
Skill を作る・育てる・配布するときの手順そのものです。人間が読む開発者向けドキュメント
としても、Claude Code がこのリポジトリで作業する際にトリガーされる Skill としても機能します。

バージョニング・検証・配布は `gh skill` 自身の機能に任せます。このリポジトリ側では
車輪の再発明をしません。

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

`gh skill install` が辿る実際の経路（provenance・メタデータ注入・ファイル取得）まで
確認したいときだけ、ブランチを push してから使い捨てディレクトリで試す。

```bash
gh skill preview halkn/skills "skills/<name>@skill/<name>"
```

### 3. PR作成・CI・マージ

`main` へ向けて PR を作成し、`PULL_REQUEST_TEMPLATE.md` のチェックリストを記入する。
`.github/workflows/lint.yml` が `skills/*/SKILL.md` の frontmatter 整合性
（`name`/`description` の存在、`name` とディレクトリ名の一致）と Markdown・
shellscript の静的検査を実行する。`gh skill publish` が担うagentskills.io仕様・
セキュリティ検証とは重複させず、CIでしか拾えない部分だけを見る。

レビュアーは `SKILL.md` の差分を直接読む。これがそのままセキュリティ的な内容確認になる。
確認できたら `main` に squash merge する。

### 4. 各端末に取り込む

マージ後、各マシンで更新を取り込む。

```bash
# 初回のみ（ユーザースコープ = マシン全体で有効）
gh skill install halkn/skills --agent claude-code --scope user --all

# 以降の更新
gh skill update --all
```

`gh skill update` にスコープ/エージェントを指定するフラグは無く、既知のホスト
ディレクトリを project/user 両スコープとも自動で走査する（`gh` 2.97.0 で確認）。
新リリースは各マシンが `gh skill update` を実行するまで反映されない（自動pushされない）
ため、各端末のskill構成は常に明示的・再現可能な状態を保てる。

## タグ/リリース（必要になったら）

バージョンを指定せずにインストールした場合、`gh skill` は「最新のタグ付きリリース →
デフォルトブランチのHEAD」の順で解決する（`gh` 2.97.0 で確認）。現状このリポジトリは
タグを切っていないため、利用者には `main` の HEAD が入る。

「複数端末で同じ状態に固定したい」「壊れた変更を踏みたくない」という要求が出た時点で、
リポジトリ全体のセマンティックバージョン（skill個別ではない）でタグを切り、リリースする。

```bash
git switch main
git fetch origin
git merge --ff-only origin/main
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
gh skill publish --tag v0.1.0
```

`gh skill publish` はagentskills.io仕様・リポジトリ設定（tag protection・secret scanning・
code scanning）を検証し、provenance付きのGitHub Releaseを作成する。個別のskillを固定
したいだけなら、タグを切らずに `gh skill install ... --pin <sha>` でも足りる。

## PRチェックリスト

- [ ] frontmatterの`name`がディレクトリ名と一致している
- [ ] `description`に具体的なトリガーフレーズが含まれる
- [ ] ローカルで動作確認済み(symlinkまたは`gh skill preview`)
- [ ] `SKILL.md`が行数目安(約500行)以内、または詳細を`references/`に退避済み
- [ ] 秘密情報や難読化されたスクリプトが含まれていない(previewしても安全)

詳細は `.github/PULL_REQUEST_TEMPLATE.md` と連動している。
