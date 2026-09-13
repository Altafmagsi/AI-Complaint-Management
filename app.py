import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_service import analyze_complaint, draft_response
from case_store import create_case, get_case, list_cases, update_case
st.set_page_config(
    page_title="University Complaint Assistant",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 University Student Complaint Assistant")
st.caption("AI recommends. Staff decides.")

if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = None


def open_case(case_id: str) -> None:
    st.session_state.current_case_id = case_id


with st.sidebar:
    st.header("Navigation")

    if st.button("➕ New Complaint", use_container_width=True):
        st.session_state.current_case_id = None
        st.rerun()

    st.divider()
    st.subheader("Existing Cases")

    cases = list_cases()
    if not cases:
        st.caption("No cases yet.")
    else:
        for case in cases:
            category = case.get("final_category") or case.get("ai_category") or "Unclassified"
            label = f"{case['case_id']} · {category}"
            if st.button(label, key=f"open_{case['case_id']}", use_container_width=True):
                open_case(case["case_id"])
                st.rerun()


# New complaint
if st.session_state.current_case_id is None:
    st.subheader("New Complaint")

    student_name = st.text_input("Student Name (optional)")
    student_id = st.text_input("Student ID (optional)")
    complaint = st.text_area(
        "Student Complaint *",
        height=220,
        placeholder="Paste the student's complaint here...",
    )

    if st.button("🔎 Analyze Complaint", type="primary"):
        if not complaint.strip():
            st.error("Please enter the student's complaint.")
            st.stop()

        case = create_case(
            student_name=student_name.strip(),
            student_id=student_id.strip(),
            complaint=complaint.strip(),
        )

        with st.spinner("Analyzing complaint..."):
            result = analyze_complaint(complaint)

        if result["success"]:
            data = result["data"]
            update_case(
                case["case_id"],
                ai_category=data.get("category"),
                ai_priority=data.get("priority"),
                ai_department=data.get("department"),
                ai_priority_reason=data.get("priority_rationale"),
                ai_uncertainty=data.get("uncertainty"),
                ai_multiple_issues=bool(data.get("multiple_issues", False)),
                ai_analysis_status="complete",
                status="Review",
            )
        else:
            update_case(
                case["case_id"],
                ai_analysis_status="failed",
                ai_error=result["error"],
                status="Manual Processing",
            )

        st.session_state.current_case_id = case["case_id"]
        st.rerun()

# Existing case
else:
    case = get_case(st.session_state.current_case_id)
    if case is None:
        st.session_state.current_case_id = None
        st.rerun()

    st.subheader(f"Case {case['case_id']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", case["status"])
    col2.metric(
        "Category",
        case["final_category"] or case["ai_category"] or "Needs Review",
    )
    col3.metric(
        "Priority",
        case["final_priority"] or case["ai_priority"] or "Needs Review",
    )

    st.divider()

    st.markdown("### Original Complaint")
    st.info(case["complaint"])

    st.markdown("### AI Recommendations")

    if case["ai_analysis_status"] == "failed":
        st.error("AI analysis is currently unavailable.")
        if case.get("ai_error"):
            st.caption(f"Details: {case['ai_error']}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Retry AI Analysis", type="primary"):
                with st.spinner("Retrying AI analysis..."):
                    result = analyze_complaint(case["complaint"])
                if result["success"]:
                    data = result["data"]
                    update_case(
                        case["case_id"],
                        ai_category=data.get("category"),
                        ai_priority=data.get("priority"),
                        ai_department=data.get("department"),
                        ai_priority_reason=data.get("priority_rationale"),
                        ai_uncertainty=data.get("uncertainty"),
                        ai_multiple_issues=bool(data.get("multiple_issues", False)),
                        ai_analysis_status="complete",
                        ai_error=None,
                        status="Review",
                    )
                else:
                    update_case(case["case_id"], ai_error=result["error"])
                st.rerun()
        with c2:
            if st.button("➡️ Continue Manually"):
                update_case(case["case_id"], status="Manual Processing")
                st.rerun()
    else:
        st.write(f"**Category:** {case['ai_category'] or 'Needs Review'}")
        st.write(f"**Priority:** {case['ai_priority'] or 'Needs Review'}")
        if case["ai_priority_reason"]:
            st.write(f"**Priority reason:** {case['ai_priority_reason']}")
        st.write(f"**Department:** {case['ai_department'] or 'Needs Review'}")
        st.write(f"**Uncertainty:** {case['ai_uncertainty'] or 'Not available'}")

        if case["ai_multiple_issues"]:
            st.warning("Multiple issues may be present. Review carefully.")
        if case["ai_priority"] == "Urgent":
            st.error("⚠️ Potentially urgent complaint — human review required.")

    st.divider()
    st.markdown("### Human Review")

    categories = [
        "Finance",
        "Registration",
        "Examinations",
        "Academic",
        "IT",
        "Hostel",
        "Facilities",
        "Student Affairs",
        "Other / Needs Review",
    ]
    priorities = ["Normal", "High", "Urgent", "Needs Review"]
    departments = [
        "Accounts / Finance",
        "Registrar / Registration",
        "Examinations",
        "Academic Department",
        "IT",
        "Hostel Administration",
        "Facilities",
        "Student Affairs",
        "Other / Needs Review",
    ]

    current_category = case["final_category"] or case["ai_category"]
    current_priority = case["final_priority"] or case["ai_priority"]
    current_department = case["final_department"] or case["ai_department"]

    category_index = categories.index(current_category) if current_category in categories else len(categories) - 1
    priority_index = priorities.index(current_priority) if current_priority in priorities else len(priorities) - 1
    department_index = departments.index(current_department) if current_department in departments else len(departments) - 1

    selected_category = st.selectbox("Final Category", categories, index=category_index)
    selected_priority = st.selectbox("Final Priority", priorities, index=priority_index)
    selected_department = st.selectbox("Final Department", departments, index=department_index)

    if st.button("✅ Confirm Case Information", type="primary"):
        update_case(
            case["case_id"],
            final_category=selected_category,
            final_priority=selected_priority,
            final_department=selected_department,
            status="Status / Resolution",
        )
        st.success("Case information confirmed.")
        st.rerun()

    st.markdown("### Status / Resolution")

    statuses = [
        "Received",
        "Under Review",
        "Forwarded to Department",
        "Awaiting Information",
        "In Progress",
        "Resolved",
        "Rejected / Not Applicable",
        "Other / Needs Review",
    ]
    current_status = case["case_status_detail"] or "Under Review"
    status_index = statuses.index(current_status) if current_status in statuses else 1

    status_detail = st.selectbox("Current Status", statuses, index=status_index)
    resolution = st.text_area(
        "Resolution / Outcome (optional)",
        value=case["resolution"] or "",
        height=100,
        placeholder="Enter only confirmed information.",
    )
    additional_info = st.text_area(
        "Additional Confirmed Information (optional)",
        value=case["additional_info"] or "",
        height=100,
        placeholder="Facts that are safe to communicate to the student.",
    )

    if st.button("💾 Save Status / Information"):
        update_case(
            case["case_id"],
            case_status_detail=status_detail,
            resolution=resolution.strip(),
            additional_info=additional_info.strip(),
            status="Response Draft",
        )
        st.success("Confirmed information saved.")
        st.rerun()

    st.markdown("### AI Response Draft")

    if case["final_category"]:
        if st.button("✍️ Generate Response Draft", type="primary"):
            with st.spinner("Generating response draft..."):
                result = draft_response(
                    complaint=case["complaint"],
                    category=case["final_category"],
                    priority=case["final_priority"],
                    department=case["final_department"],
                    status=case["case_status_detail"],
                    resolution=case["resolution"],
                    additional_info=case["additional_info"],
                )

            if result["success"]:
                update_case(
                    case["case_id"],
                    ai_response_draft=result["draft"],
                    status="Response Draft",
                )
                st.rerun()
            else:
                st.error(result["error"])
    else:
        st.info("Confirm case information before generating a response.")

    if case["ai_response_draft"]:
        edited_response = st.text_area(
            "Response",
            value=case["final_response"] or case["ai_response_draft"],
            height=260,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Edited Response"):
                update_case(
                    case["case_id"],
                    final_response=edited_response,
                    status="Response Draft",
                )
                st.success("Response saved.")
                st.rerun()

        with c2:
            if st.button("✅ Approve Response", type="primary"):
                if not edited_response.strip():
                    st.error("Response cannot be empty.")
                    st.stop()
                update_case(
                    case["case_id"],
                    final_response=edited_response,
                    response_approved=True,
                    approved_at="now",
                    status="Approved",
                )
                st.success("Response approved. It has NOT been sent automatically.")
                st.rerun()

    if case["response_approved"]:
        st.markdown("### Manual Sending")
        st.success("Response approved and ready for manual sending.")
        st.code(case["final_response"] or "", language="text")
        st.info("Copy the approved response and send it through the university's existing communication channel.")

        if st.button("📨 Mark as Sent"):
            update_case(
                case["case_id"],
                sent=True,
                sent_at="now",
                status="Sent",
            )
            st.success("Case marked as sent.")
            st.rerun()

    st.markdown("### Audit History")
    for event in case["audit_log"]:
        st.write(f"- **{event['timestamp']}** — {event['action']}")
