#!/usr/bin/env python3
"""findings.json と統一 diff を、単一ファイルの HTML レビューレポートに描画する。

標準ライブラリのみを使う。--selftest でこのファイルに同梱したテストを走らせる。
"""

import argparse
import hashlib
import json
import sys
import webbrowser
from pathlib import Path

PLACEHOLDER = "/*__DATA__*/null"
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"


def _hunk_header(line):
    """`@@ -a,b +c,d @@ section` から (old_start, new_old_count, new_start, new_count, section)。"""
    body, _, section = line[2:].partition("@@")
    old_part, new_part = body.strip().split(" ")

    def split(part):
        nums = part[1:].split(",")
        start = int(nums[0])
        count = int(nums[1]) if len(nums) > 1 else 1
        return start, count

    old_start, old_count = split(old_part)
    new_start, new_count = split(new_part)
    return old_start, old_count, new_start, new_count, section.strip()


def _unquote(path):
    """git の C クォート表記を戻す。

    core.quotePath の既定 (true) では非 ASCII のパスが `"a/\\346\\227\\245.md"` の形で出る。
    そのままキーにすると findings 側の生のパスと一致しない。
    """
    if len(path) < 2 or not path.startswith('"') or not path.endswith('"'):
        return path
    body = path[1:-1]
    out = bytearray()
    i = 0
    while i < len(body):
        if body[i] != "\\" or i + 1 >= len(body):
            out.extend(body[i].encode("utf-8"))
            i += 1
            continue
        nxt = body[i + 1]
        if nxt in "01234567" and i + 3 < len(body) + 1:
            out.append(int(body[i + 1 : i + 4], 8))
            i += 4
        else:
            out.extend({"n": b"\n", "t": b"\t", "r": b"\r"}.get(nxt, nxt.encode("utf-8")))
            i += 2
    return out.decode("utf-8", "replace")


def _strip_prefix(path):
    """`b/src/x.py` のような diff の path 接頭辞を落とす。

    `diff.mnemonicPrefix` を設定した環境では a/ b/ ではなく c/ i/ w/ o/ が付くため、
    b/ 決め打ちにしない。`diff.noprefix` で接頭辞が無い場合、トップレベルに 1 文字の
    ディレクトリがあると誤って落とすが、その組み合わせは実質起きない。
    """
    path = _unquote(path)
    if len(path) > 1 and path[1] == "/" and path[0] in "abciwo":
        return path[2:]
    return path


