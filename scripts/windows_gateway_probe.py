"""Compare unchanged Windows gateway lifecycle tests under concurrent startup."""

import json
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".diagnostics/windows-startup"
CASE = ("tests/gateway/test_windows_shutdown.py"
        "::test_windowless_gateway_stop_runs_application_cleanup")


def probe(name: str) -> dict:
    started = time.monotonic()
    try:
        run = subprocess.run(
            [sys.executable, "-m", "pytest", CASE, "-q", "--durations=0",
             f"--basetemp={OUTPUT / name}", f"--junitxml={OUTPUT / (name + '.xml')}"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=150,
        )
        log, code = run.stdout + run.stderr, run.returncode
    except subprocess.TimeoutExpired as error:
        log = repr(error)
        code = 124
    (OUTPUT / f"{name}.log").write_text(log, encoding="utf-8")
    result = {"run": name, "exit_code": code,
              "seconds": round(time.monotonic() - started, 3)}
    print(json.dumps(result), flush=True)
    if code:
        print(log[-8000:], flush=True)
    return result


def main() -> int:
    if sys.platform != "win32":
        raise RuntimeError("This probe requires native Windows")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    for stage, concurrency in enumerate((1, 3, 6, 1)):
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            names = [f"stage-{stage}-parallel-{concurrency}-run-{i}" for i in range(concurrency)]
            results.extend(executor.map(probe, names))
        report = {"platform": platform.platform(), "python": sys.version, "runs": results}
        (OUTPUT / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return int(any(result["exit_code"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
