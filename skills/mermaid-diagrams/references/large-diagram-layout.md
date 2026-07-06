# 大規模図の可読性・レイアウト制御

`mermaid-diagrams/SKILL.md` の詳細ガイド。図が育ってくると、自動レイアウトも
読み手の理解も破綻しやすくなる。

## ノード数の目安と分割

1図あたり12ノード程度を上限の目安にする。それを超える場合は、1図1関心事の
原則(ネットワーク/コンピュート/データを分ける等)に従って複数図に分割する。
architecture-beta公式ドキュメントも、少数サービスへの分割を設計指針として
推奨している。

分割の判断基準の例:

- レイヤーが異なる(インフラ層/アプリ層/データ層)→レイヤーごとに図を分ける
- 関心事が異なる(認証フロー/データフロー/デプロイ構成)→関心事ごとに図を分ける
- 1図に収めると`subgraph`が3階層以上ネストする→上位のsubgraphを別図に
  切り出す

## subgraphのdirectionに依存しない

`flowchart-guide.md`で詳述している通り、`subgraph`内の`direction`指定は
外部ノードとのリンクがあると無視される、TB/LRが逆転する等の複数の既知の
不安定挙動がある(#7477・#6438・#3096・#4648・#2789)。レイアウトの意図を
directionの指定だけに頼らず、ノードの記述順やsubgraphの分割そのもので
可読性を確保する。

## ELKレイアウトエンジン

大規模図ではdagre(デフォルト)よりELKが優れる場合がある。

```text
---
config:
  layout: elk
---
```

またはinit directive(`%%{init: {"flowchart": {"defaultRenderer": "elk"}}}%%`)
で指定する。`mergeEdges`、`nodePlacementStrategy`
(`BRANDES_KOEPF`/`SIMPLE`/`NETWORK_SIMPLEX`/`LINEAR_SEGMENTS`)を調整できる。

**ただし`@mermaid-js/layout-elk`パッケージの追加登録
(`mermaid.registerLayoutLoaders(elkLayouts)`)が必要**で、GitHub等の多くの
静的レンダラーでは標準で使えない。ELKはローカル/CIでSVGを生成する用途限定の
機能として扱う。ELK使用時はflowchartの`rankSpacing`/`nodeSpacing`の一部が
無視される点にも注意する。

## 判断を変える閾値

図が恒常的に12ノード超になる場合は、ELKレイアウトの導入(ローカル/CI限定)か、
図の分割を強制するルールをチームの規約に追加することを検討する。
