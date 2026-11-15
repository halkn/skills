#!/usr/bin/env bash
# PostToolUse フック(Write|Edit)から呼び、編集したファイルが SKILL.md のときだけ frontmatter を検証する。
# - skills/*/SKILL.md: gh skill publish --dry-run(CI の distribution-gh と同じ検査)
# - .claude/skills/*/SKILL.md: scripts/validate-internal-skills.py(CI の frontmatter ジョブと同じ検査)
# 終了コード: 2 = 検証エラー(stderr を Claude に渡す)、1 = 検証できなかった(ユーザーへの通知だけ)、0 = 問題なし。
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# フックの入力(JSON)から tool_input.file_path を取り出す。jq に依存しないよう grep で拾う。
input="$(cat)"
file_path="$(grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' <<<"${input}" | head -n 1 \
  | sed 's/^"file_path"[[:space:]]*:[[:space:]]*"//; s/"$//')"

case "${file_path}" in
  */.claude/skills/*/SKILL.md)
    target=internal
    ;;
  */skills/*/SKILL.md)
    target=distributed
    ;;
  *)
    exit 0
    ;;
esac

if [[ "${target}" == distributed ]]; then
  # gh skill は gh 2.90.0 以降にしか無い。
  if ! gh skill --help >/dev/null 2>&1; then
    echo "gh skill が使えないため ${file_path} の frontmatter を検証できませんでした(gh 2.90.0 以降が必要。CI の distribution-gh では検証される)" >&2
    exit 1
  fi
  # CI と同じく、リポジトリ直下で引数なしで呼ぶ。
  if ! output="$(cd "${repo_root}" && gh skill publish --dry-run 2>&1)"; then
    printf '%s\n' "${output}" >&2
    exit 2
  fi
else
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv が無いため ${file_path} の frontmatter を検証できませんでした(CI の frontmatter ジョブでは検証される)" >&2
    exit 1
  fi
  if ! output="$(uv run --quiet "${repo_root}/scripts/validate-internal-skills.py" 2>&1)"; then
    printf '%s\n' "${output}" >&2
    exit 2
  fi
fi
