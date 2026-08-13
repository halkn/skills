#!/usr/bin/env bash
# skills/*/SKILL.md のfrontmatterを検証する。CIとPostToolUseフックで共有する。
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

status=0

for file in "$repo_root"/skills/*/SKILL.md; do
  [ -f "$file" ] || continue

  rel="${file#"$repo_root"/}"
  dir_name=$(basename "$(dirname "$file")")

  if ! frontmatter=$(awk '
    NR==1 && $0 !~ /^---$/ { exit 1 }
    /^---$/ { c++; if (c==2) exit; next }
    c==1
  ' "$file"); then
    echo "$rel: frontmatter(---ブロック)が見つかりません" >&2
    status=1
    continue
  fi

  if ! printf '%s' "$frontmatter" | yq eval '.' - >/dev/null 2>&1; then
    echo "$rel: frontmatterがYAMLとしてパースできません" >&2
    status=1
    continue
  fi

  name=$(printf '%s' "$frontmatter" | yq eval '.name // ""' -)
  description=$(printf '%s' "$frontmatter" | yq eval '.description // ""' -)

  if [ -z "$name" ]; then
    echo "$rel: frontmatterに name がありません" >&2
    status=1
  elif [ "$name" != "$dir_name" ]; then
    echo "$rel: frontmatterの name '$name' がディレクトリ名 '$dir_name' と一致しません" >&2
    status=1
  fi

  if [ -z "$description" ]; then
    echo "$rel: frontmatterに description がありません" >&2
    status=1
  fi
done

exit "$status"
