#!/usr/bin/env python3
"""GitHub PR Poller - PRの新規作成・更新を定期的にポーリングで検出し、外部プログラムを実行する"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "state.json")

running = True


def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")


def signal_handler(_signum, _frame):
    global running
    log("終了シグナルを受信しました。終了します...")
    running = False


def check_gh_installed():
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        log("エラー: gh コマンドが見つかりません。GitHub CLI をインストールしてください。")
        sys.exit(1)


def resolve_executable_path(path_arg):
    if os.path.isabs(path_arg):
        exe_path = path_arg
    else:
        exe_path = os.path.join(SCRIPT_DIR, path_arg)
    exe_path = os.path.normpath(exe_path)
    if not os.path.exists(exe_path):
        log(f"エラー: 実行ファイルが見つかりません: {exe_path}")
        sys.exit(1)
    return exe_path


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"prs": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"警告: state.json の読み込みに失敗しました ({e})。空の状態で再初期化します。")
        return {"prs": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def fetch_prs(repo):
    cmd = ["gh", "pr", "list", "--state", "open",
           "--assignee", "@me",
           "--json", "number,updatedAt,createdAt,headRefOid"]
    if repo:
        cmd.extend(["--repo", repo])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        log(f"エラー: gh pr list の実行に失敗しました: {e.stderr.strip()}")
        return None
    except json.JSONDecodeError as e:
        log(f"エラー: gh pr list の出力をパースできませんでした: {e}")
        return None


def run_external(exe_path, pr_number, action, repo_dir):
    ext = os.path.splitext(exe_path)[1].lower()
    if ext == ".ps1":
        cmd = ["pwsh", "-NoProfile", "-File", exe_path, str(pr_number), action, repo_dir]
    elif ext == ".py":
        cmd = [sys.executable, exe_path, str(pr_number), action, repo_dir]
    else:
        cmd = [exe_path, str(pr_number), action, repo_dir]
    log(f"  実行: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
        log(f"  終了コード: {result.returncode}")
    except Exception as e:
        log(f"  エラー: 外部プログラムの実行に失敗しました: {e}")


def parse_iso_datetime(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def detect_events(prev_state, current_prs, is_first_poll, recent_seconds, force=False):
    now = datetime.now(timezone.utc)
    events = []

    for pr in current_prs:
        pr_number = str(pr["number"])
        pr_updated_at = pr["updatedAt"]
        pr_created_at = pr["createdAt"]

        if pr_number not in prev_state["prs"]:
            # 新しいPR
            if is_first_poll:
                created_dt = parse_iso_datetime(pr_created_at)
                updated_dt = parse_iso_datetime(pr_updated_at)
                created_age = (now - created_dt).total_seconds()
                updated_age = (now - updated_dt).total_seconds()

                if created_age <= recent_seconds:
                    events.append((pr["number"], "opened"))
                elif updated_age <= recent_seconds:
                    events.append((pr["number"], "updated"))
            else:
                events.append((pr["number"], "opened"))
        else:
            # 既知のPR — headRefOid（コミットSHA）が変わっているか確認
            prev_head_oid = prev_state["prs"][pr_number].get("head_ref_oid")
            current_head_oid = pr["headRefOid"]

            if prev_head_oid == current_head_oid:
                # コミット変更なし（コメント追加等） → スキップ
                continue

            prev_updated = prev_state["prs"][pr_number]["updated_at"]
            if is_first_poll and force:
                updated_dt = parse_iso_datetime(pr_updated_at)
                updated_age = (now - updated_dt).total_seconds()
                if updated_age <= recent_seconds:
                    events.append((pr["number"], "updated"))
            elif pr_updated_at != prev_updated:
                if is_first_poll:
                    updated_dt = parse_iso_datetime(pr_updated_at)
                    updated_age = (now - updated_dt).total_seconds()
                    if updated_age <= recent_seconds:
                        events.append((pr["number"], "updated"))
                else:
                    events.append((pr["number"], "updated"))

    return events


def build_new_state(current_prs):
    new_state = {"prs": {}}
    for pr in current_prs:
        new_state["prs"][str(pr["number"])] = {
            "updated_at": pr["updatedAt"],
            "head_ref_oid": pr["headRefOid"]
        }
    return new_state


def main():
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="GitHub PR Poller")
    parser.add_argument("executable", help="PR検出時に実行する実行ファイル・.ps1・.pyのパス")
    parser.add_argument("--interval", type=int, default=30, help="ポーリング間隔（秒）。デフォルト: 30")
    parser.add_argument("--repo", type=str, default=None, help="対象リポジトリ（owner/repo形式）")
    parser.add_argument("--recent", type=int, default=300, help="起動時に最近のPRとする閾値（秒）。デフォルト: 300")
    parser.add_argument("--repo-dir", type=str, required=True,
                        help="対象リポジトリのフォルダパス")
    parser.add_argument("--force", action="store_true", default=False,
                        help="起動時にstate.json記録済みでもrecent閾値内のPRを再実行する")
    args = parser.parse_args()

    check_gh_installed()
    exe_path = resolve_executable_path(args.executable)

    repo_display = args.repo if args.repo else "(カレントディレクトリのリポジトリ)"
    log(f"対象リポジトリ: {repo_display}")
    log(f"ポーリング間隔: {args.interval}秒")
    log(f"実行ファイル: {exe_path}")
    log(f"起動時閾値: {args.recent}秒")
    log(f"リポジトリフォルダ: {args.repo_dir}")
    log(f"強制再実行: {'有効' if args.force else '無効'}")
    log("ポーリングを開始します... (Ctrl+C で終了)")

    prev_state = load_state()
    is_first_poll = True

    while running:
        prs = fetch_prs(args.repo)
        if prs is not None:
            log(f"取得したPR数: {len(prs)}")

            events = detect_events(prev_state, prs, is_first_poll, args.recent, force=args.force)

            for pr_number, action in events:
                log(f"イベント検出: PR #{pr_number} - {action}")
                run_external(exe_path, pr_number, action, args.repo_dir)

            # 外部コマンドがPRを更新した可能性があるため再取得
            if events:
                refreshed = fetch_prs(args.repo)
                if refreshed is not None:
                    prs = refreshed

            prev_state = build_new_state(prs)
            save_state(prev_state)
            is_first_poll = False

        # インターバル待機（1秒刻みでrunningフラグをチェック）
        for _ in range(args.interval):
            if not running:
                break
            time.sleep(1)

    log("終了しました。")


if __name__ == "__main__":
    main()
