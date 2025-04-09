import pytest
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
from my import decrypt_doc


class TestDecryptDoc:
    @pytest.fixture(autouse=True)
    def setup(self):
        """公共测试夹具"""
        self.plaintext = "敏感数据-张三 身份证号：123456"
        self.key = hashlib.sha256(b"secret").digest()

        # 生成合法加密数据
        nonce = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(self.plaintext.encode("utf-8"))
        self.valid_data = nonce + tag + ciphertext

    def test_normal_decryption(self):
        """正常解密场景验证"""
        result = decrypt_doc(self.valid_data, self.key)
        assert result == self.plaintext

    def test_short_data(self):
        """异常数据长度验证"""
        with pytest.raises(ValueError) as excinfo:
            decrypt_doc(b"short_data", self.key)
        assert "Invalid encrypted data" in str(excinfo.value)

    def test_invalid_key_length(self):
        """非法密钥长度验证"""
        with pytest.raises(ValueError, match="Incorrect AES key length"):
            invalid_key = b"short_key_15"
            decrypt_doc(self.valid_data, invalid_key)

    def test_tag_verification_fail(self):
        """数据完整性验证"""
        tampered_data1 = self.valid_data[:16] + b"x" * 16 + self.valid_data[32:]
        with pytest.raises(ValueError, match="MAC check failed"):
            decrypt_doc(tampered_data1, self.key)

        tampered_data2 = self.valid_data[:32] + b"b" + self.valid_data[33:]
        with pytest.raises(ValueError, match="MAC check failed"):
            decrypt_doc(tampered_data2, self.key)

    def test_invalid_encoding(self):
        """非UTF8编码数据处理"""
        nonce = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(b"\x80invalid")

        with pytest.raises(UnicodeDecodeError) as excinfo:
            decrypt_doc(nonce + tag + ciphertext, self.key)
        assert "utf-8" in str(excinfo.value).lower()

    @pytest.mark.parametrize(
        "invalid_data",
        [
            b"",  # 空数据
            b"short",  # 过短数据
            b"0" * 31,  # 边界长度
            bytes(100),  # 随机二进制
        ],
    )
    def test_invalid_data_scenarios(self, invalid_data):
        with pytest.raises(ValueError):
            decrypt_doc(invalid_data, self.key)
