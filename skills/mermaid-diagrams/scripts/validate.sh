#!/usr/bin/env bash
# Mermaid diagram(.mmd)の構文検証スクリプト。mmdc(mermaid-cli)でパース可否のみを検証する。
set -uo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
puppeteer_config="${script_dir}/puppeteer-config.json"

usage() {
  echo "使い方: $0 <file1.mmd> [file2.mmd ...]" >&2
  exit 2
}

if [ "$#" -eq 0 ]; then
  usage
fi

mmdc_cmd=()
if command -v mmdc >/dev/null 2>&1; then
  mmdc_cmd=(mmdc)
elif command -v npx >/dev/null 2>&1 \
  && npx --yes @mermaid-js/mermaid-cli --version >/dev/null 2>&1; then
  mmdc_cmd=(npx --yes @mermaid-js/mermaid-cli)
fi

if [ "${#mmdc_cmd[@]}" -eq 0 ]; then
  cat >&2 <<'EOF'
mmdc(mermaid-cli)が見つかりません。次のいずれかでインストールしてください。

  npm install -g @mermaid-js/mermaid-cli
  npx @mermaid-js/mermaid-cli --version   # npx経由でその都度実行する場合

mmdcは内部でPuppeteer/Chromiumを使うため、初回はChromiumのダウンロードが
必要です。サンドボックス制限のあるCI/コンテナ環境では、同梱の
puppeteer-config.json({"args": ["--no-sandbox"]})を
`mmdc -p scripts/puppeteer-config.json` のように渡してください。
EOF
  exit 3
fi

version_output="$("${mmdc_cmd[@]}" --version 2>/dev/null)"
echo "mmdc version: ${version_output:-unknown}"
echo "注意: この検証はMermaid記法としてのパース可否のみを確認する。対象レンダラー" >&2
echo "(GitHub/GitLab等)での実際の描画可否はreferences/rendering-compatibility-guide.md" >&2
echo "を別途確認すること。" >&2

tmp_files=()
# shellcheck disable=SC2317  # invoked indirectly via trap, not unreachable
cleanup() {
  local f
  for f in "${tmp_files[@]}"; do
    rm -f "$f"
  done
}
trap cleanup EXIT

ok_count=0
total_count=0
overall_status=0

for file in "$@"; do
  total_count=$((total_count + 1))

  if [ ! -f "$file" ]; then
    echo "NG (not found): ${file}"
    overall_status=1
    continue
  fi

  tmp_out="$(mktemp --suffix=.svg)"
  tmp_files+=("$tmp_out")
  stderr_file="$(mktemp)"
  tmp_files+=("$stderr_file")

  if "${mmdc_cmd[@]}" -i "$file" -o "$tmp_out" >/dev/null 2>"$stderr_file"; then
    echo "OK: ${file}"
    ok_count=$((ok_count + 1))
    continue
  fi

  if grep -qi "sandbox" "$stderr_file" \
    && "${mmdc_cmd[@]}" -i "$file" -o "$tmp_out" -p "$puppeteer_config" \
      >/dev/null 2>"$stderr_file"; then
    echo "OK: ${file} (--no-sandbox設定で再試行して成功)"
    ok_count=$((ok_count + 1))
    continue
  fi

  echo "NG: ${file}"
  tail -n 5 "$stderr_file" | sed 's/^/  /'
  overall_status=1
done

echo "${ok_count}/${total_count} diagrams OK"
exit "$overall_status"
