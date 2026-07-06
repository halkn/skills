# データ基盤アーキテクチャレビュー: {対象}

- レビュー日: {YYYY-MM-DD}
- レビュー観点: references/review-lens.md(WAF 5柱+チームスキル適合性)
- 対象資料: {設計書・図・リポジトリ等}

## スコアカード

| 観点 | 評価 | サマリ(1行) |
|---|---|---|
| Security and governance | {✅/⚠️/❌} | |
| Operational excellence | | |
| Reliability | | |
| Performance optimization | | |
| Cost optimization | | |
| チームスキル適合性 | | |

評価基準: ✅ 懸念なし / ⚠️ 条件付き・要改善 / ❌ 重大な欠陥

## 指摘事項({N}件: CRITICAL {n} / HIGH {n} / MEDIUM {n} / LOW {n})

<!-- Severity順に記載する。Severityの目安:
CRITICAL = データ喪失・重大なセキュリティ欠陥・修正不能な構造問題
HIGH = 本番運用で高確率で顕在化する問題
MEDIUM = 効率・保守性を損なうが回避運用が可能
LOW = 改善提案・軽微な指摘 -->

### [{SEVERITY}] {観点}: {指摘タイトル}

- **Finding**: {何が問題か。設計書の該当箇所を引用する}
- **Impact**: {放置するとどうなるか}
- **Recommendation**: {どう直すか}
- **Effort**: {S / M / L / XL}

## 良い点(Strengths)

<!-- 必ず記載する。指摘を和らげるためではなく、維持すべき決定を明確にするため。 -->

- {維持すべき決定とその理由}

## 総合判定

- [ ] 承認
- [ ] 条件付き承認 — 条件: {マージ/承認までに満たすべき条件}
- [ ] 差し戻し — ブロッカー: {再設計が必要な理由}
