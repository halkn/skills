# 検証・レンダリングのワークフロー

`mermaid-diagrams/SKILL.md` の詳細ガイド。生成したMermaid図は「正しく
描画されるまで完了扱いにしない」という規律を徹底する。

## mermaid-cli(mmdc)

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i input.mmd -o output.svg
```

PNG/PDFは出力先の拡張子で切り替わる。`-t dark -b transparent`でテーマ・
背景を指定できる。stdin対応(`cat file | mmdc -i - -o out.svg`)。npx実行も
可能(`npx -p @mermaid-js/mermaid-cli mmdc ...`)。Dockerは
`minlag/mermaid-cli`イメージが使える。

## `scripts/validate.sh` の使い方

このskillには`scripts/validate.sh`を同梱している。

```bash
scripts/validate.sh diagram1.mmd diagram2.mmd
```

**動作**:

1. `mmdc`(無ければ`npx`経由)が使えるかを検出する。どちらも使えない場合は
   インストール手順を表示して終了コード`3`で終わる(クラッシュしない)。
2. 各ファイルを一時SVGファイルに変換してパース可否を検証する。
3. サンドボックス関連のエラー(後述)を検知した場合は、同梱の
   `scripts/puppeteer-config.json`を使って自動的に1回だけ再試行する。
4. ファイルごとに`OK: <file>`/`NG: <file>`を出力し、最後にサマリを表示する。

**終了コード**: `0`=全ファイルOK、`1`=検証失敗ファイルあり、`2`=使い方エラー
(引数無し)、`3`=`mmdc`/`npx`とも使用不可(未検証)。

**注意**: このスクリプトが検証するのはMermaid記法としてのパース可否のみで
あり、対象レンダラー(GitHub/GitLab等)で実際にどう描画されるかは保証しない。
機能ごとの描画互換性は`rendering-compatibility-guide.md`を別途確認する。

## 検証→修正ループ

1. 図を生成し`.mmd`として保存する。
2. `scripts/validate.sh <file>`を実行する。
3. `NG`の場合、出力されたエラーメッセージと該当図種の
   `references/*-guide.md`(または`SKILL.md`本体の構文チェックリスト)を
   突き合わせて原因を特定し修正する。
4. 再度`scripts/validate.sh`を実行し、`OK`になるまで2-3を繰り返す。
5. `OK`になって初めて完了として報告する。

## CI/コンテナでのサンドボックス問題

`mmdc`は内部でPuppeteer/Chromiumを使うため、CI(特にUbuntu 24.04以降の
AppArmorによるuser namespace制限がある環境)で`No usable sandbox!`エラーが
頻発する。同梱の`scripts/puppeteer-config.json`(`{"args": ["--no-sandbox"]}`)
を`mmdc -p scripts/puppeteer-config.json`のように渡すことで回避できる
(セキュリティ上は非推奨だが、隔離されたCI環境では実質的に必須)。
`scripts/validate.sh`はこの設定ファイルを使った自動リトライを内蔵している。
Dockerでは`minlag/mermaid-cli`イメージの利用でも回避しやすい。