def parse_diff(text):
    """統一 diff を {path: filerec} に変換する。

    filerec は path / old_path / binary / hunks を持ち、hunks の各行は
    old・new の行番号（対象外の側は None）を保持する。
    """
    records = []
    current = None
    hunk = None
    old_no = new_no = 0
    old_left = new_left = 0

    for line in text.split("\n"):
        if line.startswith("diff --git "):
            # 後ろ側を暫定のパスにする。`+++` 行と rename 情報で後から確定させる
            _, _, paths = line.partition("diff --git ")
            path = _strip_prefix(paths.split(" ")[-1])
            current = {"path": path, "old_path": None, "binary": False, "hunks": []}
            records.append(current)
            hunk = None
            continue

        if current is None:
            continue

        # ヘッダの判定は hunk の外だけで行う。hunk 内では diff 自身をレビューしたときに
        # 追加行の内容（`+++ b/x` 等）がヘッダと同じ見た目になる
        if hunk is None:
            if line.startswith("+++ "):
                # パスに空白があると git はタブで区切る。無ければ行末までがパス
                path = line[len("+++ ") :].split("\t", 1)[0]
                if path != "/dev/null":
                    current["path"] = _strip_prefix(path)
                continue
            # rename 行の値も他のパスと同じくクォートされうる。接頭辞は付かない
            if line.startswith("rename from "):
                current["old_path"] = _unquote(line[len("rename from ") :])
                continue
            if line.startswith("rename to "):
                current["path"] = _unquote(line[len("rename to ") :])
                continue
            if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
                current["binary"] = True
                continue

        if line.startswith("@@"):
            old_start, old_count, new_start, new_count, section = _hunk_header(line)
            hunk = {
                "header": line,
                "section": section,
                "old_start": old_start,
                "new_start": new_start,
                "lines": [],
            }
            current["hunks"].append(hunk)
            old_no, new_no = old_start, new_start
            old_left, new_left = old_count, new_count
            continue

        if hunk is None or (old_left <= 0 and new_left <= 0):
            hunk = None
            continue

        # hunk 内の空行は、末尾空白を落とすツールが出した context 行として扱う
        marker = line[0] if line else " "
        body = line[1:] if line else ""

        if marker == "+":
            hunk["lines"].append({"kind": "add", "old": None, "new": new_no, "text": body})
            new_no += 1
            new_left -= 1
        elif marker == "-":
            hunk["lines"].append({"kind": "del", "old": old_no, "new": None, "text": body})
            old_no += 1
            old_left -= 1
        elif marker == " ":
            hunk["lines"].append({"kind": "ctx", "old": old_no, "new": new_no, "text": body})
            old_no += 1
            new_no += 1
            old_left -= 1
            new_left -= 1
        elif marker == "\\":
            # "\ No newline at end of file"
            continue
        else:
            hunk = None

    # SKILL.md 手順2 が 2 つの git diff を連結するため、同じ path が複数回現れうる
    files = {}
    for rec in records:
        existing = files.get(rec["path"])
        if existing is None:
            files[rec["path"]] = rec
            continue
        existing["binary"] = existing["binary"] or rec["binary"]
        existing["old_path"] = existing["old_path"] or rec["old_path"]
        seen = [h["lines"] for h in existing["hunks"]]
        for hunk in rec["hunks"]:
            if hunk["lines"] not in seen:
                existing["hunks"].append(hunk)
    return files


def resolve_file(path, files):
    """finding の file を diff 内のファイルに対応づける。

    /code-review は位置を絶対パスで報告するため、完全一致だけでは引き当たらない。
    接尾辞でも探すが、複数に一致するときは推測せず None を返す。
    """
    if not path:
        return None
    if path in files:
        return files[path]
    for rec in files.values():
        if rec.get("old_path") == path:
            return rec

    normalized = path.lstrip("./")
    if normalized in files:
        return files[normalized]

    matches = [rec for key, rec in files.items() if path.endswith("/" + key)]
    return matches[0] if len(matches) == 1 else None


def attach_hunks(findings, files):
    """各 finding に、その file:line を含む hunk を紐づける。見つからなければ None。"""
    result = []
    for index, finding in enumerate(findings):
        item = dict(finding)
        item["id"] = index
        item["hunk"] = None
        rec = resolve_file(finding.get("file"), files)
        try:
            line = int(finding.get("line"))
        except (TypeError, ValueError):
            line = None
        if rec is not None and line is not None:
            # 同じ行を含む hunk が複数あるのは、連結された 2 つの diff が同じファイルの
            # 別スナップショットに行番号を振っているとき。後にある作業ツリー側が現在の内容
            for hunk in reversed(rec["hunks"]):
                if any(ln["new"] == line for ln in hunk["lines"]):
                    item["hunk"] = {
                        "file": rec["path"],
                        "section": hunk["section"],
                        "lines": hunk["lines"],
                    }
                    break
        result.append(item)
    return result


SEVERITIES = ("HIGH", "MEDIUM", "LOW")
DISPOSITIONS = ("fix-now", "issue", "wont-fix")


