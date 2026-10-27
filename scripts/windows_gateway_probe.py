"""Run the unchanged Windows gateway lifecycle test in fresh pytest processes."""

import json
import platform
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    if sys.platform != "win32":
        raise RuntimeError("This probe requires native Windows")
    root = Path(__file__).resolve().parents[1]
    output = root / ".diagnostics/windows-startup"
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for index in range(2):
        started = time.monotonic()
        run = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/gateway/test_windows_shutdown.py"
             "::test_windowless_gateway_stop_runs_application_cleanup",
             "-q", "--durations=0", f"--basetemp={output / f'tmp-{index}'}",
             f"--junitxml={output / f'junit-{index}.xml'}"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=150,
        )
        (output / f"pytest-{index}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        results.append({"run": index, "exit_code": run.returncode,
                        "seconds": round(time.monotonic() - started, 3)})
        print(json.dumps(results[-1]), flush=True)
        print(run.stdout[-5000:], flush=True)
    report = {"platform": platform.platform(), "python": sys.version, "runs": results}
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return int(any(result["exit_code"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
