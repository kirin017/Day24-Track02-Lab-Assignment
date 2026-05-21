# src/quality/validation.py
import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ExpectationSuite:
    name: str
    meta: dict = field(default_factory=dict)

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    Tạo expectation suite cho anonymized patient data.
    """
    suite = ExpectationSuite(name="patient_data_suite")
    suite.meta["manual_expectations"] = [
        {"expectation": "patient_id_not_null", "column": "patient_id"},
        {"expectation": "cccd_length_12", "column": "cccd"},
        {
            "expectation": "ket_qua_xet_nghiem_between_0_and_50",
            "column": "ket_qua_xet_nghiem",
        },
        {
            "expectation": "benh_in_valid_set",
            "column": "benh",
            "value_set": ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"],
        },
        {
            "expectation": "email_matches_regex",
            "column": "email",
            "regex": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        },
        {"expectation": "patient_id_unique", "column": "patient_id"},
    ]

    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc dạng số thuần túy
    # (sau anonymization, cccd phải là fake hoặc masked)
    if "cccd" in df.columns:
        invalid_cccd = ~df["cccd"].astype(str).str.match(r"^\d{12}$")
        if invalid_cccd.any():
            results["failed_checks"].append("cccd must be 12 digits")

    # Check 2: Không có null values trong các cột quan trọng
    required_columns = ["patient_id", "cccd", "so_dien_thoai", "benh", "ket_qua_xet_nghiem"]
    null_columns = [
        column
        for column in required_columns
        if column in df.columns and df[column].isna().any()
    ]
    if null_columns:
        results["failed_checks"].append(f"null values in required columns: {null_columns}")

    # Check 3: Số rows phải bằng original
    try:
        original_rows = len(pd.read_csv("data/raw/patients_raw.csv"))
        results["stats"]["original_rows"] = original_rows
        if len(df) != original_rows:
            results["failed_checks"].append(
                f"row count mismatch: anonymized={len(df)} original={original_rows}"
            )
    except FileNotFoundError:
        results["failed_checks"].append("original dataset not found")

    valid_conditions = {"Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"}
    if "benh" in df.columns and not df["benh"].isin(valid_conditions).all():
        results["failed_checks"].append("benh contains invalid values")

    if "ket_qua_xet_nghiem" in df.columns:
        in_range = df["ket_qua_xet_nghiem"].between(0, 50)
        if not in_range.all():
            results["failed_checks"].append("ket_qua_xet_nghiem outside [0, 50]")

    if "email" in df.columns:
        email_pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        if not df["email"].astype(str).map(lambda value: bool(email_pattern.match(value))).all():
            results["failed_checks"].append("email contains invalid values")

    if "patient_id" in df.columns and df["patient_id"].duplicated().any():
        results["failed_checks"].append("duplicate patient_id found")

    results["success"] = not results["failed_checks"]

    return results
