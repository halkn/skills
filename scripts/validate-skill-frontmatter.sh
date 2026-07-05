#!/usr/bin/env bash
# PostToolUse(Write|Edit)フック用。skills/*/SKILL.mdの編集時のみfrontmatterを検証する。
set -uo pipefail

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

case "$file" in
  */skills/*/SKILL.md) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0

dir_name=$(basename "$(dirname "$file")")

if ! frontmatter=$(awk '
  NR==1 && $0 !~ /^---$/ { exit 1 }
  /^---$/ { c++; if (c==2) exit; next }
  c==1
' "$file"); then
  echo "SKILL.md frontmatter(---ブロック)が見つかりません: $file" >&2
  exit 1
fi

name=$(printf '%s' "$frontmatter" | yq eval '.name // ""' -)
description=$(printf '%s' "$frontmatter" | yq eval '.description // ""' -)

ok=0

if [ -z "$name" ]; then
  echo "frontmatterに name がありません: $file" >&2
  ok=1
elif [ "$name" != "$dir_name" ]; then
  echo "frontmatterの name '$name' がディレクトリ名 '$dir_name' と一致しません: $file" >&2
  ok=1
fi

if [ -z "$description" ]; then
  echo "frontmatterに description がありません: $file" >&2
  ok=1
fi

exit "$ok"
