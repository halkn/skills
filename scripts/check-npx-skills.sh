#!/usr/bin/env bash
# npx skills でこのリポジトリをインストールしたとき、入るskillが skills/ 配下と過不足なく一致するかを見る。
# npx skills は skills/ 以外に .claude/skills/ なども探索するため、リポジトリ専用skillの混入をここで検出する。
# 使い方: scripts/check-npx-skills.sh [skills のバージョン(既定: SKILLS_CLI_VERSION または latest)]
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="${1:-${SKILLS_CLI_VERSION:-latest}}"

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

export DISABLE_TELEMETRY=1

# 作業ディレクトリをプロジェクトとして、Claude Code向けにコピーでインストールする。
(cd "${work}" && npx -y "skills@${version}" add "${repo_root}" \
  --agent claude-code --skill '*' --copy --yes)

expected="$(find "${repo_root}/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -exec dirname {} \; \
  | xargs -n1 basename | sort)"
# 1件も入らないとインストール先が作られない。find の失敗で止めず、下の差分で何が欠けたかを見せる。
actual=""
if [[ -d "${work}/.claude/skills" ]]; then
  actual="$(find "${work}/.claude/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -exec dirname {} \; \
    | xargs -n1 basename | sort)"
fi

if [[ "${expected}" != "${actual}" ]]; then
  echo "npx skills でインストールされるskillが skills/ 配下と一致しません" >&2
  diff <(printf '%s\n' "${expected}") <(printf '%s\n' "${actual}") >&2 || true
  exit 1
fi

echo "npx skills (skills@${version}) のインストール結果は skills/ 配下と一致しました:"
sed 's/^/  /' <<<"${actual}"
