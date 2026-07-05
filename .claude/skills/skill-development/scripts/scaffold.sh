#!/usr/bin/env bash
# 新規skillの雛形を skills/<name>/ に生成する。
set -euo pipefail

usage() {
  echo "使い方: $0 <skill-name>" >&2
  echo "  <skill-name> は小文字・数字・ハイフンのみ(例: pdf-fill-form)" >&2
  exit 1
}

if [ "$#" -ne 1 ]; then
  usage
fi

name="$1"

if ! [[ "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "エラー: skill名は小文字・数字・ハイフンのみ使用できます: '$name'" >&2
  exit 1
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && git rev-parse --show-toplevel)"
skill_dir="$repo_root/skills/$name"

if [ -e "$skill_dir" ]; then
  echo "エラー: $skill_dir は既に存在します" >&2
  exit 1
fi

mkdir -p "$skill_dir"

cat >"$skill_dir/SKILL.md" <<EOF
---
name: ${name}
description: >
  TODO: このskillが「何をするか」ではなく「いつ使うか」を具体的なトリガー
  フレーズで書く(例: "ユーザーが〜と言ったときに使う")。descriptionは
  Claude Codeがこのskillを自動トリガーする際の唯一の手がかりになる。
---

# ${name}

TODO: このskillの目的と使い方を書く。

## 使い方

TODO

## 詳細

詳細な情報が必要な場合は \`references/\` 以下に切り出し、ここからリンクする。
EOF

echo "生成しました: $skill_dir/SKILL.md"
echo "次のステップ:"
echo "  1. SKILL.md の description とTODOを埋める"
echo "  2. 必要であれば scripts/ や references/ を作成する(不要なら作らない)"
echo "  3. .claude/skills/skill-development/SKILL.md の手順に従ってローカル動作確認する"
