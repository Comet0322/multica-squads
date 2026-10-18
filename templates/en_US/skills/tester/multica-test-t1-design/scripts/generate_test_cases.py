#!/usr/bin/env python3
"""
Test Case Generator Script
Helper script for generating structured test cases, providing a standardized output format.
Every case must be tagged with a coverage dimension (Full scenario / Boundary scenario / Page check).
"""

from dataclasses import dataclass, field
from typing import Optional
import json, re, sys

# Fix Windows terminal encoding for non-ASCII output
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Coverage dimension constants
DIMENSION_FULL = "Full scenario"       # all business paths
DIMENSION_BOUNDARY = "Boundary scenario"    # boundary values / critical conditions
DIMENSION_UI = "Page check"          # UI / interaction checks

VALID_DIMENSIONS = {DIMENSION_FULL, DIMENSION_BOUNDARY, DIMENSION_UI}


# ============================================================
# Data Models
# ============================================================

@dataclass
class FunctionalTestCase:
    """Functional test case data model."""
    case_id: str
    module: str
    coverage_dimension: str  # Full scenario / Boundary scenario / Page check
    title: str
    preconditions: list[str]
    test_data: str
    case_type: str  # Functional flow / Input validation / UI check / Boundary value / Exception scenario
    priority: str   # P1 core / P2 normal / P3 exception or boundary (never default to P0)
    steps: list[str]
    expected_results: list[str]

    def __post_init__(self):
        if self.coverage_dimension not in VALID_DIMENSIONS:
            raise ValueError(
                f"coverage_dimension must be one of: {VALID_DIMENSIONS}"
            )


@dataclass
class ApiTestCase:
    """API test case data model."""
    case_id: str
    api_name: str
    api_endpoint: str
    coverage_dimension: str  # Full scenario / Boundary scenario / Page check
    title: str
    method: str  # GET/POST/PUT/DELETE
    preconditions: list[str]
    request_params: dict
    expected_status_code: int
    expected_biz_code: Optional[int] = None
    expected_response_body: dict = field(default_factory=dict)
    validation_points: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.coverage_dimension not in VALID_DIMENSIONS:
            raise ValueError(
                f"coverage_dimension must be one of: {VALID_DIMENSIONS}"
            )


# ============================================================
# Formatters
# ============================================================

def format_module_header(module_name: str, full_scenes: list[str],
                         boundary_scenes: list[str],
                         ui_checks: list[str]) -> str:
    """Format the module coverage-matrix header."""
    lines = [
        "=" * 60,
        f"Module: {module_name}",
        "=" * 60,
        "[Coverage matrix]",
    ]
    if full_scenes:
        lines.append(f"  ┌ {DIMENSION_FULL}: {' / '.join(full_scenes)}")
    if boundary_scenes:
        lines.append(f"  ┌ {DIMENSION_BOUNDARY}: {' / '.join(boundary_scenes)}")
    if ui_checks:
        lines.append(f"  ┌ {DIMENSION_UI}: {' / '.join(ui_checks)}")
    lines.append("")
    return "\n".join(lines)


def format_functional_case(tc: FunctionalTestCase) -> str:
    """Format a functional test case for output."""
    lines = [
        "-" * 60,
        f"Case ID: {tc.case_id}",
        f"Module: {tc.module}",
        f"Coverage dimension: {tc.coverage_dimension}",
        f"Title: {tc.title}",
        f"Case type: {tc.case_type}",
        f"Priority:  {tc.priority}",
        "",
        "Preconditions:",
    ]
    for i, cond in enumerate(tc.preconditions, 1):
        lines.append(f"  {i}. {cond}")

    lines.extend(["", f"Test data: {tc.test_data}", ""])

    lines.append("Steps:")
    for i, step in enumerate(tc.steps, 1):
        lines.append(f"  {i}. {step}")

    lines.append("")
    lines.append("Expected results:")
    for i, res in enumerate(tc.expected_results, 1):
        lines.append(f"  {i}. {res}")

    lines.append("")
    return "\n".join(lines)


def format_api_case(tc: ApiTestCase) -> str:
    """Format an API test case for output."""
    lines = [
        "-" * 60,
        f"Case ID: {tc.case_id}",
        f"API: {tc.method} {tc.api_endpoint}",
        f"Coverage dimension: {tc.coverage_dimension}",
        f"Title: {tc.title}",
        f"Method: {tc.method}",
        "",
        "Preconditions:",
    ]
    for i, cond in enumerate(tc.preconditions, 1):
        lines.append(f"  {i}. {cond}")

    lines.extend(["", "Request parameters:", json.dumps(tc.request_params, ensure_ascii=False, indent=2), ""])
    lines.append(f"Expected status code: {tc.expected_status_code}")
    if tc.expected_biz_code is not None:
        lines.append(f"Expected business code: {tc.expected_biz_code}")
    lines.extend(["", "Expected response body:", json.dumps(tc.expected_response_body, ensure_ascii=False, indent=2), ""])

    lines.append("Validation points:")
    for pt in tc.validation_points:
        lines.append(f"  - {pt}")

    lines.append("")
    return "\n".join(lines)


