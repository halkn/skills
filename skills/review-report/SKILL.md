---
name: review-report
license: MIT
description: >
  `/code-review` の指摘を仕分け、今回直す・確認する・Issue に切る・対応しないを番号付きの表で示し、
  issue の完了条件と diff を照らしてマージ可否を出す。頼まれたときは、
  指摘と該当 diff を並べた1枚のHTMLレポートにする。`/code-review` の後で
  「どれを直すか決めて」「指摘を仕分けて」「レビュー結果を整理して」と言われたとき、
  指摘への対応を自分で決めて進めるとき、および「レビュー結果をHTMLで見たい」
  「PRのレビュー指摘を可視化して」「code review の結果をブラウザで見せて」と言われたときに使う。
  レビュー自体は行わず、`/code-review` の結果を仕分ける。
allowed-tools: >
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py *),
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/validate_review.py *)
argument-hint: '[pr-number | pr-url]'
---

# review-report

`/code-review` の指摘を仕分け、番号付きの表で示す。ユーザーは「#2 を外して」「#1 と #3 を直して PR まで」のように番号で指示できる。頼まれたときは、指摘と該当 diff hunk を 1 枚の自己完結 HTML に並べる（指摘が 10 件以上なら HTML を勧める）。

**この skill はコードの観点を持たない。** 何を指摘するかは `/code-review` が決める。ここが持つのは、出た指摘の仕分けの基準と、issue の完了条件との突合だけ。両方にコードの観点を書くと二重メンテになる。

## 前提

- `python3`（HTML を作るときだけ。標準ライブラリのみ使う）
- PR モードと要件との突合は `gh`。GitHub 以外のホスティングではどちらも使わない

## 手順

### 1. findings を用意する

- **会話に `/code-review` の結果が既にあれば、それをそのまま使う。** レビューをやり直さない
- 無ければ `/code-review` を起動し、完了を待ってから次に進む

引数に PR 番号か PR の URL があれば **PR モード**、無ければ現在のブランチの **ローカルモード**。PR モードに入る前に `git remote -v` でホストを確認し、`github.com` 以外ならローカルモードに切り替えるかユーザーに確認する。

PR モードでは、人間のレビューの inline コメントも取り込む。

```bash
gh api "repos/{owner}/{repo}/pulls/<number>/comments" \
  --jq '.[] | {file: .path, line: (.line // .original_line), author: .user.login, body: .body}'
```

取れたコメントは Claude の指摘と同じく手順 3 で仕分け、同じ表に並べる。人間の指摘と Claude の指摘が同じ表に並ぶことが PR モードの主な価値なので、コメントが 0 件でなければ必ず入れる。解決済み（outdated）のコメントは入れない。

### 2. 要件と突合する

対象の issue を探し、完了条件を 1 項目ずつ diff と照らす。探し方・照らし方・突合しないときの扱いは [references/triage.md](references/triage.md) の「要件との突合」にある。

### 3. 仕分ける

各指摘に `severity`（`HIGH`/`MEDIUM`/`LOW`）と `disposition`（`fix-now`/`ask`/`issue`/`wont-fix`）を付ける。基準は [references/triage.md](references/triage.md) にある。要点:

- **`fix-now` はその変更が作る契約の中に壊れる入力があるかで決める。** 「今の呼び出し元では踏まない」は見送る理由にしない
- **意図や仕様が断定できないものは推測で決めず `ask` にする。** 確かめたいことを 1 文で添える
- **指摘は全件残す。** 対応しないものも落とさず `wont-fix` にする

番号は、人間のコメントを含む全件を severity 順（HIGH → LOW。同じ severity の中は `/code-review` の指摘、人間のコメントの順）に並べて `#1` から振る。HTML を作るときも同じ順で findings.json に書く。順が崩れていると `render_review.py` が落とすので、番号はずれない。

### 4. 提示する

判定を 1 行、続けて指摘の表、突合したなら要件の表を出す。

```markdown
**確認待ち** — 直すもの 2 件（#1・#2）、確認が要るもの 1 件（#3）

| # | 仕分け | severity | 位置 | 指摘 | 理由・確かめたいこと |
|---|---|---|---|---|---|
| 1 | 今回直す | HIGH | `src/parse.py:42` | 空の入力で例外になる | |
| 3 | 確認する | MEDIUM | `src/run.py:10` | 同期で呼んでいる | 意図した同期処理か（違えば今回直す） |
| 4 | Issue に切る | LOW | `src/io.py:7` | 既存の読込で close 漏れ | 今回の変更より前からある |

| # | 要件（#24 の完了条件） | 状態 | 根拠 |
|---|---|---|---|
| 1 | 空の入力ではエラーを返す | 満たす | `src/parse.py:42` |
| 2 | 件数の上限を設定で変えられる | 実装に無い | |
```

