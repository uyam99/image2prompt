"""Bounded diagnostics and lifetime management for the local app."""

from __future__ import annotations

import atexit
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path

SESSION = tempfile.TemporaryDirectory(prefix="image2prompt-session-")
SESSION_PATH = Path(SESSION.name)
os.environ.setdefault("GRADIO_TEMP_DIR", str(SESSION_PATH / "gradio"))
LOGGER = logging.getLogger("image2prompt")
_state_lock = threading.Lock()
# ponytail: one local inference at a time; split locks only for multiple workers.
_analysis_lock = threading.Lock()
_closing = threading.Event()
_processes: set[subprocess.Popen] = set()


def data_dir() -> Path:
    override = os.environ.get("IMAGE2PROMPT_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        return (
            Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
            / "image2prompt"
        )
    return Path.home() / "Library/Application Support/image2prompt"


def configure_logging() -> None:
    with _state_lock:
        if LOGGER.handlers:
            return
        folder = data_dir() / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            folder / "image2prompt.log",
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        LOGGER.addHandler(handler)
        LOGGER.setLevel(logging.INFO)
        LOGGER.propagate = False
        LOGGER.info("runtime=2026-09-06 pid=%s session=%s", os.getpid(), SESSION_PATH)


def _peak_rss_mib() -> float | None:
    if sys.platform == "win32":
        return None
    import resource

    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / divisor, 1)


def record_analysis(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        configure_logging()
        with _analysis_lock:
            if _closing.is_set():
                raise RuntimeError("アプリを終了しています。")
            request_id = uuid.uuid4().hex[:8]
            started = time.monotonic()
            LOGGER.info(
                "id=%s mode=%s start peak_rss_mib=%s",
                request_id,
                fn.__name__,
                _peak_rss_mib(),
            )
            try:
                return fn(*args, **kwargs)
            except Exception:
                LOGGER.exception("id=%s mode=%s failed", request_id, fn.__name__)
                raise
            finally:
                LOGGER.info(
                    "id=%s mode=%s end seconds=%.2f peak_rss_mib=%s",
                    request_id,
                    fn.__name__,
                    time.monotonic() - started,
                    _peak_rss_mib(),
                )

    return run


def _stop_process(process: subprocess.Popen) -> None:
    with _state_lock:
        if process not in _processes:
            return
        _processes.remove(process)
        if os.name == "nt":
            if process.poll() is None:
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=10)


def run_inference(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    ready_file: Path,
    setup_timeout: float = 3600,
    inference_timeout: float = 600,
) -> None:
    """Keep setup and generation deadlines separate; always reap our process tree."""
    configure_logging()
    with tempfile.TemporaryFile() as output:
        with _state_lock:
            if _closing.is_set():
                raise RuntimeError("アプリを終了しています。")
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=os.name != "nt",
            )
            _processes.add(process)
        LOGGER.info("child=%s started", process.pid)
        deadline = time.monotonic() + setup_timeout
        ready = False
        try:
            while True:
                if not ready and ready_file.is_file():
                    ready = True
                    deadline = time.monotonic() + inference_timeout
                    LOGGER.info("child=%s model_ready", process.pid)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    stage = "画像解析" if ready else "推論環境・モデルの準備"
                    raise TimeoutError(
                        f"{stage}が制限時間を超えました。もう一度実行してください。"
                    )
                try:
                    code = process.wait(timeout=min(1, remaining))
                    break
                except subprocess.TimeoutExpired:
                    pass
            if code:
                output.seek(max(0, output.seek(0, 2) - 65536))
                details = output.read().decode("utf-8", errors="replace").strip()
                LOGGER.error("child=%s exit=%s details=%s", process.pid, code, details)
                raise RuntimeError(
                    f"推論処理が終了しました（code={code}）。{details[-1200:]}"
                )
        finally:
            _stop_process(process)
            LOGGER.info("child=%s reaped exit=%s", process.pid, process.returncode)


def shutdown_runtime() -> None:
    _closing.set()
    with _state_lock:
        processes = list(_processes)
    for process in processes:
        _stop_process(process)
    with _analysis_lock:
        SESSION.cleanup()
    LOGGER.info("runtime stopped")


atexit.register(shutdown_runtime)
