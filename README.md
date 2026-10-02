# halkn/skills

Claude Code 用の Agent Skill 群を一箇所で開発・レビューし、[`gh skill`](https://cli.github.com/manual/gh_skill)
（GitHub CLI の Agent Skills 配布機能）経由で複数端末・複数ターミナルに配布・同期するための
リポジトリです。

## クイックスタート

このリポジトリのskillをすべてインストールする（Claude Codeのユーザースコープ = マシン全体で有効）:

```bash
gh skill install halkn/skills --agent claude-code --scope user --all
```

インストール済みskillを最新に更新する:

```bash
gh skill update --all
```

特定のskillだけ試す・中身を確認する:

```bash
gh skill install halkn/skills skills/git-flow --agent claude-code --scope user
gh skill preview halkn/skills skills/git-flow
```

> [!NOTE]
> バージョンを指定しない場合、`gh skill` は「最新のタグ付きリリース → デフォルトブランチのHEAD」の
> 順で解決します（`gh` 2.97.0 で確認）。このリポジトリはまだタグを切っていないため、現状は `main` の
> HEAD が入ります。特定の状態に固定したい場合は `--pin <tag-or-sha>` を使ってください。

## 保有スキル一覧

| 名前 | 説明 |
|------|------|
| [git-flow](skills/git-flow/SKILL.md) | ブランチ作成→コミット→push→PR作成→マージのGit作業手順。リモートがGitHubかAzure Reposかを判定してCLIを使い分ける |
| [issue-writing](skills/issue-writing/SKILL.md) | GitHub issue を決まった書式と粒度で書く。issue をそのままエージェント向けの実装計画として使える形にする |

## 開発フロー

新しいskillの追加・既存skillの改善手順は
[`.claude/skills/skill-development/SKILL.md`](.claude/skills/skill-development/SKILL.md) にまとまっています。
このリポジトリで作業する場合はまずそちらを参照してください。
このskill自体はこのリポジトリの開発運用専用であり、`skills/`配下には置かず(`gh skill`での配布対象にせず)、
`.claude/skills/`配下に置いています。