def build_payload(report, files):
    findings = attach_hunks(report.get("findings", []), files)
    stats = {"CONFIRMED": 0, "PLAUSIBLE": 0, "unknown": 0, "unmatched": 0}

    # 仕分けは画面上で変えられるので集計は JS が持つ。ここでは値の正規化だけ行う
    problems = []
    for item in findings:
        verdict = item.get("verdict")
        stats[verdict if verdict in ("CONFIRMED", "PLAUSIBLE") else "unknown"] += 1
        if item["hunk"] is None:
            stats["unmatched"] += 1
        where = f"{item.get('file')}:{item.get('line')}"
        # 解釈できない値を既定へ倒すと、マージを止めるべき指摘が非 blocking として
        # 表示され、しかも生成後の検証では捕まえられない。揺れの吸収だけに留める
        severity = str(item.get("severity") or "").strip().upper()
        if severity not in SEVERITIES:
            problems.append(f"{where}: severity が {item.get('severity')!r}（{'/'.join(SEVERITIES)}）")
        item["severity"] = severity
        disposition = str(item.get("disposition") or "").strip().lower()
        if disposition not in DISPOSITIONS:
            problems.append(f"{where}: disposition が {item.get('disposition')!r}（{'/'.join(DISPOSITIONS)}）")
        item["disposition"] = disposition
    if problems:
        raise ValueError("findings.json の値が不正です:\n  " + "\n  ".join(problems))

    stats["total"] = len(findings)
    # 仕分けの保存先を報告ごとに分けるキー。disposition を含めるので、findings.json の
    # 仕分けを直して作り直せばブラウザに残った古い上書きは引き継がれない
    identity = json.dumps(
        [
            report.get("target", {}).get("label"),
            [(f.get("file"), f.get("line"), f.get("disposition")) for f in findings],
        ],
        ensure_ascii=False,
    )
    return {
        "report_id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        "target": report.get("target", {}),
        "level": report.get("level"),
        "assessment": report.get("assessment", {}),
        "findings": findings,
        "stats": stats,
        "severities": list(SEVERITIES),
        "dispositions": list(DISPOSITIONS),
    }


def render(payload, template):
    if PLACEHOLDER not in template:
        raise ValueError(f"テンプレートに {PLACEHOLDER} がありません")
    data = json.dumps(payload, ensure_ascii=False)
    # `</script>` だけでなく `<!--` + `<script` の double-escape 経路も塞ぐ必要があるため、
    # `<` を丸ごと退避する。JSON では `<` は文字列内にしか現れないので置換して安全
    data = data.replace("<", "\\u003c")
    return template.replace(PLACEHOLDER, data)


# --- selftest ---------------------------------------------------------------

SAMPLE_DIFF = """diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,4 +1,5 @@ def head():
 import os
-import sys
+import json
+import sys

 def main():
@@ -20,3 +21,3 @@ def main():
     run()
-    cleanup()
+    cleanup(force=True)
     return 0
diff --git a/src/new.py b/src/new.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/src/new.py
@@ -0,0 +1,2 @@
+VALUE = 1
+OTHER = 2
diff --git a/old/name.py b/new/name.py
similarity index 90%
rename from old/name.py
rename to new/name.py
index 4444444..5555555 100644
--- a/old/name.py
+++ b/new/name.py
@@ -7,2 +7,2 @@ class C:
-    x = 1
+    x = 2
     y = 3
diff --git a/assets/logo.png b/assets/logo.png
index 6666666..7777777 100644
Binary files a/assets/logo.png and b/assets/logo.png differ
diff --git a/gone.py b/gone.py
deleted file mode 100644
index 8888888..0000000
--- a/gone.py
+++ /dev/null
@@ -1,2 +0,0 @@
-a = 1
-b = 2
diff --git i/docs/mnemonic.md w/docs/mnemonic.md
index 9999999..aaaaaaa 100644
--- i/docs/mnemonic.md
+++ w/docs/mnemonic.md
@@ -3,1 +3,1 @@
-old
+new
"""


