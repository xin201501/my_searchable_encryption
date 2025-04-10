import pytest
from my import encrypt_doc, decrypt_doc, generate_key


class TestEncryptDoc:
    def setup_method(self):
        self.test_key = generate_key()
        self.test_data = (
            "This is a secret message containing 12345 & special characters@"
        )

    def test_encrypt_decrypt_consistency(self):
        # 正常加密解密流程验证
        encrypted = encrypt_doc(self.test_data, self.test_key)
        decrypted = decrypt_doc(encrypted, self.test_key)
        assert decrypted == self.test_data

    def test_empty_data(self):
        # 空数据加密场景
        encrypted = encrypt_doc("", self.test_key)
        decrypted = decrypt_doc(encrypted, self.test_key)
        assert decrypted == ""

    def test_invalid_key(self):
        # 密钥错误场景验证
        wrong_key = generate_key()
        encrypted = encrypt_doc(self.test_data, self.test_key)
        with pytest.raises(ValueError):
            decrypt_doc(encrypted, wrong_key)

    def test_tampered_ciphertext(self):
        # 数据篡改检测场景
        encrypted = encrypt_doc(self.test_data, self.test_key)
        tampered = encrypted[:32] + b"x" + encrypted[33:]  # 修改密文部分
        with pytest.raises(ValueError):
            decrypt_doc(tampered, self.test_key)
