# dev-docs の上流

`skills/dev-docs` が参考にしている skill・名前で呼ぶ skill と、確かめる対象・取り込むかを決める基準。確かめ方と取り込みの手順は `.claude/skills/skill-development/SKILL.md` の「上流の取り込み」にある。

## figure-docs（参考にする）

- リポジトリ: <https://github.com/u-ichi/agent-plugins>（`main`。MIT。著作権表示は `skills/dev-docs/references/LICENSE-agent-plugins`）
- 最後に目を通したコミット: `02a8453a007900603fee5c51d64363065976c6a2`
- 追うパス:
  - `LICENSE`
  - `plugins/figure-docs/skills/figure-docs/SKILL.md`
  - `plugins/figure-docs/skills/figure-docs/references/dev.html`
- 写して同期しない。`skills/dev-docs/references/figures.md` は figure-docs を参考に、Markdown の開発文書に合わせて書いた dev-docs の決まりである

参考にしている点:

- `SKILL.md` の「開発の図の分類とルール」（分類、四角は6つまで、矢印に内容、連作、変更の前後の色分け、状態の図の検証）
- `SKILL.md` の「言葉のそろえ方と読み手への配慮」
- `SKILL.md` の「図・表・文章の使い分け」と「図の形を選ぶ手順」（問いを1文に決める → 分類 → 形）
- `references/dev.html` の図の一覧（名前・使う場面・Mermaid の種類）。figures.md の「図の一覧」に、Mermaid で描けるものだけを載せた

採らない点:

- 資料全体を「図を先に描き、文章は図ごとの要点1行」にする方針。手順を文章と箇条書きで書く Runbook・README に合わない
- 事業の図（`references/business.html`、FT Visual Vocabulary 由来の分類、数値のある図のルール）。開発文書の範囲の外
- SVG・HTML・Artifact で描く手順と、HTML の表示の確かめ。dev-docs は Markdown の中に Mermaid で描く
- Mermaid で描けない見本（Context Map、Wardley map、Event storming、Timing diagram、Flame graph など）。Markdown の文書では画像を添付するしかない

## yomiyasu（名前で呼ぶ）

- リポジトリ: <https://github.com/nanaism/yomiyasu>（MIT）
- 写さず、版も固定しない。版の更新が速く、lint のスクリプトも含むため、写すと追従の手間が大きい
- 確かめるファイル: `main` の `skills/yomiyasu/SKILL.md`

頼っている挙動（確かめる記述）:

| 記述 | 頼っている理由 |
|---|---|
| 「名前を出して頼んだとき」 | dev-docs は yomiyasu を名前で呼ぶ。description が名前を出した依頼で発動しなくなると、推敲が動かない |
| 「依頼で指定された見出しの形」 | dev-docs は見出しの方針を「指定された見出しの形」として渡す。この決まりが無いと、設計書・ADR の結論の1文の見出しが項目名に直される |
| 「manual」 | dev-docs は Runbook・README に種類 manual を渡す |

頼る挙動を増やしたら（yomiyasu に渡す指定を足すなど）、その根拠になる記述を上の表に足す。