- 判定は `fix-now` が 1 件でもあれば「このままはマージしない」、無くても `ask` か「実装に無い」「判断できない」要件があれば「確認待ち」、どちらも無ければ「マージしてよい」
- 表の「指摘」は `/code-review` の記述を短く詰めたもので、言い換えない
- 最後に、次の一手を 1 つ提案して確認する（例: 「#1・#2 を直してから PR まで進めてよいですか。#3 は答えをもらってから仕分けます」）
- 指摘が 10 件以上なら、HTML にできることを 1 文添える

ユーザーが仕分けを変えたら、そのとおりに直して進め、最後の報告に変えた内容を 1 行ずつ残す（[references/triage.md](references/triage.md) の「人が仕分けを変えたとき」）。

**PR まで任されているとき**（git-flow の手順の途中など）は、確認を挟まずに `fix-now` を直して進める。`ask` には手を付けず、PR 本文と最後の報告に「確認事項」として番号付きで並べる。`issue` は、issue を立てるよう頼まれていなければ報告に並べるだけにする。

### 5. HTML にする（頼まれたときだけ）

ユーザーに頼まれたときだけ、以下の 5-1 〜 5-5 で HTML を作る。頼まれていなければここで終わる。

#### 5-1. 作業ディレクトリを決める

以降の中間ファイルをここに置く。

```bash
root=$(git rev-parse --show-toplevel) || exit 1
work_root="$root/.scratch/review-report"
if ! git check-ignore -q "$work_root/"; then
  mkdir -p "$root/.scratch" || exit 1
  if [ ! -e "$root/.scratch/.gitignore" ]; then
    printf '%s\n' '*' >"$root/.scratch/.gitignore" || exit 1
  fi
  if ! git check-ignore -q "$work_root/"; then
    echo ".scratch/ を ignore させられませんでした" >&2
    exit 1
  fi
fi
work="$work_root/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$work"
ls -1d "$work_root"/*/ 2>/dev/null | sort -r | tail -n +11 | while IFS= read -r old; do
  rm -rf "$old"
done
echo "work=$work"
```

置き場は、セッションに scratchpad があっても作業木のルートの中の `.scratch/review-report/` にする。以降の手順は Bash のコマンドに `$work` のパスを書いて読み書きする。作業ディレクトリの外のパス（scratchpad を含む）を Bash のコマンドに書くと、`permissions.blockReadsOutsideWorkingDirectories` を有効にした環境では auto モードでも毎回確認が出る。環境変数から組んだパスでも同じなので、`$TMPDIR` や `/tmp` にもしない（Claude Code v2.1.326 で確認）。

シェル変数は Bash の呼び出しをまたいで残らない。以降の手順の `$work` は、ここで出力した `work=` の絶対パスに置き換えて書く。作業木ごとに `.scratch/` が分かれるので、同じリポジトリの複数 worktree のレポートも混ざらない。

- `.scratch/` が ignore されていなければ、`.scratch/.gitignore` に `*` の 1 行を書いて ignore させる。作業木の中のファイルなので、linked worktree でも作業ディレクトリの外（本体のリポジトリの `.git/info/`）に触れない。`*` は `.gitignore` 自身にも一致するので、これも未追跡のファイルとして出ない
- `.scratch/.gitignore` が既にあれば、上書きせず中身もそのままにする。ignore されたかは `git check-ignore -q` で確かめ、されていなければ `$work` を作らずに止まる。ignore されないまま `diff.patch` を置くと、レビュー対象のソースが commit に混ざり得る
- `.scratch/review-report/` はこの skill の置き場で、今回の分を含めて新しい 10 件だけ残し、それより古いものは消す（`.scratch/` はセッションの終わりに消えず、`diff.patch` にはレビュー対象のソースがそのまま入るため）。`.scratch/` の他のファイルには触れない。手で消してもよい

変数名を `base` にしない。次のステップが diff の基準 ref を `base` に入れるため、衝突すると基準 ref 無しのときの報告がパス文字列になる。

#### 5-2. diff を取る

PR モード: base ブランチ名を調べ、base・PR head の順に fetch してから、ローカルで diff を書き出す。`gh` と `git fetch` は、それぞれ何も前置きせず 1 コマンドだけで実行する。

```bash
gh pr view <number> --json baseRefName --jq .baseRefName
git fetch origin <baseRefName>
git fetch origin pull/<number>/head
```

