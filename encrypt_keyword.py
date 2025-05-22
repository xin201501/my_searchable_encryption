import enc_rust
def symmetric_encryption_for_keyword(key, word):
    # 使用AES加密算法进行加密
    ciphertext = enc_rust.aes_ecb_encrypt(key, word)
    return ciphertext


def symmetric_decryption_for_keyword(key, word_enc):
    # 使用AES解密算法进行解密
    plaintext = enc_rust.aes_ecb_decrypt(key, word_enc)
    return plaintext
