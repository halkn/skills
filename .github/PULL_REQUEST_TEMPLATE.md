## 概要

<!-- 追加/変更したskillと目的を1〜2行で -->

## チェックリスト

- [ ] frontmatterの `name` がディレクトリ名と一致している
- [ ] `description` に具体的なトリガーフレーズが含まれている(「何をするか」ではなく「いつ使うか」)
- [ ] ローカルで動作確認済み(symlinkでの反復、`scripts/check-npx-skills.sh`、または `gh skill preview`)
- [ ] `SKILL.md` が行数目安(約500行)以内、または詳細を `references/` に退避済み
- [ ] 秘密情報や難読化されたスクリプトが含まれていない(previewしても安全)
- [ ] PRタイトルに種別(`feat:`/`add:`/`fix:` など)が付いている(リリースの版の決定に使う)

詳細は [.claude/skills/skill-development/SKILL.md](../.claude/skills/skill-development/SKILL.md) を参照。
