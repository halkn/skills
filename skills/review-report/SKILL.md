---
name: review-report
description: >
  code review の指摘を、該当 diff と並べて読める1枚のHTMLレポートにする。
  「レビュー結果をHTMLで見たい」「PRのレビュー指摘を可視化して」「指摘を一覧で確認したい」
  「code review の結果をブラウザで見せて」と言われたとき、および `/code-review` の指摘が
  多くて取捨選択に判断が要るときに使う。レビュー自体は行わず、`/code-review` の結果を描画する。
allowed-tools: >
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py *),
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/validate_review.py *)
argument-hint: "[pr-number | pr-url]"
---

# review-report

`/code-review` の指摘と、その指摘が指す diff hunk を、1 枚の自己完結 HTML に並べる。左に指摘一覧、右に選択中の指摘の詳細と該当 hunk が出る。

**この skill はレビュー観点を持たない。** 何を指摘するかは `/code-review` が決める。ここは「出た指摘をどう読ませるか」だけを担う。両方に観点を書くと二重メンテになる。

## 前提

- `python3`（標準ライブラリのみ使う。追加インストールは不要）
- PR モードのみ `gh`。GitHub 以外のホスティングでは PR モードに入らない

## 手順

### 1. 対象を決める

引数に PR 番号か PR の URL があれば **PR モード**。無ければ現在のブランチの **ローカルモード**。

PR モードに入る前に `git remote -v` でホストを確認する。`github.com` 以外なら PR モードは使えないので、ローカルモードに切り替えるかユーザーに確認する。

作業ディレクトリを決めて、以降の中間ファイルをそこに置く。

```bash
root=$(git rev-parse --show-toplevel)
slug=$(printf '%s' "${root#/}" | tr -c 'A-Za-z0-9._-' '-')
base="${XDG_STATE_HOME:-$HOME/.local/state}/review-report/$slug"
work="$base/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$work"
ls -1d "$base"/*/ 2>/dev/null | sort -r | tail -n +11 | while IFS= read -r old; do
  rm -rf "$old"
done
```

対象リポジトリの中には何も書かない。`.gitignore` の変更も不要。

リポジトリの識別にはトップレベルの絶対パス全体を使う。basename だけだと別 owner の同名リポジトリや同じリポジトリの複数 worktree が 1 つのディレクトリに混ざり、どの作業木のレポートか区別できない。

`diff.patch` にはレビュー対象のソースがそのまま入るので、同一リポジトリの過去分は最新 10 件だけ残して消す。手で消してよい。

### 2. diff を取る

PR モード:

```bash
gh pr diff <number> > "$work/diff.patch"
```

ローカルモード（コミット済みと未コミットの両方を含める）:

```bash
default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)
upstream=$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)
: >"$work/branch.patch"
for candidate in "$upstream" "$default"; do
  [ -n "$candidate" ] || continue
  git rev-parse --verify --quiet "$candidate" >/dev/null 2>&1 || continue
  git diff "$candidate"...HEAD >"$work/branch.patch"
  [ -s "$work/branch.patch" ] && { base="$candidate"; break; }
done
cat "$work/branch.patch" >"$work/diff.patch"
git diff HEAD >>"$work/diff.patch"
echo "base=${base:-なし（未コミット変更のみ）}"
```

**空かどうかは `git diff "$candidate"...HEAD` だけで判定する。** 連結後のファイルで判定すると、未コミット変更が 1 つでもあれば最初の候補で必ず非空になり、そこで止まってコミット済みのブランチ差分が丸ごと落ちる。

候補を順に試すのは、push 済みのブランチでは `@{upstream}` が HEAD と一致して差分が空になるため。git-flow の順序（commit → push → `/code-review` → `/review-report`）はまさにその状態なので、既定ブランチへのフォールバックが要る。

**どの候補でも空なら base 無しとして、作業ツリーの差分だけを対象にする。** ここで `HEAD~1` に落とすと、まだコミットしていないブランチ（HEAD が既定ブランチと同じコミット）で無関係な直前のコミットを引き込む。ブランチのコミットが対象に入っていないと分かったときは、base を推測せずユーザーに確認する。

選ばれた base は最後の報告に書く。`/code-review` の対象範囲とずれることがあり、ずれていれば「diff 外」の件数として現れる。

