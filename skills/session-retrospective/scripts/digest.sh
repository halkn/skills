#!/usr/bin/env bash
# Claude Code の transcript(jsonl)を、振り返りで読める大きさの Markdown に要約する。
set -euo pipefail

usage() {
  echo "使い方: $0 <transcript.jsonl>... | --selftest" >&2
  exit 1
}

# transcript の形式は公開仕様ではない。頼るのは type・sessionId・cwd・timestamp・isSidechain・isMeta・
# message.content(文字列 / text・tool_use・tool_result の配列)だけにし、それ以外のレコードは読み飛ばす。
readonly SLIM='
  def text_of: if type == "string" then . elif type == "array" then map(.text? // "") | join(" ") else tostring end;
  def summary: .input | (.command // .file_path // .pattern // .url // tojson) | tostring | gsub("\n"; " ") | .[0:160];
  # ! で打ったコマンドとスラッシュコマンドはユーザーの操作として残し、その出力やハーネスの通知は落とす。
  def prompt_line:
    if startswith("<bash-input>") then "! " + (capture("<bash-input>(?<x>.*)</bash-input>"; "s").x)
    elif startswith("<command-name>") then
      (capture("<command-name>(?<n>[^<]*)</command-name>").n) + " " + ((capture("<command-args>(?<a>[^<]*)</command-args>").a) // "")
    elif startswith("<") then empty
    else . end
    | gsub("\\s+"; " ") | .[0:300];
  fromjson?
  | select(type == "object" and (.type == "user" or .type == "assistant") and (.message | type) == "object")
  | select(.isSidechain != true)
  | {s: .sessionId, c: .cwd, t: (.timestamp // ""), ty: .type, meta: (.isMeta == true), m: .message.content}
  | if .ty == "assistant" then
      {k: "uses", s, c, t, uses: [(.m | arrays | .[]) | select(.type == "tool_use") | {id, name, in: summary}]}
    elif (.m | type) == "string" then
      if .meta then empty else {k: "prompt", s, c, t, p: (.m | prompt_line)} end
    else
      . as $r
      | (.m | arrays | .[])
      | if .type == "tool_result" then
          {k: "result", s: $r.s, c: $r.c, t: $r.t, id: .tool_use_id, err: (.is_error == true), x: (.content | text_of | if length > 400 then .[0:200] + "\n" + .[-200:] else . end)}
        elif .type == "text" and (.text | startswith("[Request interrupted")) then
          {k: "interrupt", s: $r.s, c: $r.c, t: $r.t}
        elif .type == "text" and ($r.meta | not) then
          {k: "prompt", s: $r.s, c: $r.c, t: $r.t, p: (.text | prompt_line)}
        else empty end
    end
'

readonly RENDER='
  def kind: if test("hook error") then "hook"
    elif test("auto mode classifier") then "classifier"
    elif test("Permission to use .* has been denied") then "permission-rule"
    elif test("doesn.t want to proceed") then "user-rejected"
    else "error" end;
  # 失敗の理由は出力の末尾に出ることが多く、先頭の 2 行で束ねると成功した前段の出力で割れる。
  def norm: split("\n") | map(select(length > 0)) | (if length > 1 then [.[0], .[-1]] else . end) | join(" / ")
    | gsub("[0-9a-f]{7,}"; "…") | gsub("[0-9]+"; "N") | .[0:140];
  def code: "`" + (gsub("`"; ([39] | implode))) + "`";
  def groups(f):
    group_by([f, .g]) | sort_by(-length)
    | map("- \(length) 回 \(.[0] | f) — \(.[0].g)\n" + (map(select(.name) | "  - \(.name) \(.in | code)") | unique | .[0:3] | join("\n")))
    | join("\n");

  . as $all
  | (map(select(.k == "uses") | .uses[]) | INDEX(.id)) as $uses
  | [ $all[] | select(.k == "result" and .err)
      | . + {kind: (.x | kind), g: (.x | norm)} + ($uses[.id] // {}) ] as $errs
  | ($all | map(select(.k == "interrupt"))) as $ints
  | "# Session digest\n",
    "## Sessions\n",
    "| session | cwd | start | prompts | tool calls | errors |",
    "|---|---|---|---|---|---|",
    ($all | group_by(.s)[]
      | . as $g
      | "| \($g[0].s) | \(map(.c | strings)[0] // "") | \(map(.t | select(length > 0)) | min // "" | .[0:16]) | \(map(select(.k == "prompt")) | length) | \(map(select(.k == "uses") | .uses | length) | add // 0) | \($errs | map(select(.s == $g[0].s)) | length) |"),
    "\n## Stops\n",
    "hook・auto mode classifier・permission rule に止められた呼び出し、ユーザーが拒否・中断した呼び出し。\n",
    ($errs | map(select(.kind != "error")) | if length == 0 then "(なし)" else groups(.kind) end),
    (if ($ints | length) > 0 then "- \($ints | length) 回 interrupted — [Request interrupted by user]" else empty end),
    "\n## Tool errors\n",
    ($errs | map(select(.kind == "error")) | if length == 0 then "(なし)" else groups(.name // "?") end),
    "\n## Prompts\n",
    ($all | map(select(.k == "prompt")) | group_by(.s)[]
      | "### \(.[0].s) (\(.[0].c // ""))\n",
        (sort_by(.t)[] | "- \(.t[5:16]) \(.p)"),
        "")
'

digest() {
  local slim
  slim="$(cat "$@" | jq -R -c "${SLIM}")"
  if [[ -z "${slim}" ]]; then
    echo "digest: user / assistant のレコードが見つかりません。transcript の形式が変わった可能性があります: $*" >&2
    return 1
  fi
  printf '%s\n' "${slim}" | jq -s -r "${RENDER}"
}

selftest() {
  local out
  # macOS の mktemp -d は雛形が無いと TMPDIR を見ず、sandbox の書込先から外れる。
  dir="$(mktemp -d "${TMPDIR:-/tmp}/digest-selftest.XXXXXX")"
  trap 'rm -rf "${dir}"' EXIT
  cat >"${dir}/s1.jsonl" <<'EOF'
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:00:00.000Z","isSidechain":false,"message":{"role":"user","content":"設定を直して"}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:00:01.000Z","isSidechain":false,"isMeta":true,"message":{"role":"user","content":"META-SHOULD-NOT-APPEAR"}}
not json
{"type":"assistant","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:01:00.000Z","isSidechain":false,"message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"gh pr list | head"}}]}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:01:01.000Z","isSidechain":false,"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t1","is_error":true,"content":"PreToolUse:Bash hook error: [h=~/.claude/hooks/block-piped-excluded.sh]: blocked"}]}}
{"type":"assistant","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:02:00.000Z","isSidechain":false,"message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"Bash","input":{"command":"gh issue close 1"}}]}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:02:01.000Z","isSidechain":false,"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t2","is_error":true,"content":[{"type":"text","text":"Permission for this action was denied by the Claude Code auto mode classifier. Reason: [External System Writes]."}]}]}}
{"type":"assistant","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:03:00.000Z","isSidechain":false,"message":{"role":"assistant","content":[{"type":"tool_use","id":"t3","name":"Bash","input":{"command":"cargo test"}},{"type":"tool_use","id":"t4","name":"Edit","input":{"file_path":"/r/a/x.md","old_string":"a","new_string":"b"}}]}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:03:01.000Z","isSidechain":false,"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t3","is_error":true,"content":"Exit code 101\nerror: build failed"},{"type":"tool_result","tool_use_id":"t4","is_error":true,"content":"The user doesn't want to proceed with this tool use. The tool use was rejected."}]}}
{"type":"assistant","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:03:30.000Z","isSidechain":false,"message":{"role":"assistant","content":[{"type":"tool_use","id":"t5","name":"Bash","input":{"command":"touch x.pem"}}]}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:03:31.000Z","isSidechain":false,"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t5","is_error":true,"content":"Permission to use Bash with command touch x.pem has been denied."}]}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:04:00.000Z","isSidechain":false,"message":{"role":"user","content":[{"type":"text","text":"[Request interrupted by user for tool use]"}]}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:05:00.000Z","isSidechain":false,"message":{"role":"user","content":"<bash-input>mise install</bash-input>"}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:05:01.000Z","isSidechain":false,"message":{"role":"user","content":"<bash-stdout>STDOUT-SHOULD-NOT-APPEAR</bash-stdout>"}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:06:00.000Z","isSidechain":false,"message":{"role":"user","content":"<command-name>/add-dir</command-name>\n<command-message>add-dir</command-message>\n<command-args>~/x</command-args>"}}
{"type":"user","sessionId":"s1","cwd":"/r/a","timestamp":"2026-11-01T10:07:00.000Z","isSidechain":true,"message":{"role":"user","content":"SUBAGENT-SHOULD-NOT-APPEAR"}}
EOF
  out="$(digest "${dir}/s1.jsonl")"

  local failed=0 want
  for want in \
    '| s1 | /r/a | 2026-11-01T10:00 | 3 | 5 | 5 |' \
    '設定を直して' \
    '! mise install' \
    '/add-dir ~/x' \
    'hook' \
    '`gh pr list | head`' \
    'classifier' \
    '`gh issue close 1`' \
    'permission-rule' \
    'user-rejected' \
    '`/r/a/x.md`' \
    'interrupted' \
    'Exit code N' \
    '`cargo test`'; do
    if [[ "${out}" != *"${want}"* ]]; then
      echo "selftest: 出力に含まれない: ${want}" >&2
      failed=1
    fi
  done
  for want in META-SHOULD-NOT-APPEAR STDOUT-SHOULD-NOT-APPEAR SUBAGENT-SHOULD-NOT-APPEAR; do
    if [[ "${out}" == *"${want}"* ]]; then
      echo "selftest: 出力に含まれてはいけない: ${want}" >&2
      failed=1
    fi
  done
  if printf '{"foo":1}\n' >"${dir}/bad.jsonl" && digest "${dir}/bad.jsonl" >/dev/null 2>&1; then
    echo "selftest: 想定外の形式で失敗しない" >&2
    failed=1
  fi

  if [[ "${failed}" -ne 0 ]]; then
    printf '%s\n' "--- 出力 ---" "${out}" >&2
    return 1
  fi
  echo "selftest: ok"
}

main() {
  [[ "$#" -ge 1 ]] || usage
  if [[ "$1" == "--selftest" ]]; then
    selftest
  else
    digest "$@"
  fi
}

main "$@"
