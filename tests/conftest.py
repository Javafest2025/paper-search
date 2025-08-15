import os
import sys
import json
import time
from typing import Dict, Any
from dotenv import load_dotenv


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _add_project_root_to_syspath():
    # tests/ -> project root containing the `app` package
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)


_add_project_root_to_syspath()


def pytest_sessionstart(session):
    # Initialize global report collector
    session.config._api_report: Dict[str, Any] = {"start_ts": int(time.time()), "clients": {}}
    # Load .env so tests can read UNPAYWALL_EMAIL, CORE_API_KEY, etc.
    env_path = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)


def pytest_sessionfinish(session, exitstatus):
    # Write report at end of session
    report: Dict[str, Any] = session.config._api_report  # type: ignore[attr-defined]
    report["end_ts"] = int(time.time())
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "academic_api_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