def _selftest():
    files = parse_diff(SAMPLE_DIFF)

    assert set(files) == {
        "src/app.py",
        "src/new.py",
        "new/name.py",
        "assets/logo.png",
        "gone.py",
        "docs/mnemonic.md",
    }, sorted(files)

    # diff.mnemonicPrefix を設定した環境では a/ b/ ではなく i/ w/ が付く
    mnemonic = files["docs/mnemonic.md"]
    assert [ln["new"] for ln in mnemonic["hunks"][0]["lines"]] == [None, 3]

    app = files["src/app.py"]
    assert app["binary"] is False
    assert app["old_path"] is None
    assert len(app["hunks"]) == 2, len(app["hunks"])

    # 1つめの hunk: 削除1行・追加2行を挟んで new 側の行番号が 1..5 になる
    lines = app["hunks"][0]["lines"]
    assert [ln["text"] for ln in lines] == [
        "import os",
        "import sys",
        "import json",
        "import sys",
        "",
        "def main():",
    ], [ln["text"] for ln in lines]
    assert [ln["kind"] for ln in lines] == [
        "ctx",
        "del",
        "add",
        "add",
        "ctx",
        "ctx",
    ]
    assert [ln["new"] for ln in lines] == [1, None, 2, 3, 4, 5]
    assert [ln["old"] for ln in lines] == [1, 2, None, None, 3, 4]

    # 2つめの hunk: 新側は 21 から始まる
    lines = app["hunks"][1]["lines"]
    assert [ln["new"] for ln in lines] == [21, None, 22, 23]
    assert [ln["old"] for ln in lines] == [20, 21, None, 22]

    new = files["src/new.py"]
    assert [ln["new"] for ln in new["hunks"][0]["lines"]] == [1, 2]
    assert all(ln["old"] is None for ln in new["hunks"][0]["lines"])

    renamed = files["new/name.py"]
    assert renamed["old_path"] == "old/name.py"
    assert [ln["new"] for ln in renamed["hunks"][0]["lines"]] == [None, 7, 8]

    logo = files["assets/logo.png"]
    assert logo["binary"] is True
    assert logo["hunks"] == []

    gone = files["gone.py"]
    assert gone["binary"] is False
    assert [ln["kind"] for ln in gone["hunks"][0]["lines"]] == ["del", "del"]
    assert all(ln["new"] is None for ln in gone["hunks"][0]["lines"])

    # hunk ヘッダの末尾（関数名などのコンテキスト）を保持する
    assert app["hunks"][0]["section"] == "def head():"
    assert files["src/new.py"]["hunks"][0]["section"] == ""

    # 空の diff
    assert parse_diff("") == {}

    _selftest_matching(files)
    _selftest_render(files)
    _selftest_concatenated_diffs()
    _selftest_diff_line_lookalikes()
    _selftest_path_resolution()
    _selftest_quoted_paths()
    _selftest_line_types()
    _selftest_cli_errors()
    print("selftest: ok")


def _selftest_cli_errors():
    """不正な findings.json は traceback ではなく読めるメッセージで落とす。"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "f.json").write_text(
            json.dumps({"findings": [{"file": "a", "line": 1, "short_summary": "s", "severity": "bogus"}]}),
            encoding="utf-8",
        )
        (tmp / "d.patch").write_text("", encoding="utf-8")
        code = main(
            ["--findings", str(tmp / "f.json"), "--diff", str(tmp / "d.patch"), "--out", str(tmp / "o.html")]
        )
        assert code == 1, code
        assert not (tmp / "o.html").exists(), "検証に失敗したのに HTML を書いている"


# core.quotePath の既定 (true) では非 ASCII のパスが C クォート表記で出る。
# パスに空白があると git は `---`/`+++` の行末にタブを足して区切りを示す（実出力で確認）
_JP = "\\346\\227\\245\\346\\234\\254\\350\\252\\236 \\343\\201\\256\\345\\220\\215\\345\\211\\215.md"
QUOTED_DIFF = (
    f'diff --git "i/{_JP}" "w/{_JP}"\n'
    f'--- "i/{_JP}"\t\n'
    f'+++ "w/{_JP}"\t\n'
    "@@ -1,1 +1,1 @@\n"
    "-old\n"
    "+new\n"
)


def _selftest_quoted_paths():
    files = parse_diff(QUOTED_DIFF)
    assert set(files) == {"日本語 の名前.md"}, sorted(files)
    assert attach_hunks([{"file": "日本語 の名前.md", "line": 1}], files)[0]["hunk"] is not None
    assert attach_hunks([{"file": "/abs/日本語 の名前.md", "line": 1}], files)[0]["hunk"] is not None

    # 引用符を含む普通のパスを壊さない
    plain = parse_diff('diff --git a/a"b.md b/a"b.md\n+++ b/a"b.md\n@@ -1,1 +1,1 @@\n-x\n+y\n')
    assert set(plain) == {'a"b.md'}, sorted(plain)

    # クォートと rename の組み合わせ。類似度100%だと ---/+++ 行が無く rename 行だけが頼り
    renamed = parse_diff(
        f'diff --git "i/{_JP}" "w/新しい名前.md"\n'
        "similarity index 100%\n"
        f'rename from "{_JP}"\n'
        "rename to 新しい名前.md\n"
    )
    assert set(renamed) == {"新しい名前.md"}, sorted(renamed)
    assert renamed["新しい名前.md"]["old_path"] == "日本語 の名前.md"


CONCATENATED_DIFF = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -10,2 +10,2 @@ committed
-old
+committed change
 tail
diff --git a/only/committed.py b/only/committed.py
--- a/only/committed.py
+++ b/only/committed.py
@@ -1,1 +1,1 @@
-a
+b
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -50,2 +50,2 @@ uncommitted
-old
+uncommitted change
 tail
"""


