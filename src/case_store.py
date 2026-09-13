from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import json


DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "cases.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def _load_cases() -> list[dict[str, Any]]:
    _ensure_storage()
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_cases(cases: list[dict[str, Any]]) -> None:
    _ensure_storage()
    DATA_FILE.write_text(
        json.dumps(cases, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _audit(case: dict[str, Any], action: str) -> None:
    case.setdefault("audit_log", []).append({"timestamp": _now(), "action": action})


def _next_case_id(cases: list[dict[str, Any]]) -> str:
    numbers: list[int] = []
    for case in cases:
        value = str(case.get("case_id", ""))
        if value.startswith("CASE-"):
            try:
                numbers.append(int(value.split("-", 1)[1]))
            except ValueError:
                pass
    return f"CASE-{max(numbers, default=1000) + 1}"


def create_case(student_name: str, student_id: str, complaint: str) -> dict[str, Any]:
    cases = _load_cases()
    now = _now()

    case = {
        "case_id": _next_case_id(cases),
        "student_name": student_name,
        "student_id": student_id,
        "complaint": complaint,
        "status": "New",
        "received_at": now,
        "created_at": now,
        "updated_at": now,

        # AI recommendations
        "ai_category": None,
        "ai_priority": None,
        "ai_department": None,
        "ai_priority_reason": None,
        "ai_uncertainty": None,
        "ai_multiple_issues": False,
        "ai_analysis_status": "pending",
        "ai_error": None,

        # Staff-confirmed data
        "final_category": None,
        "final_priority": None,
        "final_department": None,
        "case_status_detail": None,
        "resolution": "",
        "additional_info": "",

        # Response
        "ai_response_draft": "",
        "final_response": "",
        "response_approved": False,
        "approved_at": None,

        # Sending
        "sent": False,
        "sent_at": None,

        "audit_log": [],
    }

    _audit(case, "Case created")
    cases.append(case)
    _save_cases(cases)
    return case


def list_cases() -> list[dict[str, Any]]:
    return list(reversed(_load_cases()))


def get_case(case_id: str) -> dict[str, Any] | None:
    for case in _load_cases():
        if case.get("case_id") == case_id:
            return case
    return None


def update_case(case_id: str, **updates: Any) -> dict[str, Any]:
    cases = _load_cases()

    for case in cases:
        if case.get("case_id") != case_id:
            continue

        previous = dict(case)

        for key, value in updates.items():
            if value == "now" and key.endswith("_at"):
                value = _now()
            case[key] = value

        case["updated_at"] = _now()

        if any(key.startswith("ai_") for key in updates):
            if any(key in updates for key in {"ai_category", "ai_priority", "ai_department", "ai_analysis_status"}):
                _audit(case, "AI analysis updated")

        if any(key in updates for key in {"final_category", "final_priority", "final_department"}):
            _audit(case, "Staff case information updated")

        if any(key in updates for key in {"case_status_detail", "resolution", "additional_info"}):
            _audit(case, "Status/resolution information updated")

        if "ai_response_draft" in updates:
            _audit(case, "AI response draft generated")

        if "final_response" in updates:
            _audit(case, "Response edited/saved")

        if updates.get("response_approved") is True:
            _audit(case, "Response approved")

        if updates.get("sent") is True:
            _audit(case, "Case marked as sent")

        _save_cases(cases)
        return case

    raise KeyError(f"Case not found: {case_id}")
