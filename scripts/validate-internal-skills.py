# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""リポジトリ専用skill(.claude/skills/*/SKILL.md)のfrontmatterを検証する。

skills/ 配下は gh skill publish --dry-run が検証するが、gh skill は隠しディレクトリを
見ないため、.claude/skills/ はここで見る。CIとPostToolUseフックで共有する。

- frontmatter(先頭の --- ブロック)があり、YAMLとして読めること
- name がディレクトリ名と一致し、description があること
- metadata.internal が YAML の真偽値 true であること。npx skills が internal とみなす値は
  版で違い、文字列の "true" や "1" を受けない版がある(1.7.4)ため、どの版でも効く真偽値だけを認める。

使い方: uv run scripts/validate-internal-skills.py
問題があれば stderr に出して終了コード 1 で終わる。
"""

import re
import sys
from pathlib import Path

import yaml


class StrictBoolLoader(yaml.SafeLoader):
    """真偽値を true/false だけにした SafeLoader。

    PyYAML は YAML 1.1 に従い yes/on なども真偽値にするが、npx skills が使う YAML 1.2 の
    パーサーではこれらは文字列になる。検証で見逃さないよう、YAML 1.2 と同じ扱いにする。
    """


StrictBoolLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:bool"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
StrictBoolLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def read_frontmatter(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].rstrip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.rstrip() == "---":
            return "\n".join(lines[1:i])
    return None


def validate(path: Path, rel: str) -> list[str]:
    text = read_frontmatter(path)
    if text is None:
        return [f"{rel}: frontmatter(---ブロック)が見つかりません"]
    try:
        data = yaml.load(text, Loader=StrictBoolLoader)
    except yaml.YAMLError as e:
        return [f"{rel}: frontmatterがYAMLとしてパースできません: {e}"]
    if not isinstance(data, dict):
        return [f"{rel}: frontmatterがマッピングではありません"]

    errors = []
    dir_name = path.parent.name
    name = data.get("name")
    if not name:
        errors.append(f"{rel}: frontmatterに name がありません")
    elif name != dir_name:
        errors.append(
            f"{rel}: frontmatterの name '{name}' がディレクトリ名 '{dir_name}' と一致しません"
        )
    if not data.get("description"):
        errors.append(f"{rel}: frontmatterに description がありません")

    metadata = data.get("metadata")
    internal = metadata.get("internal") if isinstance(metadata, dict) else None
    if internal is not True:
        errors.append(
            f"{rel}: リポジトリ専用skillには metadata.internal: true(真偽値)が必要です(npx skills の配布対象から外すため)"
        )
    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    errors = []
    for path in sorted(repo_root.glob(".claude/skills/*/SKILL.md")):
        errors += validate(path, str(path.relative_to(repo_root)))
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
