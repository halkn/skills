# findings.json のスキーマ

`render_review.py` が読む入力の形式と、`/code-review` の出力からここへ書き起こすときの規約。

## 全体

```json
{
  "target": {
    "kind": "pr",
    "label": "PR #12 — add review-report skill",
    "url": "https://github.com/halkn/skills/pull/12",
    "base": "main",
    "head": "skill/review-report"
  },
  "level": "high",
  "assessment": {
    "note": "diff パーサに、この skill 自身の手順で必ず踏む欠陥が2件ある。…"
  },
  "findings": []
}
```

| キー | 必須 | 内容 |
|---|---|---|
| `target.kind` | ○ | `"pr"` または `"local"` |
| `target.label` | ○ | 画面上部に出す 1 行。PR なら `PR #<n> — <title>`、ローカルなら `<base>...<head>` |
| `target.url` | | PR の URL。`local` では省く |
| `target.base` | | 比較元の ref |
| `target.head` | | 比較先の ref |
| `level` | | `/code-review` を実行した effort level（`low`〜`max`）。不明なら省く |
| `assessment.note` | | マージ可否の根拠を述べる短い文章。**可否そのものは書かない**（画面が仕分けから算出し、ユーザーが仕分けを変えれば追随するため） |
| `findings` | ○ | 下記オブジェクトの配列。0 件でもよい |

## findings の 1 要素

`file` から `outcome` までのキー名と意味は `ReportFindings` ツールに揃える。将来ホストアプリ側の構造化出力をそのまま流し込めるようにするため、この範囲に独自のキーを足さない。`severity` 以降はこの skill の追加。

```json
{
  "file": "skills/review-report/scripts/render_review.py",
  "line": 42,
  "category": "correctness",
  "verdict": "CONFIRMED",
  "short_summary": "rename された diff でファイル名を引き当てられない",
  "summary": "…（1 文で欠陥を述べる）",
  "failure_scenario": "…（具体的な入力・状態 → 誤った出力やクラッシュ）",
  "outcome": null,
  "severity": "MEDIUM",
  "disposition": "issue",
  "disposition_reason": "実害はあるが今回の変更に起因しないため別 Issue にする"
}
```

| キー | 必須 | 内容 |
|---|---|---|
| `file` | ○ | リポジトリルートからの相対パス。`/code-review` が返す絶対パスも引き当てるが、diff 内に同名のファイルが複数あると解決できないので相対に直して書く |
| `line` | ○ | **head 側（変更後）の行番号**。1 始まり |
| `category` | | `correctness` / `simplification` / `efficiency` / `test-coverage` など kebab-case。人間のレビューコメント由来なら `human` |
| `verdict` | | `CONFIRMED` / `PLAUSIBLE`。判定が出ていなければ `null` |
| `short_summary` | ○ | 一覧に出す 60 文字以内のラベル。主張だけを書き、理由や影響を続けない |
| `summary` | ○ | 欠陥を述べる 1 文 |
| `failure_scenario` | | 失敗の再現条件 |
| `outcome` | | 修正後の再報告でのみ `fixed` / `skipped` / `no_change_needed`。通常は `null` |
| `author` | | `category: "human"` のとき、コメントした人の GitHub ログイン名 |
| `severity` | ○ | `HIGH` / `MEDIUM` / `LOW`。レビューが severity を出していればそれを移す |
| `disposition` | ○ | `fix-now` / `issue` / `wont-fix`。下記の基準で決める |
| `disposition_reason` | | `issue` と `wont-fix` のとき、そう決めた理由を 1 文で |

### severity の決め方

レビューが severity を出していればそのまま移す。出していない場合だけ、`failure_scenario` の実害から決める。

- `HIGH` — データの破壊・情報漏洩・不可逆な操作、または本番の主要な経路が壊れる
- `MEDIUM` — 実際に踏む条件があり、踏むと誤った出力になる
- `LOW` — 実害はあるが条件が限定的、または品質・保守性の問題

### disposition の決め方

**マージ可否は `disposition` から画面が算出する。** `fix-now` が 1 件でも残っていれば「このままはマージしない」になるので、その重みで判断する。

- `fix-now` — **今回の変更が持ち込んだ欠陥**で、マージ前に直すべきもの。この PR を通すと本番に入ってしまうもの
- `issue` — 実害はあるが、今回の変更に起因しない（既存バグ）か、修正が今回の範囲を超えて別 PR になるもの
- `wont-fix` — 意図した挙動、実害が無視できる、または今回の設計判断として受け入れるもの

判断に迷ったら `fix-now` に寄せない。**`fix-now` は「マージを止める」という主張**なので、止めるほどではないものは `issue` にする。

`disposition` は画面上でユーザーが変更でき、変更はブラウザに保持される。ここに書くのは初期値であって最終決定ではない。

## 書き起こしの規約

ターミナルセッションの `/code-review` は findings を会話のテキストとして返す（`ReportFindings` 経由の構造化出力になるのはホストアプリの場合のみ）。そのテキストからこの JSON を書き起こす際は次に従う。

- **1 指摘 = 1 オブジェクト。** 同じファイルの複数箇所をまとめて 1 件にしない。行ごとに分ける
- **`line` は head 側の行番号。** `/code-review` は `file:line` 形式で位置を示すのでその数値をそのまま使う。diff の hunk ヘッダの数値ではない
- **出ていない情報は `null` にする。** 推測で `verdict` や `category` を埋めない
- **文言を要約し直さない。** `summary` と `failure_scenario` はレビューの記述をそのまま移す。`short_summary` だけはこちらで 60 文字以内に詰める
- **指摘を取捨選択しない。** 対応しないと判断した指摘も全件入れる。判断は HTML を見てから行う

`gh` から取り込む人間のレビューコメントは `category: "human"`、`verdict: null`、`author` にログイン名を入れ、コメント本文を `summary` に、その 1 行目を `short_summary` にする。
