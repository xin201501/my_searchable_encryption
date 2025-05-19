from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from functools import lru_cache


@lru_cache(maxsize=100, typed=True)
def _get_encrypt_cipher(key: bytes):
    return AES.new(key, AES.MODE_ECB)


# 缓存解密 cipher 对象
@lru_cache(maxsize=100, typed=True)
def _get_decrypt_cipher(key: bytes):
    return AES.new(key, AES.MODE_ECB)


def symmetric_encryption_for_keyword(key, word):
    # 使用AES加密算法进行加密
    cipher = _get_encrypt_cipher(key)
    # 添加PKCS7填充
    padded_data = pad(word.encode(), AES.block_size)
    ciphertext = cipher.encrypt(padded_data)
    return ciphertext


def symmetric_decryption_for_keyword(key, word_enc):
    # 使用AES解密算法进行解密
    cipher = _get_decrypt_cipher(key)
    decrypted_padded = cipher.decrypt(word_enc)
    # 移除填充
    return unpad(decrypted_padded, AES.block_size).decode()
