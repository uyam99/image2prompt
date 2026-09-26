import concurrent.futures
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from image2prompt import runtime
from image2prompt.ui import build_app


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.ready = self.root / "ready"
        logger = logging.getLogger("runtime-test")
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        self.logger_patch = patch.object(runtime, "LOGGER", logger)
        self.logger_patch.start()
        self.addCleanup(self.logger_patch.stop)

    def run_script(self, code, **kwargs):
        runtime.run_inference(
            [sys.executable, "-c", code],
            cwd=self.root,
            env=os.environ.copy(),
            ready_file=self.ready,
            **kwargs,
        )

    def test_failure_and_timeout_allow_next_run(self):
        with self.assertRaisesRegex(RuntimeError, "code=7"):
            self.run_script("raise SystemExit(7)")
        with self.assertRaisesRegex(TimeoutError, "準備"):
            self.run_script("import time; time.sleep(30)", setup_timeout=0.2)
        self.run_script("from pathlib import Path; Path('success').touch()")
        self.assertTrue((self.root / "success").exists())
        self.assertFalse(runtime._processes)

    @unittest.skipIf(os.name == "nt", "POSIX process-group regression")
    def test_generation_timeout_stops_grandchild(self):
        code = (
            "import subprocess,sys,time; from pathlib import Path; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            "Path('child').write_text(str(p.pid)); Path('ready').touch(); time.sleep(30)"
        )
        with self.assertRaisesRegex(TimeoutError, "画像解析"):
            self.run_script(code, setup_timeout=10, inference_timeout=0.2)
        pid = int((self.root / "child").read_text())
        state = subprocess.run(
            ["ps", "-p", str(pid), "-o", "stat="],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        self.assertTrue(not state or state.startswith("Z"), state)
        self.assertFalse(runtime._processes)

    def test_shutdown_interrupts_child_and_cleans_session(self):
        with (
            patch.object(runtime, "_closing", threading.Event()),
            patch.object(runtime, "SESSION") as session,
            concurrent.futures.ThreadPoolExecutor(1) as pool,
        ):
            future = pool.submit(
                self.run_script,
                "from pathlib import Path; import time; "
                "Path('ready').touch(); time.sleep(30)",
            )
            deadline = time.monotonic() + 10
            while not self.ready.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            try:
                self.assertTrue(self.ready.exists())
            finally:
                runtime.shutdown_runtime()
            with self.assertRaises(RuntimeError):
                future.result(timeout=10)
            session.cleanup.assert_called_once()
            self.assertFalse(runtime._processes)
            with self.assertRaisesRegex(RuntimeError, "終了"):
                self.run_script("pass")

    def test_rotating_log_and_analysis_diagnostics(self):
        logger = logging.getLogger("bounded-log-test")
        logger.handlers.clear()
        with (
            patch.object(runtime, "LOGGER", logger),
            patch.object(runtime, "data_dir", return_value=self.root),
        ):

            @runtime.record_analysis
            def example():
                raise ValueError("diagnostic failure")

            with self.assertRaises(ValueError):
                example()
            runtime.configure_logging()
            self.assertEqual(len(logger.handlers), 1)
            handler = logger.handlers[0]
            self.assertEqual(handler.backupCount, 3)
            self.assertEqual(handler.maxBytes, 2 * 1024 * 1024)
            handler.close()
        text = (self.root / "logs/image2prompt.log").read_text()
        self.assertIn("mode=example start", text)
        self.assertIn("diagnostic failure", text)
        self.assertIn("peak_rss_mib=", text)

    def test_both_modes_share_one_queue(self):
        app = build_app().queue(default_concurrency_limit=1)
        functions = [
            fn
            for fn in app.fns.values()
            if fn.name in ("run_analysis", "run_natural_analysis")
        ]
        self.assertEqual(len(functions), 2)
        self.assertEqual({fn.concurrency_id for fn in functions}, {"inference"})
        self.assertEqual({fn.concurrency_limit for fn in functions}, {1})


if __name__ == "__main__":
    unittest.main()
