# gh_pr_poller

GitHub CLIの`gh`コマンドを利用して、指定リポジトリのPRの新規作成・更新を定期的にポーリングで検出し、検出時に指定された実行ファイル・`.ps1`・`.py`を起動するPythonスクリプトです。

## 前提条件

- Windows または macOS
- Python 3.10以上
- [PowerShell Core 7+ (`pwsh`)](https://learn.microsoft.com/powershell/scripting/install/installing-powershell) [(Win)](https://learn.microsoft.com/ja-jp/powershell/scripting/install/install-powershell-on-windows?view=powershell-7.6) — `.ps1` を実行する場合
- [GitHub CLI (`gh`)](https://cli.github.com/) がインストール済みかつ認証済みであること

## 使い方

```
python gh_pr_poller.py <実行ファイルパス> --repo-dir <リポジトリフォルダパス> [--interval <秒>] [--repo <owner/repo>] [--recent <秒>] [--force]
```

### 引数

| 引数 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `実行ファイルパス` | ○ | — | PR検出時に実行する `.exe` / `.ps1` / `.py` のパス（相対パス or 絶対パス） |
| `--repo-dir` | ○ | — | 対象リポジトリのフォルダパス |
| `--interval` | — | `30` | ポーリング間隔（秒） |
| `--repo` | — | カレントディレクトリのリポジトリ | 対象リポジトリ（`owner/repo` 形式） |
| `--recent` | — | `300` | 起動時に「最近のPR」として実行対象とする閾値（秒） |
| `--force` | — | `無効` | 起動時に `state.json` 記録済みでも `--recent` 閾値内のPRを再実行する |

※ 相対パスはスクリプト自身の配置フォルダを基準に解決されます。

`.ps1` は `pwsh -File`、`.py` は現在の Python インタプリタでラップ実行されます。その他の拡張子はそのまま実行されます。

### 実行例

```bash
# 基本的な使い方
python gh_pr_poller.py ./on_pr_event.ps1 --repo-dir /path/to/repo

# ポーリング間隔を60秒に変更
python gh_pr_poller.py ./on_pr_event.ps1 --repo-dir /path/to/repo --interval 60

# リポジトリを明示的に指定
python gh_pr_poller.py ./on_pr_event.ps1 --repo-dir /path/to/repo --repo myorg/myrepo

# 起動時に直近10分以内のPRのみ対象にする
python gh_pr_poller.py ./on_pr_event.ps1 --repo-dir /path/to/repo --recent 600

# 起動時に記録済みPRも強制的に再実行する
python gh_pr_poller.py ./on_pr_event.ps1 --repo-dir /path/to/repo --force

# Windows / Mac 共通の起動ショートカット（同梱）
pwsh -File ./run_gh_pr_poller_slumbr-unity.ps1
pwsh -File ./run_gh_pr_poller_slumbr-unity_force.ps1
```

## 検出するイベント

| アクション | 条件 |
|---|---|
| `opened` | PRが新規作成された |
| `updated` | PRが更新された（コミットのpush、タイトル・本文の変更など） |

## 外部プログラムの呼び出し

イベント検出時、以下の形式で外部プログラムが実行されます。

```
<実行ファイルパス> <PR番号> <アクション> <リポジトリフォルダパス>
```

例:

```
./on_pr_event.ps1 42 opened /path/to/repo
./on_pr_event.ps1 15 updated /path/to/repo
```

## 起動時の挙動

起動直後の初回ポーリングでは、`--recent` 秒以内のイベントのみ外部プログラムを実行します。これにより、スクリプトが停止していた間に発生した最近のPRイベントをキャッチアップできます。

ただし、前回の実行で `state.json` に記録済みのPRは、デフォルトでは `updatedAt` が変化していない限りスキップされます。`--force` を指定すると、記録済みのPRでも `--recent` 閾値内であれば再実行されます。

2回目以降のポーリングでは閾値チェックは行わず、前回との差分のみで検出します（`--force` は初回ポーリングのみ影響します）。

## 終了方法

`Ctrl+C` でグレースフルに終了します。
