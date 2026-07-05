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

バージョニング・検証・配布は `gh skill` 自身の機能（タグ/リリース・`publish`・
`install`/`update`/`--pin`）に任せます。このリポジトリ側では車輪の再発明をしません。

## Skill の構造

Agent Skills 仕様に従い、各 Skill は次の構造を取ります。

```text
skills/<skill-name>/
├── SKILL.md          # 必須。frontmatter (name, description) + 本体
├── scripts/          # 任意。実行可能なヘルパースクリプト
├── references/        # 任意。詳細情報（プログレッシブディスクロージャ用）
└── assets/           # 任意。テンプレート・画像などの静的ファイル
```

- `SKILL.md` の frontmatter の `name` は、ディレクトリ名 `<skill-name>` と**必ず一致**させる。
- `SKILL.md` は目安として **約500行 / 5000語以内**に収める。それを超える詳細は
  `references/` 以下のファイルに逃がし、`SKILL.md` からリンクする
  （プログレッシブディスクロージャ）。
- 命名規則やfrontmatterの詳細は [references/conventions.md](references/conventions.md) を参照。

## 開発フロー(作成 → 複数端末同期まで)

### 1. ブランチ作成

`main` から `skill/<name>` ブランチを作成する。

```bash
git switch -c skill/<name>
```

### 2. 雛形生成

`scripts/scaffold.sh` を使って `skills/<name>/SKILL.md` 一式を生成する。

```bash
.claude/skills/skill-development/scripts/scaffold.sh <name>
```

生成後、`SKILL.md` の `description` には具体的なトリガーフレーズ
（「〜したいときに使う」）を書く。曖昧な description は Skill が
正しくトリガーされない原因になる。

### 3. ローカル反復

`skills/<name>` をローカルの Claude Code ユーザースコープ Skill ディレクトリに
シンボリックリンクし、編集と動作確認をすばやく繰り返す。

```bash
ln -s "$(pwd)/skills/<name>" ~/.claude/skills/<name>
```

編集 → Claude Code を再起動 or 新規セッションでトリガー確認、を繰り返す。

### 4. PR前の実配布経路テスト

シンボリックリンクでの反復だけでは、実際に `gh skill install` /
`gh skill preview` が辿る経路（provenance・メタデータ注入・ファイル取得）は
確認できない。ブランチを push した後、使い捨てディレクトリで実際の
インストール経路を確認する。

```bash
# ブランチを push しておく
git push -u origin skill/<name>

# 使い捨てディレクトリで実インストールを試す
mkdir -p /tmp/gh-skill-test && cd /tmp/gh-skill-test
gh skill install halkn/skills "skills/<name>@skill/<name>" \
  --agent claude-code --scope project

# または、インストールせずに内容だけプレビューする
gh skill preview halkn/skills "skills/<name>@skill/<name>"

# 確認後は使い捨てディレクトリを削除する
cd - && rm -rf /tmp/gh-skill-test
```

`--scope project` はカレントのgitリポジトリ配下に、`--scope user` は
ホームディレクトリ配下（マシン全体）にインストールされる。

### 5. PR作成

`main` へ向けて PR を作成し、`PULL_REQUEST_TEMPLATE.md` のチェックリストを記入する。

### 6. CI

`.github/workflows/validate-skills.yml` が、変更された `SKILL.md` の
frontmatter 整合性（`name`/`description` の存在、`name` とディレクトリ名の一致）と
行数警告をチェックする。`gh skill publish` が担うagentskills.io仕様・
セキュリティ検証とは重複させず、CIでしか拾えない部分だけを見る。

### 7. 人間によるレビュー

レビュアーが `SKILL.md` の差分を直接読む。これがそのままセキュリティ的な
内容確認になる。必要なら、レビュアー自身も手順4と同じ方法で PR ブランチに対して
`gh skill preview` を実行できる。

### 8. マージ

`main` に squash merge する。`main` は「未確定・レビュー中」のラインであり、
利用者は `main` から直接 install しない。

### 9. リリースを切る

配布可能な安定版として公開するタイミングで、注釈付きタグを作成・push し、
そのタグから `gh skill publish` を実行する。

```bash
git switch main && git pull
git tag -a v0.2.0 -m "v0.2.0"
git push origin v0.2.0
gh skill publish --tag v0.2.0
```

タグはスキルごとに分けず、リポジトリ全体でのセマンティックバージョンを使う
（例: `v0.2.0`）。スキル数が増えて個別のライフサイクル管理が必要になった段階で
見直す。`gh skill publish` はagentskills.io仕様・リポジトリ設定
（tag protection・secret scanning・code scanning）を検証し、改ざん不能な
GitHub Release（provenance付き）を作成する。

### 10. 複数端末での同期

各マシン/ターミナルで実施する。

```bash
# 新規マシンでの初回install(ユーザースコープ = マシン全体で有効)
gh skill install halkn/skills --agent claude-code --scope user --all
# または特定のskillだけ
gh skill install halkn/skills "skills/<name>@v0.2.0" --agent claude-code --scope user

# ローカルでカスタマイズ済み、または勝手に変わってほしくないskillは --pin する
gh skill install halkn/skills "skills/<name>@v0.2.0" --agent claude-code --scope user --pin v0.2.0

# 定期的に(当面は手動)、pinされていない新しいリリースを取り込む
gh skill update --agent claude-code --scope user
```

新リリースは各マシンが `gh skill update` を実行するまで反映されない
(自動pushされない)ため、各端末のskill構成は常に明示的・再現可能な状態を保てる。

## PRチェックリスト

- [ ] frontmatterの`name`がディレクトリ名と一致している
- [ ] `description`に具体的なトリガーフレーズが含まれる
- [ ] ローカルで動作確認済み(symlinkまたは使い捨てinstall)
- [ ] `SKILL.md`が行数目安(約500行)以内、または詳細を`references/`に退避済み
- [ ] 秘密情報や難読化されたスクリプトが含まれていない(previewしても安全)

詳細は `.github/PULL_REQUEST_TEMPLATE.md` と連動している。
