#!/usr/bin/env bash
# SKILL.md のfrontmatterを検証する。CIとPostToolUseフックで共有する。
# - skills/*/SKILL.md: 配布対象。name/description の存在と、name とディレクトリ名の一致を見る。
# - .claude/skills/*/SKILL.md: リポジトリ専用。npx skills は .claude/skills/ も探索するため、
#   metadata.internal: true で配布対象から外れていることを見る。
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# PostToolUse フックは終了コード 2 のときだけ stderr を Claude に渡す（1 はユーザーへの通知だけ）。CI はどちらでも失敗する。
status=0

# frontmatter を標準出力に出す。見つからない・YAML として読めないときは失敗する。
read_frontmatter() {
  local file="$1" rel="$2" fm
  if ! fm=$(awk '
    NR==1 && $0 !~ /^---$/ { exit 1 }
    /^---$/ { c++; if (c==2) exit; next }
    c==1
  ' "${file}"); then
    echo "${rel}: frontmatter(---ブロック)が見つかりません" >&2
    return 1
  fi
  if ! printf '%s' "${fm}" | yq eval '.' - >/dev/null 2>&1; then
    echo "${rel}: frontmatterがYAMLとしてパースできません" >&2
    return 1
  fi
  printf '%s' "${fm}"
}

for file in "$repo_root"/.claude/skills/*/SKILL.md; do
  [ -f "$file" ] || continue
  rel="${file#"$repo_root"/}"
  if ! frontmatter=$(read_frontmatter "$file" "$rel"); then
    status=2
    continue
  fi
  internal=$(printf '%s' "$frontmatter" | yq eval '.metadata.internal // ""' -)
  case "$internal" in
    true | 1) ;;
    *)
      echo "$rel: リポジトリ専用skillには metadata.internal: true が必要です(npx skills の配布対象から外すため)" >&2
      status=2
      ;;
  esac
done

for file in "$repo_root"/skills/*/SKILL.md; do
  [ -f "$file" ] || continue

  rel="${file#"$repo_root"/}"
  dir_name=$(basename "$(dirname "$file")")

  if ! frontmatter=$(read_frontmatter "$file" "$rel"); then
    status=2
    continue
  fi

  name=$(printf '%s' "$frontmatter" | yq eval '.name // ""' -)
  description=$(printf '%s' "$frontmatter" | yq eval '.description // ""' -)

  if [ -z "$name" ]; then
    echo "$rel: frontmatterに name がありません" >&2
    status=2
  elif [ "$name" != "$dir_name" ]; then
    echo "$rel: frontmatterの name '$name' がディレクトリ名 '$dir_name' と一致しません" >&2
    status=2
  fi

  if [ -z "$description" ]; then
    echo "$rel: frontmatterに description がありません" >&2
    status=2
  fi
done

exit "$status"
