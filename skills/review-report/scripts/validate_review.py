#!/usr/bin/env python3
"""生成した HTML レビューレポートを検証する。

指摘が欠落していないか、オフラインで開けるか（外部リソース参照がゼロか）を見る。
問題があれば内容を出力して非ゼロで終了する。
"""

import argparse
import html as html_mod
import json
import re
import sys
from pathlib import Path

DATA_PREFIX = "window.__REVIEW_DATA__ = "
SEVERITIES = ("HIGH", "MEDIUM", "LOW")
DISPOSITIONS = ("fix-now", "issue", "wont-fix")
RESOURCE_ATTR = re.compile(r"""\b(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
HIDDEN_RULE = re.compile(r"\[hidden\]\s*\{[^}]*display\s*:\s*none\s*!important", re.I)


def extract_data(html):
    start = html.find(DATA_PREFIX)
    if start < 0:
        raise ValueError(f"{DATA_PREFIX} が見つかりません")
    start += len(DATA_PREFIX)
    end = html.find(";</script>", start)
    if end < 0:
        raise ValueError("データ埋め込みの script が閉じていません")
    span = html[start:end]
    if "<" in span:
        raise ValueError("データ span に生の < が残っている（HTML パーサが script を閉じられない）")
    return json.loads(span)


def strip_data_script(html):
    """埋め込みデータの span を落とす。レビュー対象の diff 本文を markup として読まないため。"""
    start = html.find(DATA_PREFIX)
    if start < 0:
        return html
    end = html.find(";</script>", start)
    if end < 0:
        return html
    return html[:start] + html[end:]


def external_resources(html):
    """markup が外部ホストを参照している src / href を返す。"""
    found = []
    for url in RESOURCE_ATTR.findall(strip_data_script(html)):
        url = html_mod.unescape(url)
        if url.lower().startswith(("http://", "https://", "//")):
            found.append(url)
    return found


def check(html, expect_findings=None):
    problems = []
    data = extract_data(html)
    findings = data.get("findings", [])

    if expect_findings is not None and len(findings) != expect_findings:
        problems.append(f"findings が {len(findings)} 件、--expect-findings は {expect_findings} 件")

    for url in external_resources(html):
        problems.append(f"外部リソースを参照している: {url}")

    # タブの切替は hidden 属性に頼っている。author origin の display 指定に負けると
    # サマリーの下に指摘ペインが重なって出るが、DOM を見るだけでは分からない
    if not HIDDEN_RULE.search(html):
        problems.append("[hidden] を display: none !important で押さえる CSS がありません")

    for item in findings:
        where = f"findings[{item.get('id')}]"
        for key in ("file", "short_summary"):
            if not item.get(key):
                problems.append(f"{where} に {key} がありません")
        if item.get("line") is None:
            problems.append(f"{where} に line がありません")
        if item.get("severity") not in SEVERITIES:
            problems.append(f"{where} の severity が不正: {item.get('severity')!r}")
        if item.get("disposition") not in DISPOSITIONS:
            problems.append(f"{where} の disposition が不正: {item.get('disposition')!r}")

    return data, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True, help="検証する HTML のパス")
    parser.add_argument("--expect-findings", type=int, help="期待する findings の件数")
    args = parser.parse_args(argv)

    html = Path(args.html).read_text(encoding="utf-8")
    try:
        data, problems = check(html, args.expect_findings)
    except ValueError as exc:
        print(f"NG: {exc}", file=sys.stderr)
        return 1

    if problems:
        for problem in problems:
            print(f"NG: {problem}", file=sys.stderr)
        return 1

    stats = data.get("stats", {})
    print(f"ok: findings {stats.get('total', 0)} 件、外部リソース参照なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
