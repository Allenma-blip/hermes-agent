"""codex_review — Codex 执行 + 审查子模块

由 feishu_codex.handle_codex_message 调用。
职责：执行 Codex CLI → 提取 git diff → 调用 codex review 评分。
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

CODEX_TIMEOUT = 300
CODEX_WORKDIR = os.path.expanduser("~/hermes-source")
REVIEW_SCRIPT = os.path.expanduser("~/.hermes/scripts/codex_review.py")
LANDING_SCRIPT = os.path.expanduser("~/.hermes/scripts/codex_landing.py")


async def run_review(
    project_name: str, description: str
) -> tuple[Path, Path, str, str, float | None]:
    """执行 Codex → 提取 diff → 评分

    Returns:
        (md_path, patch_path, status, result_msg, score)
    """
    prompt = (
        description[len("codex"):].strip()
        if description.startswith("codex")
        else description
    )

    # 1. 执行 Codex
    try:
        result = await asyncio.to_thread(
            _run_codex, prompt, CODEX_WORKDIR, CODEX_TIMEOUT
        )
    except asyncio.TimeoutError:
        return Path(), Path(), "failure", "❌ Codex 执行超时", None
    except Exception:
        logger.exception("Codex execution failed")
        return Path(), Path(), "failure", "❌ Codex 执行出错", None

    if result["exit_code"] != 0:
        return (
            Path(), Path(), "failure",
            f"❌ Codex 执行失败 (exit={result['exit_code']})", None,
        )

    # 2. 提取 diff
    md_path, patch_path = _extract_diff(CODEX_WORKDIR, project_name)
    if md_path is None:
        return Path(), Path(), "success", "✅ Codex 执行完成，无变更", None

    # 3. 评分
    score = _run_codex_review(md_path)
    if score is None:
        return (
            md_path, patch_path, "success",
            f"📝 变更已提取，自动评分失败，请手动审核\n审查文件: {md_path}",
            None,
        )

    # 4. 落地（≥9 自动 commit+push）
    if score >= 9:
        verdict = "pass"
    elif score >= 7:
        verdict = "warn"
    else:
        verdict = "fail"

    land_output = _run_landing(CODEX_WORKDIR, score, verdict)

    if verdict == "pass":
        result_msg = (
            f"✅ 审核通过 ({score}/10)，已自动提交并推送\n{land_output}"
        )
    elif verdict == "warn":
        result_msg = (
            f"⚠️ 审核通过 ({score}/10)，已自动提交\n"
            f"建议人工复查\n{land_output}"
        )
    else:
        result_msg = (
            f"❌ 审核不通过 ({score}/10)，不落地\n"
            f"审查报告: {md_path}\n完整 diff: {patch_path}"
        )

    return md_path, patch_path, "success", result_msg, score


def _run_codex(prompt: str, workdir: str, timeout: int) -> dict:
    cert = "/tmp/codex_proxy_cert.pem"
    proxy = "http://127.0.0.1:8443"
    env = os.environ.copy()
    env["SSL_CERT_FILE"] = cert
    env["HTTPS_PROXY"] = proxy

    proc = subprocess.run(
        ["codex", "exec", "-s", "danger-full-access", prompt],
        capture_output=True, text=True, timeout=timeout,
        cwd=workdir, env=env,
    )
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-500:],
    }


def _extract_diff(
    project_dir: str, project_name: str
) -> tuple[Path | None, Path | None]:
    result = subprocess.run(
        ["git", "-C", project_dir, "diff", "--stat"],
        capture_output=True, text=True, timeout=10,
    )
    if not result.stdout.strip():
        return None, None

    subprocess.run(
        ["python3", REVIEW_SCRIPT, project_dir],
        capture_output=True, timeout=15,
    )

    safe_name = "".join(c for c in project_name if c.isalnum() or c in "_-")
    md_path = Path(f"/tmp/codex_review_{safe_name}.md")
    patch_path = Path(f"/tmp/codex_full_diff_{safe_name}.patch")

    diff_result = subprocess.run(
        ["git", "-C", project_dir, "diff"],
        capture_output=True, text=True, timeout=10,
    )
    try:
        patch_path.write_text(diff_result.stdout)
    except OSError:
        logger.warning("Failed to write full diff patch: %s", patch_path)

    return (md_path if md_path.exists() else None), patch_path


def _run_codex_review(review_file: Path) -> float | None:
    cert = "/tmp/codex_proxy_cert.pem"
    proxy = "http://127.0.0.1:8443"
    env = os.environ.copy()
    env["SSL_CERT_FILE"] = cert
    env["HTTPS_PROXY"] = proxy

    try:
        content = review_file.read_text()
    except OSError:
        return None

    proc = subprocess.run(
        [
            "codex", "review",
            f"评分这段代码变更 (0-10分)，只输出数字分数。\n\n{content}"
        ],
        capture_output=True, text=True, timeout=180,
        cwd=CODEX_WORKDIR, env=env,
    )

    match = re.search(r"(\d+(?:\.\d+)?)", proc.stdout)
    if match:
        return float(match.group(1))
    return None


def _run_landing(project_dir: str, score: float, verdict: str) -> str:
    proc = subprocess.run(
        ["python3", LANDING_SCRIPT, project_dir, str(score), verdict],
        capture_output=True, text=True, timeout=30,
        cwd=project_dir,
    )
    return proc.stdout.strip() or proc.stderr.strip()