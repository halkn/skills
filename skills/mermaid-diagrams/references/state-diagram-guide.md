# stateDiagram-v2 の書き方

`mermaid-diagrams/SKILL.md` の詳細ガイド。状態遷移・ライフサイクルの表現に
使う図種。安定しているが、システム構成図には不向き。

## 基本構文

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Processing : start
    Processing --> Completed : success
    Processing --> Failed : error
    Completed --> [*]
    Failed --> [*]
```

`[*]`は開始/終了の擬似状態を表す。

## 複合状態(ネスト)

```mermaid
stateDiagram-v2
    [*] --> Active
    state Active {
        [*] --> Idle
        Idle --> Running : trigger
        Running --> Idle : done
    }
    Active --> [*] : cancel
```

## 分岐(choice)・並行(fork/join)

```mermaid
stateDiagram-v2
    state check <<choice>>
    [*] --> check
    check --> Approved : valid
    check --> Rejected : invalid
```

`<<choice>>`で条件分岐、`<<fork>>`/`<<join>>`で並行処理の分岐・合流を表現する。

## 構文の落とし穴

状態名に`end`を単独で使うと予約語衝突の対象になり得るため、SKILL.md本体の
チェックリスト通り大文字化した名前を使う。遷移ラベル(`:`以降のテキスト)に
`()`・`,`・`{}`を含む場合はダブルクォートで囲む。
