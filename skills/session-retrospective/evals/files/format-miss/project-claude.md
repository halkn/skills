# CLAUDE.md

## 開発

- lint は `shuck check .` と `shuck format --check .`。CI の `lint` ジョブも同じコマンドを実行する。
- 新しい shellscript を書いたら `shuck format <file>` で整形してからコミットする。