def format_dedup_report(skipped: int, ambiguous: int, details: list[dict]) -> str:
    """Format the dedup report."""
    lines = [
        "",
        "[Dedup report]",
        f"  Skipped automatically (duplicates): {skipped}",
        f"  Flagged as ambiguous: {ambiguous}",
    ]
    for d in details:
        tc = d.get("test_case", {})
        match = d.get("best_match", {})
        sim = d.get("similarity", 0)
        lines.append(
            f"    {tc.get('title', '?')[:50]} -> "
            f"matched {match.get('key', '?')} ({sim:.0%})"
        )
    return "\n".join(lines)


def clean_wiki_markers(text: str) -> str:
    """Strip Confluence wiki markers (e.g. {LQ}{RQ}) so cases stay readable.

    These markers may survive as plain text after Confluence HTML->Markdown conversion,
    and would confuse users if they appeared in test cases.
    """
    text = re.sub(r'\{LQ\}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\{RQ\}', '', text, flags=re.IGNORECASE)
    return text


def validate_steps_expected(tc) -> None:
    """Validate the steps / expected_results correspondence; on mismatch log a warning without aborting.

    Note: an expected result may contain several verification points (numbered 1) 2) 3)),
    but every step must have a matching expected result; empty expected results are forbidden.
    A validation problem in one case does not block generation of the others.
    """
    steps = tc.get("steps", [])
    expected = tc.get("expected_results", [])
    if not steps:
        return
    if not expected:
        print(f"WARNING: case_id={tc.get('case_id', '?')} title={tc.get('title', '?')} "
              f"has steps but empty expected results; recorded")
        return
    # Check for empty-string expected results
    for i, (step, exp) in enumerate(zip(steps, expected)):
        if not exp or not exp.strip():
            print(f"WARNING: case_id={tc.get('case_id', '?')} "
                  f"step {i+1}='{step[:30]}' has an empty expected result; flagged")


def print_coverage_checklist(modules: dict[str, dict[str, bool]],
                              uncovered_notes: str = ""):
    """Print the module-level coverage checklist."""
    lines = ["", "=" * 60, "Coverage check report", "=" * 60]
    for module_name, dims in modules.items():
        lines.append(f"\nModule: {module_name}")
        for dim, covered in dims.items():
            mark = "✓" if covered else " "
            lines.append(f"  [{mark}] {dim}")
    if uncovered_notes:
        lines.append(f"\nUncovered notes: {uncovered_notes}")
    print("\n".join(lines))


# ============================================================
# Example usage
# ============================================================

if __name__ == "__main__":
    # Demo: module header
    print(format_module_header(
        module_name="User login",
        full_scenes=["Normal login", "Wrong password", "User does not exist", "Account locked", "Remember password"],
        boundary_scenes=["Empty username", "Empty password", "Overlong password (100 chars)", "5 consecutive failures"],
        ui_checks=["Login page layout", "Input hover state", "Error message position", "Button disabled state"],
    ))

    # Demo: functional test case
    ftc = FunctionalTestCase(
        case_id="TC-F-LOGIN-001",
        module="User login",
        coverage_dimension=DIMENSION_FULL,
        title="Verify login succeeds with the correct username and password",
        preconditions=["User is registered and the account is in good standing", "The login page is open in the browser"],
        test_data="Username: testuser@example.com, Password: Abc@123456",
        case_type="Functional flow",
        priority="P1",
        steps=[
            "Enter testuser@example.com in the username field",
            "Enter Abc@123456 in the password field",
            "Click the 'Log in' button",
        ],
        expected_results=[
            "The field displays the entered text normally",
            "The password is displayed masked",
            "Login succeeds and redirects to the home page",
        ],
    )
    print(format_functional_case(ftc))

    print(print_coverage_checklist(
        {
            "User login": {
                DIMENSION_FULL: True,
                DIMENSION_BOUNDARY: True,
                DIMENSION_UI: True,
            },
            "Product list": {
                DIMENSION_FULL: True,
                DIMENSION_BOUNDARY: False,
                DIMENSION_UI: True,
            },
        },
        uncovered_notes="Product list lacks pagination boundary scenarios (API docs missing)",
    ))
