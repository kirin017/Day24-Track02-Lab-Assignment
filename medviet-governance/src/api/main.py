# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()
RAW_DATA_PATH = "data/raw/patients_raw.csv"
ANON_DATA_PATH = "data/processed/patients_anonymized.csv"


def _load_patients() -> pd.DataFrame:
    try:
        return pd.read_csv(RAW_DATA_PATH)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Raw patient dataset not found. Run scripts/generate_data.py first.",
        ) from exc

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    df = _load_patients()
    return {"records": df.head(10).to_dict(orient="records")}

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    df = _load_patients()
    df_anon = anonymizer.anonymize_dataframe(df)
    df_anon.to_csv(ANON_DATA_PATH, index=False)
    return {"records": df_anon.head(10).to_dict(orient="records")}

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    df = _load_patients()
    by_condition = df["benh"].value_counts().to_dict()
    avg_result = df.groupby("benh")["ket_qua_xet_nghiem"].mean().round(2).to_dict()

    return {
        "total_patients": int(len(df)),
        "patients_by_condition": {str(key): int(value) for key, value in by_condition.items()},
        "average_lab_result_by_condition": {
            str(key): float(value) for key, value in avg_result.items()
        },
    }

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    return {
        "status": "deleted",
        "patient_id": patient_id,
        "deleted_by": current_user["username"],
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
