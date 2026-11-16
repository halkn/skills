# Azure DevOps（`az repos`）

Azure Repos（`dev.azure.com`・`*.visualstudio.com`）での `az repos` 固有の手順。共通のフロー・コミット規約は `SKILL.md` を参照。

## 前提

- `az repos` は Azure CLI の拡張 `azure-devops` のコマンド。`az extension show --name azure-devops` で入っているかを見る。入っていなければ自分で入れず、ユーザーに `az extension add --name azure-devops` の実行を頼む
  - 理由: 依存の取得はユーザーの環境を変える。拡張が無いまま `az repos` を打つと、環境によってはインストールの確認プロンプトで止まる
- 認証のエラーが出たら、ユーザーに `az login` を頼む
- organization と project は、作業ディレクトリの git のリモートから自動で検出される。作業ディレクトリと別のリポジトリが対象のときは、`az repos pr create` に `--org <URL>`・`--project <名前>`・`--repository <名前>` を付ける。PR の ID は organization の中で一意なので、`show`・`update`・`policy`・`work-item` は `--id` と（必要なら）`--org` で足りる
- 出力を絞るときは `--query <JMESPath>` と `--output tsv`（`-o tsv`）を使う

## PR テンプレート

PR を作る前に、既定ブランチにテンプレートがあるか確認する。Azure Repos が使うのは既定ブランチのテンプレートだけなので、作業ツリーではなく既定ブランチ側を見る。

```bash
git ls-tree -r --name-only origin/HEAD | grep -i pull_request_template
```

Azure Repos が認識するのは、`.azuredevops/`・`.vsts/`・`docs/`・リポジトリルートのいずれかに置かれたファイルで、ファイル名とフォルダ名の大文字小文字は区別されない。フォルダはこの順に探され、最初に見つかったものが使われる。

- `pull_request_template.md` / `pull_request_template.txt` — 既定のテンプレート
- `pull_request_template/branches/<対象ブランチ名>.md`（`.txt`）— 対象ブランチ専用。あれば既定のテンプレートより優先される
- `pull_request_template/` 直下のその他の `.md` / `.txt` — 作成者が選んで追記する追加のテンプレート。変更内容に合うものがあれば足し、判断が付かなければユーザーに聞く

本文は `--description` で明示して渡す。テンプレートの中身を読み、埋めたものを自分でファイルに書いて渡す。

## PR 作成

```bash
az repos pr create --title "<title>" --description "@<本文ファイル>" --source-branch <branch> --target-branch <branch>
```

- `--source-branch` は作業ブランチを明示する。`--target-branch` は省略するとリポジトリの既定ブランチ。既定ブランチ以外へ向けるときだけ明示する
- 本文はファイルに書き、Azure CLI の `@<file>` の形で `--description` に渡す。`--description` に文字列を直接渡すと、値ごとに 1 行になり、改行やバッククォートのエスケープで壊れやすい
  - 本文ファイルの置き場所・ファイル名・作り方は、`references/github.md` の「PR 作成」の本文ファイルの規則と同じにする
  - `@` の後ろのファイルが読めないと、Azure CLI はエラーにせず `@<本文ファイル>` という文字列をそのまま本文にする。作成後の読み返しで必ず確かめる
- `--description` を省くと、コミットが 1 つの PR ではそのコミットメッセージが本文になる。テンプレートの有無にかかわらず本文は明示する
- work item を紐付けるときは `--work-items <ID> <ID>` を付ける（下記「work item の紐付け」）
- 途中段階なら `--draft true`
- 作成時に完了オプション（`--auto-complete`・`--squash`・`--delete-source-branch`・`--transition-work-items`・`--bypass-policy`）を付けない。これらはマージの時点で決める（下記「マージ」）
- 作成後に `az repos pr show --id <ID> --query description -o tsv` で読み返し、意図した本文になっているか確かめる
- 作成後に PR の ID と URL（`<repository.webUrl>/pullrequest/<ID>`）を報告する。ID は作成時の出力の `pullRequestId`、`repository.webUrl` も同じ出力にある。`--open` でブラウザを開かない（ヘッドレス環境で止まる）

本文を変えるときは `az repos pr update --id <ID> --description "@<本文ファイル>"` に同じ規則を適用する。

## work item の紐付け

- PR の作成時は `--work-items <ID>`、作成後は `az repos pr work-item add --id <PR の ID> --work-items <ID>` で紐付ける。紐付いているものは `az repos pr work-item list --id <PR の ID>` で見る
- コミットメッセージに `#<ID>` を書くと、push した時点でそのコミットと work item `<ID>` が紐付く。GitHub の issue 番号のつもりで `#123` を書かない。別の work item に紐付いて履歴に残る
- 紐付けだけでは work item の状態は変わらない。マージと同時に work item を次の状態（例: Active → Resolved）に進めるのは `--transition-work-items true` で、work item の完了を指示されたときだけ付ける

## マージ

Azure Repos ではマージを「PR の完了（complete）」と呼ぶ。`az repos pr update` で状態を `completed` にする。

```bash
az repos pr policy list --id <ID> --output table
az repos pr show --id <ID> --query completionOptions
az repos pr update --id <ID> --status completed --squash false --delete-source-branch false --transition-work-items false
az repos pr show --id <ID> --query status -o tsv
```

- マージ前に `az repos pr policy list` でブランチポリシー（ビルド・レビュアー数・work item の紐付けなど）の評価を見る。`Blocking` が `True` で `Status` が `Approved` でないものがあればマージせず報告する
- マージ方式は `--squash` で明示する。`--squash false` は履歴を保持する通常の merge（Merge (no fast forward)）、`--squash true` は squash merge
  - `az repos pr update` は、指定しなかった完了オプションに PR に既に保存されている値を使う。Web UI や他の人が設定した値（squash・ソースブランチの削除・work item の遷移）がそのまま効くので、3 つとも毎回値を明示する
  - PR に `completionOptions.mergeStrategy` が保存されていると、`--squash` は無視されてそちらの方式でマージされる。`az repos pr` からは `mergeStrategy` を変えられないので、値が意図した方式（`noFastForward` / `squash`）と違えばマージせずユーザーに伝える
  - `az repos pr` から選べるのは merge と squash だけ。リポジトリの方針やブランチポリシーが rebase（Rebase and fast-forward・Semi-linear merge）を求めるときは、別の手段を探さずユーザーに伝える
- ソースブランチの削除は `--delete-source-branch true`、work item の遷移は `--transition-work-items true` で、どちらも指示されたときだけ付ける
- `--bypass-policy` はブランチポリシーを迂回する。ユーザーが明示的に指示した場合だけ使う
- `--auto-complete true` は、ポリシーが揃った時点での自動マージの予約になる。即時マージのつもりで使わない
- マージ後に `az repos pr show` の `status` が `completed` になったことを確かめる。`active` のままなら、`--query mergeStatus` の値（`queued` はマージ処理中。`conflicts`・`rejectedByPolicy`・`failure` は失敗）を添えて報告する

## その他

- PR の一覧は `az repos pr list --source-branch <branch> --status active`
- レビューの投票は `az repos pr set-vote --id <ID> --vote <値>`。投票はユーザーの判断なので、指示されたときだけ行う

## 確認プロンプトが出た場合

環境によっては `az repos pr create` や `az repos pr update` に hook や permission 設定が掛かっており、対象リポジトリによって確認プロンプトが出る。これは想定された動作なので、フラグを変える・別コマンドで代替するといった回避を試みず、ユーザーの判断を待つ。