def _selftest_concatenated_diffs():
    """SKILL.md 手順2 が `git diff base...HEAD` と `git diff HEAD` を連結するので、
    同じファイルが 2 回現れる。後勝ちで潰さず hunk をまとめること。"""
    files = parse_diff(CONCATENATED_DIFF)
    assert set(files) == {"src/app.py", "only/committed.py"}, sorted(files)

    hunks = files["src/app.py"]["hunks"]
    assert len(hunks) == 2, len(hunks)
    assert [h["new_start"] for h in hunks] == [10, 50]
    assert [h["section"] for h in hunks] == ["committed", "uncommitted"]

    findings = [
        {"file": "src/app.py", "line": 10, "short_summary": "committed 側"},
        {"file": "src/app.py", "line": 50, "short_summary": "uncommitted 側"},
    ]
    matched = attach_hunks(findings, files)
    assert matched[0]["hunk"] is not None, "コミット済み側の hunk が失われている"
    assert matched[1]["hunk"] is not None
    assert matched[0]["hunk"]["section"] == "committed"
    assert matched[1]["hunk"]["section"] == "uncommitted"

    # 完全に同一の hunk が両方に出たら 1 つにまとめる
    same = parse_diff(CONCATENATED_DIFF.split("diff --git a/only")[0] * 2)
    assert len(same["src/app.py"]["hunks"]) == 1

    _selftest_overlapping_hunks()


OVERLAPPING_DIFF = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -9,1 +9,1 @@ committed
-original
+committed9
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -9,1 +9,1 @@ worktree
-committed9
+worktree9
"""


def _selftest_overlapping_hunks():
    """連結した 2 つの diff は同じファイルの別スナップショットに行番号を振る。
    同じ行を含む hunk が両方にあるときは、作業ツリー側（後に連結される方）を採る。"""
    files = parse_diff(OVERLAPPING_DIFF)
    assert len(files["src/app.py"]["hunks"]) == 2

    hunk = attach_hunks([{"file": "src/app.py", "line": 9}], files)[0]["hunk"]
    assert hunk is not None
    assert hunk["section"] == "worktree", hunk["section"]
    assert [ln["text"] for ln in hunk["lines"]] == ["committed9", "worktree9"]


def _selftest_line_types():
    """findings.json は散文から手で書き起こすので line の型が揺れる。"""
    files = parse_diff(SAMPLE_DIFF)
    assert attach_hunks([{"file": "src/app.py", "line": "21"}], files)[0]["hunk"] is not None
    assert attach_hunks([{"file": "src/app.py", "line": "not a number"}], files)[0]["hunk"] is None
    assert attach_hunks([{"file": "src/app.py", "line": None}], files)[0]["hunk"] is None


LOOKALIKE_DIFF = """diff --git a/doc.md b/doc.md
--- a/doc.md
+++ b/doc.md
@@ -1,1 +1,5 @@
 intro