```bash
git diff "origin/<baseRefName>...FETCH_HEAD" >"$work/diff.patch"
```

`gh pr diff > file` にしないのは、ファイルへのリダイレクトを含む呼び出しを丸ごと sandbox の中で動かす環境があり、そこでは `gh` の通信や認証情報の読取が失敗するため。`FETCH_HEAD` は直前の fetch で上書きされるので、PR head の fetch を最後にする。

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

#### 5-3. findings.json を書く

`$work/findings.json` に書く。スキーマと書き起こしの規約は [references/findings-schema.md](references/findings-schema.md) にある。手順 3 の仕分けと手順 2 の要件の表を、提示した番号の順のまま移す。手順 1 で取り込んだ人間のコメントは `category: "human"`、`author` にログイン名を入れる。

`assessment.note` にマージ可否の**根拠**を短く書く。可否そのもの（「マージしてよい」等）は書かない。画面が仕分けから算出し、ユーザーが仕分けを変えれば追随するため、note に結論を書くと食い違う。

#### 5-4. レンダリングして検証する

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py \
  --findings "$work/findings.json" --diff "$work/diff.patch" --out "$work/index.html"
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_review.py \
  --html "$work/index.html" --expect-findings <件数>
```

`validate_review.py` が落ちたら HTML をユーザーに渡さず、原因を直してからやり直す。

「diff 外」と報告された指摘は、`line` を head 側の行番号として書けていないか、diff の取り方が対象とずれている。まずそこを疑う。件数が合っていれば、行が本当に diff の外（既存バグの指摘など）なので、そのままでよい。

ブラウザで開くなら `--open` を足すか `open "$work/index.html"` を実行する。**ユーザーに頼まれない限り勝手に開かない。** sandbox が `open` を禁じている環境（macOS で Launch Services が塞がれ `-10822` 等で失敗する）では、`$work` を展開した絶対パスで `open <path>` を提示し、ユーザーに `!` 付きで実行してもらう。

#### 5-5. 報告する

- HTML の絶対パス（`$work` を展開したもの。ユーザーが `!open <path>` で開くときに、どのディレクトリからでも使える）
- 判定と、`fix-now`・`ask` の件数
- 「diff 外」の件数
- 画面で仕分けを決めたら「指示文をコピー」で貼り戻せること

指摘の中身を全部テキストで並べ直さない。手順 4 で既に出していれば、それを繰り返さない。

## 画面の構成

画面で仕分けを決め、その結果を指示文として Claude に貼り戻すための 1 枚の画面。テキストで提示した表と同じ番号・同じ並びで出す。

- **上部の固定バー:** 判定（「このままはマージしない」「確認待ち」「マージしてよい」）、4 区分の件数、「指示文をコピー」ボタン。判定は画面の仕分けに即座に追随する
- **指摘の表:** 1 行に 1 指摘で、行の中の 4 択で仕分けを変える。行を開くと、その下に summary・failure scenario・該当 hunk が出る
  - 初期値から変えた行には、変えた理由を書く欄が出る（任意）
  - `ask` の行には、確かめたいことと答えの欄が出る
- **要件との対応:** 突合したときだけ、表の下に出る
- **キー操作:** `j`/`k` で行を移り、`1`〜`4` で仕分けを選び、`Enter` で開閉する。入力欄にいる間は効かない（`Esc` で抜ける）

**指示文の形:** 「#1・#4 を直して。#2 は Issue に。#3 は対応しない。」に続けて、変えた仕分け（初期値→変更後と理由）と確認への答えが入る。ユーザーがこれを貼り戻したら、手順 4 の仕分けへの指示として扱う。変えた仕分けは、報告に残す差分でもある。Clipboard API は secure context でしか使えず、`file://` で開くこの画面ではたいてい無いので、`execCommand('copy')` で書く。それも失敗したら、文を選択した状態で出す。

**画面上の変更は `findings.json` には書き戻らない。** 指示文が正本になる。変更は `localStorage` に残るので、閉じて開き直しても保たれる。保存キーは `disposition` と要件の状態を含むので、作り直せば古い上書きは引き継がれない。「初期値に戻す」ボタンでも消せる（確認への答えは残す）。

## 生成物の性質

出力は外部リソースを一切参照しない単一の HTML で、オフラインでも開ける。`validate_review.py` がこれを検証する。CDN やフォントを足したくなっても入れない（レビュー対象のコードが載る画面なので、外部へのリクエストを発生させない）。

## 開発時のテスト

diff パーサと描画のテストはスクリプトに同梱している。

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py --selftest
```
