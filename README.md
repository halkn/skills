# halkn/skills

Claude Code 用の Agent Skill 群を一箇所で開発・レビューし、複数端末・複数ターミナルに配布・同期するための
リポジトリです。配布経路は [`gh skill`](https://cli.github.com/manual/gh_skill)（GitHub CLI）と
[`npx skills`](https://github.com/vercel-labs/skills)（Vercel の Skills CLI）の2つに対応しています。
どちらで入れても同じ内容になります。

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

### バージョンの決まり方

`skills/` 配下を変えた変更が `main` に入るたびに、CI がタグ（`vX.Y.Z`）と GitHub Release を作ります。
版を指定しない場合、`gh skill` は最新のリリース、`npx skills` は `main` の HEAD を入れますが、
`skills/` の変更ごとにリリースするので、両者の内容は一致します。

### issue-writing から handoff への入れ直し

`issue-writing` は `handoff` に改名しました。更新（`update`）では新しい名前の skill は入らないので、入れ直してください。

```bash
# gh skill（削除のサブコマンドが無いので、古いディレクトリは手で消す）
gh skill install halkn/skills skills/handoff --agent claude-code --scope user
rm -r ~/.claude/skills/issue-writing

# npx skills
npx skills remove --global --agent claude-code issue-writing --yes
npx skills add halkn/skills --global --agent claude-code --skill handoff --yes
```

## 保有スキル一覧

| 名前 | 説明 |
|------|------|
| [git-flow](skills/git-flow/SKILL.md) | ブランチ作成→コミット→push→PR作成→マージのGit作業手順（GitHub / gh 前提）。GitHub以外のリモートではユーザーに確認する |
| [handoff](skills/handoff/SKILL.md) | 作業を別のセッション・別のリポジトリ・issue・設計書に引き継ぐ文を書く。行き先を選び、今すぐ続けるセッションには貼り付ける引き継ぎ文を、後で着手する作業には実装計画として使える issue・設計書を書く。GitHub 以外やチャットでの本文作成にも対応 |
| [review-report](skills/review-report/SKILL.md) | `/code-review` の指摘を、該当 diff と並べて読める1枚のHTMLレポートにする。レビュー自体は行わない |
| [session-retrospective](skills/session-retrospective/SKILL.md) | Claude Code のセッションを振り返り、同じ手戻りを次のセッションで起こさないための環境の改善（lint・hook・settings.json・CLAUDE.md・docs・skill・memory）を提案する。自動では起動しないので `/session-retrospective` で呼ぶ |

## 開発フロー

新しいskillの追加・既存skillの改善手順は
[`.claude/skills/skill-development/SKILL.md`](.claude/skills/skill-development/SKILL.md) にまとまっています。
このリポジトリで作業する場合はまずそちらを参照してください。
このskill自体はこのリポジトリの開発運用専用であり、`skills/`配下には置かず`.claude/skills/`配下に置いています。
`npx skills` は `.claude/skills/` も探索するため、frontmatter に `metadata.internal: true` を付けて配布対象から外しています。
