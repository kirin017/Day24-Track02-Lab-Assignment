from pathlib import Path

from scripts.generate_data import generate_patients


def pytest_sessionstart(session):
    project_root = Path(__file__).resolve().parents[1]
    raw_path = project_root / "data" / "raw" / "patients_raw.csv"

    if raw_path.exists():
        return

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    generate_patients().to_csv(raw_path, index=False)
