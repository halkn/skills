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
複数端末に Skill を配布・同期するためのリポジトリです。claude.ai・Cowork 向けには、
`.claude-plugin/marketplace.json` でプラグインマーケットプレイスとしても公開しています。このドキュメントは、このリポジトリで
Skill を作る・育てる・配布するときの手順そのものです。人間が読む開発者向けドキュメント
としても、Claude Code がこのリポジトリで作業する際にトリガーされる Skill としても機能します。

検証・配布・更新は両CLIの機能に任せ、リポジトリ側では再実装しません。リポジトリ側が持つのは、
「両CLIで同じskillが入ること」を確かめるCIと、`skills/` の変更ごとにリリースを作るCDだけです。

## 配布の仕組み

| 段階 | 仕組み | 定義 |
|------|--------|------|
| PR | `.claude/skills/` の frontmatter 検証、Markdown・shell・YAML の静的検査、`gh skill publish --dry-run`(`skills/` の frontmatter の検証を兼ねる)、`npx skills` で入るskillが `skills/` と一致するかの検査、`claude plugin validate --strict .` でのマーケットプレイスの検証 | `.github/workflows/ci.yml` |
| main へのマージ | `skills/**` が変わったときだけ、`scripts/next-version.sh` で版を決め、`gh skill publish --tag` でタグと Release を作る | `.github/workflows/release.yml` |
| 各端末 | `gh skill update --all` または `npx skills update --global --yes` を実行したときだけ反映される | README |

- `gh skill` は版を指定しないと「最新のリリース → `main` の HEAD」、`npx skills` は `main` の HEAD を入れる。`skills/` の変更ごとにリリースするので、両者の内容は一致する。
- `skills/` 以外（README・CI・`.claude/` など）だけの変更ではリリースしない。配布物が変わらないため。
- `npx skills` は `skills/` に加えて `.claude/skills/` なども探索する。リポジトリ専用skillには frontmatter に `metadata.internal: true` を付けて配布対象から外す。付け忘れは `scripts/validate-internal-skills.py`(フック・CI の `frontmatter` ジョブ)と CI の `distribution-npx` ジョブで検出する。
- プラグイン `halkn` はリポジトリ直下を指し、既定の `skills/` の走査で入る skill が決まる。リポジトリ直下に `bin/`・`commands/`・`agents/`・`hooks/` などプラグインの既定の置き場所を作ると、プラグインの中身が変わる（`bin/` があると claude.ai と Cowork が入れない）。`version` を書かないので、claude.ai には `main` の commit がそのまま届く。

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
├── scripts/          # 任意。ヘルパースクリプト(呼び出しはインタプリタ経由)
├── references/       # 任意。詳細情報（プログレッシブディスクロージャ用）
└── assets/           # 任意。テンプレート・画像などの静的ファイル
```

- `SKILL.md` の frontmatter の `name` は、ディレクトリ名 `<skill-name>` と**必ず一致**させる。
- `SKILL.md` は目安として **約500行 / 5000語以内**に収める。それを超える詳細は
  `references/` 以下のファイルに逃がし、`SKILL.md` からリンクする
  （プログレッシブディスクロージャ）。
- 命名規則やfrontmatterの詳細は [references/conventions.md](references/conventions.md) を参照。
- `scripts/` のスクリプトは `bash ${CLAUDE_SKILL_DIR}/scripts/foo.sh` や `python3 ${CLAUDE_SKILL_DIR}/scripts/foo.py` のようにインタプリタ経由で呼ぶ(`allowed-tools` の `Bash(...)` も同じ形にする)。`gh skill install` は実行ビットを保持せず、全ファイルを `0644` で書き出すため、直接実行すると Permission denied になる。

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
# 配布済みの skill は ~/.claude/skills/<name> が実ディレクトリなので、先に skills/ の外へ退避する。
# 退避しないと ln -s はそのディレクトリの中にリンクを作り、インストール済みの版が読み込まれたままになる。
[ -d ~/.claude/skills/<name> ] && [ ! -L ~/.claude/skills/<name> ] && mv ~/.claude/skills/<name> ~/.claude/skill-backup-<name>
ln -s "$(pwd)/skills/<name>" ~/.claude/skills/<name>
```