+++ b/other.md
+--- a/other.md
+diff --git a/nope.md b/nope.md
+Binary files a/x and b/x differ
"""


def _selftest_diff_line_lookalikes():
    """diff 自体を含むファイルをレビューすると、hunk 内の追加行がヘッダに見える。"""
    files = parse_diff(LOOKALIKE_DIFF)
    assert set(files) == {"doc.md"}, sorted(files)

    lines = files["doc.md"]["hunks"][0]["lines"]
    assert [ln["text"] for ln in lines] == [
        "intro",
        "++ b/other.md",
        "--- a/other.md",
        "diff --git a/nope.md b/nope.md",
        "Binary files a/x and b/x differ",
    ], [ln["text"] for ln in lines]
    assert [ln["new"] for ln in lines] == [1, 2, 3, 4, 5]
    assert files["doc.md"]["binary"] is False


def _selftest_path_resolution():
    """/code-review は位置を絶対パスで報告するので、そのまま書き起こしても引き当てる。"""
    files = parse_diff(SAMPLE_DIFF)
    findings = [
        {"file": "/Users/me/repos/proj/src/app.py", "line": 21, "short_summary": "絶対パス"},
        {"file": "./src/app.py", "line": 21, "short_summary": "相対の ./ 付き"},
        {"file": "/elsewhere/src/other.py", "line": 21, "short_summary": "存在しない"},
    ]
    matched = attach_hunks(findings, files)
    assert matched[0]["hunk"] is not None, "絶対パスが引き当たらない"
    assert matched[1]["hunk"] is not None, "./ 付きが引き当たらない"
    assert matched[2]["hunk"] is None

    # 接尾辞が複数のファイルに一致するときは推測しない
    ambiguous = parse_diff(
        "diff --git a/x/util.py b/x/util.py\n--- a/x/util.py\n+++ b/x/util.py\n@@ -1,1 +1,1 @@\n-a\n+b\n"
        "diff --git a/y/util.py b/y/util.py\n--- a/y/util.py\n+++ b/y/util.py\n@@ -1,1 +1,1 @@\n-a\n+b\n"
    )
    assert attach_hunks([{"file": "/abs/util.py", "line": 1}], ambiguous)[0]["hunk"] is None


def _selftest_matching(files):
    findings = [
        {"file": "src/app.py", "line": 22, "verdict": "CONFIRMED", "short_summary": "a"},
        {"file": "src/app.py", "line": 999, "verdict": "PLAUSIBLE", "short_summary": "b"},
        {"file": "does/not/exist.py", "line": 1, "short_summary": "c"},
        # rename 前のパスで来ても引き当てる
        {"file": "old/name.py", "line": 7, "verdict": "CONFIRMED", "short_summary": "d"},
        # 削除行だけの指摘は new 側の行番号を持たないので引き当てない
        {"file": "gone.py", "line": 1, "short_summary": "e"},
    ]
    matched = attach_hunks(findings, files)

    assert [f["id"] for f in matched] == [0, 1, 2, 3, 4]
    assert matched[0]["hunk"]["file"] == "src/app.py"
    assert matched[0]["hunk"]["lines"][0]["new"] == 21
    assert matched[1]["hunk"] is None
    assert matched[2]["hunk"] is None
    assert matched[3]["hunk"]["file"] == "new/name.py"
    assert matched[4]["hunk"] is None

    graded_findings = [{**f, "severity": "LOW", "disposition": "issue"} for f in findings]
    payload = build_payload({"target": {"label": "t"}, "findings": graded_findings}, files)
    assert payload["stats"] == {
        "CONFIRMED": 2,
        "PLAUSIBLE": 1,
        "unknown": 2,
        "unmatched": 3,
        "total": 5,
    }, payload["stats"]

    graded = build_payload(
        {
            "findings": [
                {**findings[0], "severity": "HIGH", "disposition": "fix-now"},
                # 大文字小文字と前後の空白は揺れとして受ける。丸めずに正規化する
                {**findings[1], "severity": " high ", "disposition": "Fix-Now"},
            ]
        },
        files,
    )
    assert [f["severity"] for f in graded["findings"]] == ["HIGH", "HIGH"]
    assert [f["disposition"] for f in graded["findings"]] == ["fix-now", "fix-now"]

    # 解釈できない値と欠落は、黙って別の値に倒さず落とす。
    # 倒すとマージを止めるべき指摘が非 blocking として表示されてしまう
    for bad in (
        {"severity": "bogus", "disposition": "fix-now"},
        {"severity": "HIGH", "disposition": "bogus"},
        {"severity": "HIGH"},
        {"disposition": "fix-now"},
    ):
        try:
            build_payload({"findings": [{**findings[0], **bad}]}, files)
        except ValueError:
            pass
        else:
            raise AssertionError(f"不正な値で落ちていない: {bad}")

    # 指摘の顔ぶれや仕分けが変われば別の報告として扱う（仕分けの保存先を分けるため）
    base = {"target": {"label": "t"}, "findings": [{**findings[0], "severity": "LOW", "disposition": "issue"}]}
    assert build_payload(base, files)["report_id"] == build_payload(base, files)["report_id"]
    moved = {**base, "findings": [{**base["findings"][0], "disposition": "fix-now"}]}
    assert build_payload(base, files)["report_id"] != build_payload(moved, files)["report_id"]

    empty = build_payload({"findings": []}, files)
    assert empty["stats"]["total"] == 0


def _selftest_render(files):
    payload = build_payload(
        {
            "target": {"label": "PR #1"},
            # `</script>` と、double-escape 経路を開く `<!--` + `<script` の両方を含める
            "findings": [
                {
                    "file": "src/app.py",
                    "line": 2,
                    "short_summary": "</script> と <!-- と <script を含む",
                    "severity": "LOW",
                    "disposition": "issue",
                }
            ],
        },
        files,
    )
    html = render(payload, TEMPLATE.read_text(encoding="utf-8"))
    assert PLACEHOLDER not in html

    start = html.index("window.__REVIEW_DATA__ = ") + len("window.__REVIEW_DATA__ = ")
    end = html.index(";</script>", start)
    span = html[start:end]
    assert "<" not in span, "データ span に生の < が残っている"
    decoded = json.loads(span)
    assert [ln["new"] for ln in decoded["findings"][0]["hunk"]["lines"]] == [1, None, 2, 3, 4, 5]

    try:
        render(payload, "<html></html>")
    except ValueError:
        pass
    else:
        raise AssertionError("placeholder が無いテンプレートで落ちていない")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings", help="findings.json のパス")
    parser.add_argument("--diff", help="統一 diff のパス")
    parser.add_argument("--out", help="出力する HTML のパス")
    parser.add_argument(
        "--open", action="store_true", dest="open_browser", help="生成後にブラウザで開く"
    )
    parser.add_argument("--selftest", action="store_true", help="同梱テストを実行する")
    args = parser.parse_args(argv)

    if args.selftest:
        _selftest()
        return 0

    missing = [n for n in ("findings", "diff", "out") if not getattr(args, n)]
    if missing:
        parser.error("--" + " と --".join(missing) + " が必要です")

    report = json.loads(Path(args.findings).read_text(encoding="utf-8"))
    files = parse_diff(Path(args.diff).read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")

    try:
        payload = build_payload(report, files)
    except ValueError as exc:
        print(f"NG: {exc}", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(payload, template), encoding="utf-8")

    stats = payload["stats"]
    print(f"{out}: findings {stats['total']} 件 (diff 外 {stats['unmatched']} 件)")
    if args.open_browser:
        webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
