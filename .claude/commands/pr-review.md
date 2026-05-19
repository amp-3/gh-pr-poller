---
allowed-tools: Bash(gh:*)
argument-hint: <PR番号>
description: PRをレビューしてコメントを投稿する
---

Review the PR: $ARGUMENTS

あなたはプルリクエストのレビューを支援するAIです。
このタスクは非常に高レベルなスキルが要求されるので、 ultrathink するようにしてください。

## コンテキスト

### PR情報
!`gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`

### 変更ファイル一覧
!`gh pr diff $ARGUMENTS --name-only`

### 変更差分
!`gh pr diff $ARGUMENTS`

## タスク

プルリクエストの内容を分析し、以下の観点からコメントを作成してください：

1. 品質
2. セキュリティ
3. パフォーマンス
4. テスト
5. ドキュメント

分析結果を以下のフォーマットでMarkdownコードブロック内に出力してください。
最後に、生成したレビュー本文を一時ファイルに書き出してから `gh pr comment $ARGUMENTS --body-file <一時ファイル>` でPRにコメント投稿してください。

```markdown
## コードレビュー: [PR タイトル]

### 📋 PRの概要

[このPRの目的と実装内容を2-3文で簡潔に説明]

### このPRの背景知識として抑えておくべきコードの知識

[このPRを理解するために必要なコードの知識や背景情報]

### 人間が重点的にチェックする場所

- [人間がチェックすべきポイント1（ファイルのパスも含めて）]
- [人間がチェックすべきポイント2（ファイルのパスも含めて）]

### 分かりづらい箇所の解説

- [分かりづらい箇所1の説明(ファイルのパスも含めて)]
- [分かりづらい箇所2の説明(ファイルのパスも含めて)]

### その他のコメント

[全体的なフィードバック]

フィードバックのタイプ：
- POSITIVE: 良い点や成功している部分を強調する場合
- IMPROVEMENT: 具体的な改善が必要な点がある場合  
- SUGGESTION: 新しいアイデアや提案を提供する場合

### PRのリンク

[PRのリンク](PRのURL)