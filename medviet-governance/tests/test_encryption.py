from src.encryption.vault import SimpleVault


def test_envelope_encryption_round_trip(tmp_path):
    vault = SimpleVault(master_key_path=str(tmp_path / "vault.key"))
    sample_cccd = "012345678901"
    original = f"Nguyen Van A - CCCD: {sample_cccd}"

    encrypted = vault.encrypt_data(original)
    decrypted = vault.decrypt_data(encrypted)

    assert encrypted["algorithm"] == "AES-256-GCM"
    assert decrypted == original
    assert original not in encrypted["ciphertext"]
