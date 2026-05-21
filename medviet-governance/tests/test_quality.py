import pandas as pd

from src.pii.anonymizer import MedVietAnonymizer
from src.quality.validation import validate_anonymized_data


def test_validate_anonymized_data_success(tmp_path):
    df = pd.read_csv("data/raw/patients_raw.csv")
    df_anon = MedVietAnonymizer().anonymize_dataframe(df)
    output_path = tmp_path / "patients_anonymized.csv"
    df_anon.to_csv(output_path, index=False)

    result = validate_anonymized_data(str(output_path))

    assert result["success"] is True
    assert result["failed_checks"] == []
    assert result["stats"]["total_rows"] == len(df)
