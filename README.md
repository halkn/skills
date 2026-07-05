# halkn/skills

Claude Code 用の Agent Skill 群を一箇所で開発・レビューし、[`gh skill`](https://cli.github.com/manual/gh_skill)
（GitHub CLI の Agent Skills 配布機能）経由で複数端末・複数ターミナルに配布・同期するための
リポジトリです。

## クイックスタート

新しいマシンで、このリポジトリが公開しているすべてのskillをClaude Code用にインストールする:

```bash
gh skill install halkn/skills --agent claude-code --scope user --all
```

特定のskillだけ、特定バージョンでインストールする場合:

```bash
gh skill install halkn/skills "skills/<name>@vX.Y.Z" --agent claude-code --scope user
```

定期的に(当面は手動で)最新リリースを取り込む:

```bash
gh skill update --agent claude-code --scope user
```

> [!IMPORTANT]
> `main` ブランチではなく、必ずタグ/リリースからインストール・更新してください。
> `main` は開発中・レビュー中の変更を含む場合があり、安定性が保証されません。

## 保有スキル一覧

| 名前 | 説明 |
|------|------|
| [github-flow](skills/github-flow/SKILL.md) | 「ブランチ切ってcommitして」「PR作って」のような一言からGitHub Flow(ブランチ作成→コミット→PR作成→マージ)を進める |

## 開発フロー

新しいskillの追加・既存skillの改善・リリース手順は、すべて
[`.claude/skills/skill-development/SKILL.md`](.claude/skills/skill-development/SKILL.md) にまとまっています。
このリポジトリで作業する場合はまずそちらを参照してください。
このskill自体はこのリポジトリの開発運用専用であり、`skills/`配下には置かず(`gh skill`での配布対象にせず)、
`.claude/skills/`配下に置いています。
