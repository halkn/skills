#!/usr/bin/env bash
# PostToolUse フック(Write|Edit)から呼び、skills/*/SKILL.md を gh skill publish --dry-run で検証する。
# CI の distribution-gh ジョブと同じ検査(name の命名規則・name とディレクトリ名の一致・name/description の有無)。
# .claude/skills/ の metadata.internal の付け忘れは CI の distribution-npx ジョブで検出する。
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# gh skill は gh 2.90.0 以降にしか無い。無い環境では検査を飛ばす(CI で同じ検査をする)。
if ! gh skill --help >/dev/null 2>&1; then
  exit 0
fi

if ! output="$(gh skill publish --dry-run "${repo_root}" 2>&1)"; then
  # PostToolUse フックは終了コード 2 のときだけ stderr を Claude に渡す(1 はユーザーへの通知だけ)。
  printf '%s\n' "${output}" >&2
  exit 2
fi
