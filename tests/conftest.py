import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_skipped = 0


def pytest_runtest_logreport(report):
    global _skipped
    if report.skipped:
        _skipped += 1


def pytest_sessionfinish(session, exitstatus):
    # Tripwire (T10): an empty or partially skipped run is a failed run.
    if session.testscollected == 0:
        print("\nTRIPWIRE: 0 tests collected")
        session.exitstatus = 1
    elif _skipped:
        print(f"\nTRIPWIRE: {_skipped} skipped test(s); skips are not allowed")
        session.exitstatus = 1


@pytest.fixture(scope="session")
def build():
    return subprocess.run(["pnpm", "build"], cwd=ROOT, capture_output=True, text=True)


@pytest.fixture(scope="session")
def dist(build):
    return ROOT / "dist"