**未追跡ファイルは `git diff` に出ない。** 新規ファイルの指摘を「diff 外」にしないために、レビュー前にコミットしておく（git-flow の手順ではコミット・push の後にレビューするので、通常はこの条件を満たしている）。

### 3. findings を用意する

- **会話に `/code-review` の結果が既にあれば、それをそのまま使う。** レビューをやり直さない
- 無ければ `/code-review` を起動し、完了を待ってから次に進む

ターミナルセッションの `/code-review` は findings を会話のテキストとして返す。ファイルには書かれないので、次のステップで自分で書き起こす。

### 4. PR モードなら人間のレビューも取り込む

```bash
gh api "repos/{owner}/{repo}/pulls/<number>/comments" \
  --jq '.[] | {file: .path, line: (.line // .original_line), author: .user.login, body: .body}'
```

取れた inline コメントを `category: "human"`、`author` にログイン名を入れて findings に混ぜる。人間の指摘と Claude の指摘が同じ画面に並ぶことが PR モードの主な価値なので、コメントが 0 件でなければ必ず入れる。

解決済み（outdated）のコメントは入れない。

### 5. findings.json を書く

`$work/findings.json` に書く。スキーマと書き起こしの規約は [references/findings-schema.md](references/findings-schema.md) にある。**指摘は全件入れる。** 対応しないと判断したものも落とさない。

各指摘に `severity`（`HIGH`/`MEDIUM`/`LOW`）と `disposition`（`fix-now`/`issue`/`wont-fix`）を付ける。`disposition` の初期値を決めるのはここでの仕事で、基準は findings-schema.md にある。**`fix-now` は「マージを止める」という主張**なので、止めるほどではないものは `issue` に寄せる。`issue` と `wont-fix` には `disposition_reason` を 1 文添える。

`assessment.note` にマージ可否の**根拠**を短く書く。可否そのもの（「マージしてよい」等）は書かない。画面が仕分けから算出し、ユーザーが仕分けを変えれば追随するため、note に結論を書くと食い違う。

### 6. レンダリングして検証する

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py \
  --findings "$work/findings.json" --diff "$work/diff.patch" --out "$work/index.html"
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_review.py \
  --html "$work/index.html" --expect-findings <件数>
```

`validate_review.py` が落ちたら HTML をユーザーに渡さず、原因を直してからやり直す。

「diff 外」と報告された指摘は、`line` を head 側の行番号として書けていないか、diff の取り方が対象とずれている。まずそこを疑う。件数が合っていれば、行が本当に diff の外（既存バグの指摘など）なので、そのままでよい。

ブラウザで開くなら `--open` を足すか `open "$work/index.html"` を実行する。**ユーザーに頼まれない限り勝手に開かない。**

### 7. 報告する

- HTML のパス
- マージ可否の結論と、`fix-now` に仕分けた指摘の件数
- severity × 仕分けの内訳（1 行で足りる）
- 「diff 外」の件数

指摘の中身を全部テキストで並べ直さない。それをやると HTML を作った意味が無くなる。

## 画面の構成

**サマリー**タブが最初に出る。マージ可否の判定（`fix-now` が 1 件でも残っていれば「このままはマージしない」）、severity × 仕分けの内訳表、`fix-now` と `issue` の指摘一覧、Issue 本文を組み立てるボタンが並ぶ。

**指摘**タブは severity 順の一覧と、選択した指摘の詳細・仕分けラジオ・該当 hunk。仕分けを変えるとサマリーの判定に即座に反映される。変更は `localStorage` に残るので、閉じて開き直しても保たれる。

**画面上の変更は `findings.json` には書き戻らない。** 恒久化したいなら findings.json の `disposition` を直して作り直す。保存キーは `disposition` を含むので、作り直せば古い上書きは引き継がれない。サマリーの「仕分けを初期値に戻す」ボタンでも消せる。

## 生成物の性質

出力は外部リソースを一切参照しない単一の HTML で、オフラインでも開ける。`validate_review.py` がこれを検証する。CDN やフォントを足したくなっても入れない（レビュー対象のコードが載る画面なので、外部へのリクエストを発生させない）。

## 開発時のテスト

diff パーサと描画のテストはスクリプトに同梱している。

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py --selftest
```
