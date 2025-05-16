from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def symmetric_encryption_for_keyword(key, word):
    # 使用AES加密算法进行加密
    cipher = AES.new(key, AES.MODE_ECB)
    # 添加PKCS7填充
    padded_data = pad(word.encode(), AES.block_size)
    ciphertext = cipher.encrypt(padded_data)
    return ciphertext


def symmetric_decryption_for_keyword(key, word_enc):
    # 使用AES解密算法进行解密
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_padded = cipher.decrypt(word_enc)
    # 移除填充
    return unpad(decrypted_padded, AES.block_size).decode()
