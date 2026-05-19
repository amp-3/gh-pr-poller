#!/usr/bin/env python3
"""on_pr_event - claude_code_pr_summary.ps1 と claude_code_pr_review.ps1 を並行実行する"""

import os
import subprocess
import sys
import threading
from datetime import datetime

from beep import play_completion_beep_high

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def run_task(script_name, args, label, results, lock):
    """スクリプト (.ps1 など) を実行し、完了時に出力を表示"""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if script_name.endswith(".ps1"):
        cmd = ["pwsh", "-NoProfile", "-File", script_path] + args
    else:
        cmd = [script_path] + args
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace"
    )
    output_lines = []
    for line in proc.stdout:
        output_lines.append(line)
    proc.wait()

    with lock:
        log(f"[on_pr_event] {label} 完了 (終了コード: {proc.returncode})")
        for line in output_lines:
            print(f"  [{label}] {line}", end="", flush=True)

    results[label] = proc.returncode


def main():
    if len(sys.argv) < 4:
        print("Usage: on_pr_event.py <pr_number> <action> <repo_dir>")
        sys.exit(1)

    pr_number, action, repo_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    args = [pr_number, action, repo_dir]

    log(f"[on_pr_event] PR #{pr_number} アクション: {action} リポジトリ: {repo_dir}")
    log("[on_pr_event] claude_code_pr_summary.ps1 と claude_code_pr_review.ps1 を並行実行します...")

    results = {}
    lock = threading.Lock()

    tasks = [
        ("claude_code_pr_summary.ps1", "pr-summary"),
        ("claude_code_pr_review.ps1", "pr-review"),
    ]

    threads = []
    for script_name, label in tasks:
        t = threading.Thread(
            target=run_task, args=(script_name, args, label, results, lock)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    log("[on_pr_event] 全タスク完了")
    play_completion_beep_high()


if __name__ == "__main__":
    main()
