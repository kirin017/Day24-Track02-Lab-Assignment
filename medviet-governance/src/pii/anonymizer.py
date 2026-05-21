# src/pii/anonymizer.py
import hashlib
import secrets

import pandas as pd
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        text = "" if text is None else str(text)
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        if strategy == "replace":
            return self._replace_detected_spans(text, results)
        elif strategy == "mask":
            return self._mask_detected_spans(text, results)
        elif strategy == "hash":
            return self._hash_detected_spans(text, results)
        else:
            raise ValueError(f"Unsupported anonymization strategy: {strategy}")

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = [fake.name() for _ in range(len(df_anon))]
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(len(df_anon))]
        if "email" in df_anon.columns:
            df_anon["email"] = [fake.email() for _ in range(len(df_anon))]
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = [fake.address().replace("\n", ", ") for _ in range(len(df_anon))]
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = [self._fake_cccd() for _ in range(len(df_anon))]
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [self._fake_phone() for _ in range(len(df_anon))]
        if "ngay_sinh" in df_anon.columns:
            df_anon["ngay_sinh"] = [self._generalize_birth_year(value) for value in df_anon["ngay_sinh"]]

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0

    @staticmethod
    def _fake_cccd() -> str:
        return secrets.choice("123456789") + "".join(secrets.choice("0123456789") for _ in range(11))

    @staticmethod
    def _fake_phone() -> str:
        return f"0{secrets.choice(['3', '5', '7', '8', '9'])}" + "".join(
            secrets.choice("0123456789") for _ in range(8)
        )

    @staticmethod
    def _generalize_birth_year(value: object) -> str:
        parts = str(value).split("/")
        return parts[-1] if parts and len(parts[-1]) == 4 else str(value)

    @staticmethod
    def _hash_detected_spans(text: str, results: list) -> str:
        output = text
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            original = output[result.start:result.end]
            digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
            output = output[:result.start] + digest + output[result.end:]
        return output

    def _replace_detected_spans(self, text: str, results: list) -> str:
        output = text
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            replacement = {
                "PERSON": fake.name(),
                "EMAIL_ADDRESS": fake.email(),
                "VN_CCCD": self._fake_cccd(),
                "VN_PHONE": self._fake_phone(),
            }.get(result.entity_type, "[REDACTED]")
            output = output[:result.start] + replacement + output[result.end:]
        return output

    @staticmethod
    def _mask_detected_spans(text: str, results: list) -> str:
        output = text
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            original = output[result.start:result.end]
            masked = " ".join(
                word[:1] + ("*" * max(len(word) - 1, 0)) for word in original.split(" ")
            )
            output = output[:result.start] + masked + output[result.end:]
        return output