編集 → Claude Code の新規セッションでトリガー確認、を繰り返す。確認が済んだら
リンクを外し（`rm ~/.claude/skills/<name>`）、退避したものがあれば
`mv ~/.claude/skill-backup-<name> ~/.claude/skills/<name>` で戻す。

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
claude.ai でプラグイン `halkn` を有効にすると、claude.ai のアカウントでサインインした Claude Code には
`halkn@synced` として同期され、同じ skill が2つ読み込まれる。止め方は README の claude.ai の節にある。

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

## 上流の取り込み

外部の skill を参考にして書いた、または外部の skill を名前で呼ぶ skill は、上流の記録をリポジトリ直下の `upstream/<name>.md` に置く。
配布物（`skills/`）に入れないのは、利用者の端末では使わないことと、記録だけを進める変更でリリースしないためである。
参考にする上流は写して同期せず、変更を見て、skill に影響するか参考になるものだけを skill の言葉で取り込む。上流の著作権表示は、参考にして書いたファイルと一緒に `skills/<name>/` に置く。

記録に書くこと:

- 参考にする上流: リポジトリとブランチ、最後に目を通したコミット SHA、追うパス、参考にしている点・採らない点（取り込むかを決める基準）
- 名前で呼ぶ上流: リポジトリ、確かめるファイル（ブランチとパス）、skill が頼る挙動の根拠になる記述とその理由。名前で呼ぶ上流は版を追わない

### 上流を確かめる

週1回（Claude のスケジュールタスクか手で）、`upstream/*.md` の上流ごとに次を確かめる。

- 参考にする上流: 最後に目を通したコミットからブランチの先頭までに、追うパスのファイル（フォルダなら配下）を変えたコミットがあるか。改名・移動で追うパスから外れたファイルも変更に数える。
- 名前で呼ぶ上流: 確かめるファイルに、頼る挙動の記述がすべて残っているか。

差がある上流ごとに Issue「上流の更新: <name>（<repo>）」を作る。同じ題の open な Issue があれば、作らずに本文を更新する。本文には、参考にする上流は追うパスに触れたコミットの一覧・変更ファイル・比較の URL を、名前で呼ぶ上流は見つからない記述と、それに頼っている理由・上流のファイルの URL を書く。差が無ければ何もしない。

### Issue を取り込む

Issue が来たら、次の順で進める。

1. Issue を読む。
2. 参考にする上流は、差分を見て、変更ごとに取り込むか見送るかを決める。skill の決まりと食い違う変更（skill に影響する）と、skill にも当てはまる新しい決まり（参考になる）を取り込み、`upstream/<name>.md` の採らない点に当たるものは見送る。名前で呼ぶ上流は、上流のファイルを読み、頼っていた挙動がまだあるかを確かめる。
3. 記録を更新する。参考にする上流は、取り込む変更を skill の言葉で skill のファイルに書き、`upstream/<name>.md` の最後に目を通したコミットを上流の先頭にする。Issue が追うパスの改名・移動を挙げていれば追うパスも直す。名前で呼ぶ上流は、挙動が無くなっていれば skill の呼び方を直し、言い回しが変わっただけなら記録の記述を新しい言い回しに直す。参考にしている点・採らない点・頼っている点が変わったら、それも直す。どの変更を取り込み・見送ったかの一覧は PR 本文に書く。
4. skill のファイルを変えたときだけ、`skills/<name>/evals/` の evals（trigger evals を含む）を skill-creator で流し直し、結果を PR 本文に残す。
5. PR を出し、本文に `Closes #<Issue>` を書く。タイトルの種別は「版の決め方」に従う（見送りだけで記録を進めるなら `chore:`。`skills/` が変わらないのでリリースされない）。

参考にする上流は、見送るだけでも最後に目を通したコミットを進める。進めないと、次の週も同じ差で Issue が更新される。

## PRチェックリスト

- [ ] frontmatterの`name`がディレクトリ名と一致している
- [ ] `description`に具体的なトリガーフレーズが含まれる
- [ ] ローカルで動作確認済み(symlink・`scripts/check-npx-skills.sh`・`gh skill preview` のいずれか)
- [ ] `scripts/` のスクリプトをインタプリタ経由(`bash`/`python3`)で呼んでいる
- [ ] `SKILL.md`が行数目安(約500行)以内、または詳細を`references/`に退避済み
- [ ] 秘密情報や難読化されたスクリプトが含まれていない(previewしても安全)
- [ ] PRタイトルに種別(`feat:`/`add:`/`fix:` など)が付いている

詳細は `.github/PULL_REQUEST_TEMPLATE.md` と連動している。
