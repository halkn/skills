# halkn/skills

Claude Code 用の Agent Skill 群を一箇所で開発・レビューし、複数端末・複数ターミナルに配布・同期するための
リポジトリです。配布経路は [`gh skill`](https://cli.github.com/manual/gh_skill)（GitHub CLI）と
[`npx skills`](https://github.com/vercel-labs/skills)（Vercel の Skills CLI）の2つに対応しています。
どちらで入れても同じ内容になります。claude.ai・Cowork には、プラグインマーケットプレイスとして入れられます。

## インストール

1台のマシンではどちらか一方だけを使ってください。どちらも `~/.claude/skills/<name>` に入れるため、
混ぜると片方の更新がもう片方の管理外のファイルを上書きします。
迷ったら `gh skill` を使ってください（Node.js が要らず、`--pin` で版を固定できます）。

### gh skill（GitHub CLI 2.90.0 以降）

```bash
# すべてのskillをユーザースコープ（マシン全体）に入れる
gh skill install halkn/skills --agent claude-code --scope user --all

# 更新
gh skill update --all

# 1つだけ入れる・中身を確認する
gh skill install halkn/skills skills/git-flow --agent claude-code --scope user
gh skill preview halkn/skills skills/git-flow

# 版を固定する
gh skill install halkn/skills skills/git-flow@v0.1.0 --agent claude-code --scope user
```

### npx skills（Node.js 22.20 以降）

```bash
# すべてのskillをユーザースコープ（~/.claude/skills）に入れる
npx skills add halkn/skills --global --agent claude-code --skill '*' --yes

# 更新
npx skills update --global --yes

# 入るskillの一覧を確認する（インストールしない）
npx skills add halkn/skills --list

# 1つだけ入れる・版を固定する
npx skills add halkn/skills --global --agent claude-code --skill git-flow --yes
npx skills add halkn/skills@v0.1.0 --global --agent claude-code --skill '*' --yes
```

`npx skills` は匿名の利用統計を送ります。止めるときは `DISABLE_TELEMETRY=1` を付けてください。

### claude.ai・Cowork（プラグインマーケットプレイス）

このリポジトリは、`.claude-plugin/marketplace.json` でプラグインマーケットプレイス `halkn-skills` としても読めます。
`skills/` 配下のすべての skill が、1つのプラグイン `halkn` に入っています（`.claude/skills/` のものは入りません）。

1. claude.ai で Customize > Plugins > Personal plugins を開く
2. Add marketplace > Add from a repository で `halkn/skills` を追加する
3. マーケットプレイス `halkn-skills` からプラグイン `halkn` を入れる

claude.ai のチャットにはローカルの git リポジトリもシェルも無いため、そこで役に立つのは `handoff`（issue・設計書の本文を書く）です。
`git-flow`・`review-report`・`session-retrospective` は、作業ツリーとシェル（`git`・`gh`・スクリプトの実行）を前提にしています。
`dev-docs` は Claude Code で作業ツリーの文書を書く前提で作っています。

更新は、マーケットプレイスの「Check for updates」で手動で取り込むか、「Sync automatically」を有効にして自動で取り込みます。
プラグインに `version` を書いていないので、`main` に commit が入るたびに新しい版として扱われます。

claude.ai のアカウントでサインインした Claude Code では、claude.ai で有効にしたプラグインが `halkn@synced` として同期されます。
そのため、同じ端末で `gh skill` か `npx skills` でも入れていると、同じ skill が2つ読み込まれます。どちらかを止めてください。

- Claude Code への同期を止める: `~/.claude/settings.json` に `"syncClaudeAiPlugins": false` を書く
- `gh skill`・`npx skills` で入れた skill を消し、同期されたプラグインだけを使う

### バージョンの決まり方

`skills/` 配下を変えた変更が `main` に入るたびに、CI がタグ（`vX.Y.Z`）と GitHub Release を作ります。
版を指定しない場合、`gh skill` は最新のリリース、`npx skills` は `main` の HEAD を入れますが、
`skills/` の変更ごとにリリースするので、両者の内容は一致します。

## 保有スキル一覧

| 名前 | 説明 |
|------|------|
| [dev-docs](skills/dev-docs/SKILL.md) | 人が読むリポジトリの文書（Azure DevOps Wiki・GitHub の設計書・ADR・Runbook・README）を、種類ごとの型と見出しの方針で書き、開発の図を Mermaid で入れ、文の推敲を内部で [yomiyasu](https://github.com/nanaism/yomiyasu) に任せる。yomiyasu は同梱せず、入っていなければ推敲を飛ばす |
| [git-flow](skills/git-flow/SKILL.md) | ブランチ作成→コミット→push→PR作成→マージのGit作業手順（GitHub は gh、Azure DevOps は az repos）。それ以外のリモートではユーザーに確認する |
| [handoff](skills/handoff/SKILL.md) | 作業を別のセッション・別のリポジトリ・issue・設計書に引き継ぐ文を書く。行き先を選び、今すぐ続けるセッションには貼り付ける引き継ぎ文を、後で着手する作業には実装計画として使える issue・設計書を書く。GitHub 以外やチャットでの本文作成にも対応 |
| [review-report](skills/review-report/SKILL.md) | `/code-review` の指摘を仕分け（今回直す・確認する・Issue に切る・対応しない）、issue の完了条件と照らしてマージ可否を出す。頼まれれば該当 diff と並べた1枚のHTMLレポートにする。レビュー自体は行わない |
| [session-retrospective](skills/session-retrospective/SKILL.md) | Claude Code のセッションを振り返り、同じ手戻りを次のセッションで起こさないための環境の改善（lint・hook・settings.json・CLAUDE.md・docs・skill・memory）を提案する。自動では起動しないので `/session-retrospective`（プラグインから入れた場合は `/halkn:session-retrospective`）で呼ぶ |

## 開発フロー

新しいskillの追加・既存skillの改善手順は
[`.claude/skills/skill-development/SKILL.md`](.claude/skills/skill-development/SKILL.md) にまとまっています。
このリポジトリで作業する場合はまずそちらを参照してください。
このskill自体はこのリポジトリの開発運用専用であり、`skills/`配下には置かず`.claude/skills/`配下に置いています。
`npx skills` は `.claude/skills/` も探索するため、frontmatter に `metadata.internal: true` を付けて配布対象から外しています。
