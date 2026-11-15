#!/usr/bin/env bash
# 直近の v* タグ以降に skills/ を変えたコミットから、次のリリースタグを決めて標準出力に出す。
# - タグが無い: v0.1.0
# - skills/ を変えたコミットが無い: 何も出さずに終了コード 0(リリース不要)
# - 件名が feat/add で始まるコミット、または破壊的変更(type!:)がある: minor を上げる
# - それ以外: patch を上げる
# 1.0.0 未満の間は破壊的変更でも major を上げない。
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

last_tag="$(git describe --tags --abbrev=0 --match 'v[0-9]*.[0-9]*.[0-9]*' 2>/dev/null || true)"

if [[ -z "${last_tag}" ]]; then
  echo "v0.1.0"
  exit 0
fi

subjects="$(git log --format=%s "${last_tag}..HEAD" -- skills/)"
if [[ -z "${subjects}" ]]; then
  exit 0
fi

IFS=. read -r major minor patch <<<"${last_tag#v}"

if grep -Eq '^(feat|add)(\([^)]*\))?!?:|^[a-z]+(\([^)]*\))?!:' <<<"${subjects}"; then
  if ((major == 0)); then
    minor=$((minor + 1))
    patch=0
  elif grep -Eq '^[a-z]+(\([^)]*\))?!:' <<<"${subjects}"; then
    major=$((major + 1))
    minor=0
    patch=0
  else
    minor=$((minor + 1))
    patch=0
  fi
else
  patch=$((patch + 1))
fi

echo "v${major}.${minor}.${patch}"
