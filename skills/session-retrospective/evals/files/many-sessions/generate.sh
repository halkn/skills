#!/usr/bin/env bash
# eval「many-sessions」の transcript を生成する。全体を読みきれない大きさの中に、セッションをまたいで繰り返すエラーを埋める。
# 生成物は数 MB になり、配布物に含めないため commit しない（.gitignore）。evals を回す前に一度実行する。
set -euo pipefail

out_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -f "${out_dir}"/session-*.jsonl

# 大きな Read の結果。中身に意味は無く、読む量を増やすためだけにある。
filler="$(for i in $(seq 1 1500); do printf 'line %04d: lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.\n' "${i}"; done)"

# 繰り返すエラー（zsh が引用符の無い ? を glob として展開する）を埋めるセッション。
recurring=" 03 07 11 15 18 19 "

for n in $(seq -w 1 20); do
  repo="proj-$(((10#${n} % 3)))"
  jq -n -c \
    --arg q "'" --arg s "s${n}" --arg cwd "/work/${repo}" --arg day "$(printf '%02d' $((10#${n})))" \
    --arg filler "${filler}" --argjson recurring "$([[ "${recurring}" == *" ${n} "* ]] && echo true || echo false)" \
    --argjson n "$((10#${n}))" '
    def rec($ty; $t; $content): {type: $ty, sessionId: $s, cwd: $cwd, timestamp: "2026-10-\($day)T\($t).000Z", isSidechain: false, message: {role: $ty, content: $content}};
    def use($t; $id; $name; $input): rec("assistant"; $t; [{type: "tool_use", id: $id, name: $name, input: $input}]);
    def result($t; $id; $err; $text): rec("user"; $t; [{type: "tool_result", tool_use_id: $id, is_error: $err, content: $text}]);
    rec("user"; "09:00:00"; "issue #\($n) の対応を進めて"),
    (range(0; 6) as $i
      | use("09:0\($i):00"; "r\($i)"; "Read"; {file_path: "/work/src/module_\($i).rs"}),
        result("09:0\($i):01"; "r\($i)"; false; $filler)),
    (if $recurring then
        use("09:10:00"; "g1"; "Bash"; {command: "gh api repos/o/\($cwd | split("/") | last)/git/trees/HEAD?recursive=1 --jq \($q).tree[].path\($q)"}),
        result("09:10:01"; "g1"; true; "Exit code 1\n(eval):1: no matches found: repos/o/\($cwd | split("/") | last)/git/trees/HEAD?recursive=1"),
        use("09:11:00"; "g2"; "Bash"; {command: "gh api \($q)repos/o/\($cwd | split("/") | last)/git/trees/HEAD?recursive=1\($q) --jq \($q).tree[].path\($q)"}),
        result("09:11:01"; "g2"; false; "src/main.rs\nsrc/lib.rs")
      else empty end),
    (if $n == 5 then
        use("09:20:00"; "t1"; "Bash"; {command: "cargo test"}),
        result("09:20:01"; "t1"; true; "Exit code 101\ntest parse::empty_input ... FAILED\ntest result: FAILED. 41 passed; 1 failed"),
        use("09:21:00"; "t2"; "Edit"; {file_path: "/work/src/parse.rs", old_string: "unwrap()", new_string: "unwrap_or_default()"}),
        result("09:21:01"; "t2"; false; "The file has been updated successfully."),
        use("09:22:00"; "t3"; "Bash"; {command: "cargo test"}),
        result("09:22:01"; "t3"; false; "test result: ok. 42 passed; 0 failed")
      else empty end),
    (if $n == 9 then
        use("09:30:00"; "c1"; "Bash"; {command: "curl -fsSL https://example.com/docs/old-page.md"}),
        result("09:30:01"; "c1"; true; "Exit code 22\ncurl: (22) The requested URL returned error: 404")
      else empty end),
    (if $n == 13 then
        use("09:40:00"; "e1"; "Edit"; {file_path: "/work/README.md", old_string: "## Usage", new_string: "## How to use"}),
        result("09:40:01"; "e1"; true; "The user doesn\($q)t want to proceed with this tool use. The tool use was rejected."),
        rec("user"; "09:41:00"; "見出しはそのままでいいです")
      else empty end),
    rec("user"; "09:50:00"; "OK、commit して")
  ' >"${out_dir}/session-${n}.jsonl"
done

echo "生成しました: ${out_dir}/session-*.jsonl ($(du -sh "${out_dir}" | cut -f1))"
