// 在 crypto.rs 中添加实现
use aes::{
    Aes128, Aes256,
    cipher::{BlockDecryptMut, KeyInit, block_padding::Pkcs7},
};
pub fn symmetric_decryption_for_keyword_128bit(
    key: &[u8],
    ciphertext: &[u8],
) -> Result<String, String> {
    let cipher = ecb::Decryptor::<Aes128>::new_from_slice(key)
        .map_err(|_| "Failed to create AES-128 ECB decryptor".to_string())?;
    let decrypted = cipher
        .decrypt_padded_vec_mut::<Pkcs7>(ciphertext)
        .map_err(|e| format!("Decryption failed with error {e}"))?;
    String::from_utf8(decrypted.to_vec()).map_err(|e| format!("UTF-8 conversion failed: {}", e))
}

pub fn symmetric_decryption_for_keyword_256bit(
    key: &[u8],
    ciphertext: &[u8],
) -> Result<String, String> {
    let cipher = ecb::Decryptor::<Aes256>::new_from_slice(key)
        .map_err(|_| "Failed to create AES-256 ECB decryptor".to_string())?;
    let decrypted = cipher
        .decrypt_padded_vec_mut::<Pkcs7>(ciphertext)
        .map_err(|e| format!("Decryption failed with error {e}"))?;
    String::from_utf8(decrypted.to_vec()).map_err(|e| format!("UTF-8 conversion failed: {}", e))
}

#[cfg(test)]
mod tests_128bit {
    use super::*;
    use aes::{Aes128, cipher::BlockEncryptMut};

    type Aes128EcbEnc = ecb::Encryptor<Aes128>;

    #[test]
    fn tc1_normal_decryption() {
        // Arrange
        let key = [0u8; 16];
        let plaintext = "ECB模式测试数据";
        // 生成测试密文
        let encryptor = Aes128EcbEnc::new_from_slice(&key).unwrap();
        let mut buffer = plaintext.as_bytes().to_vec();
        let ciphertext = encryptor.encrypt_padded_vec_mut::<Pkcs7>(&mut buffer);

        // Act
        let result = symmetric_decryption_for_keyword_128bit(&key, &ciphertext);

        // Assert
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), plaintext);
    }

    #[test]
    fn tc2_invalid_ciphertext_length() {
        // Arrange
        let key = [0u8; 16];
        let mut ciphertext = vec![0u8; 15]; // 非16倍数长度

        // Act
        let result = symmetric_decryption_for_keyword_128bit(&key, &mut ciphertext);

        // Assert
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Decryption failed"));
    }

    #[test]
    fn tc3_corrupted_padding() {
        // Arrange
        let key = [0u8; 16];
        let mut ciphertext = vec![0u8; 16]; // 全零数据会导致填充解析失败

        // Act
        let result = symmetric_decryption_for_keyword_128bit(&key, &mut ciphertext);

        // Assert
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Decryption failed"));
    }

    #[test]
    fn tc4_invalid_utf8_data() {
        // Arrange
        let key = [0u8; 16];
        // 构造解密后得到0xFF的测试数据
        let invalid_utf8 = vec![0xFFu8; 16];
        let encryptor = Aes128EcbEnc::new_from_slice(&key).unwrap();
        let mut binding = invalid_utf8.clone();
        let ciphertext = encryptor.encrypt_padded_vec_mut::<Pkcs7>(&mut binding);

        // Act
        let result = symmetric_decryption_for_keyword_128bit(&key, &ciphertext);

        // Assert
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("UTF-8 conversion failed"));
    }
}

#[cfg(test)]
mod tests_256bit {
    use super::*;
    use aes::{Aes256, cipher::BlockEncryptMut};
    type Aes256EcbEnc = ecb::Encryptor<Aes256>;
    #[test]
    fn tc1_normal_decryption() {
        // Arrange
        let key = [1u8; 32];
        let plaintext = "ECB模式测试数据";
        // 生成测试密文
        let encryptor = Aes256EcbEnc::new_from_slice(&key).unwrap();
        let mut buffer = plaintext.as_bytes().to_vec();
        let ciphertext = encryptor.encrypt_padded_vec_mut::<Pkcs7>(&mut buffer);

        // Act
        let result = symmetric_decryption_for_keyword_256bit(&key, &ciphertext);

        // Assert
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), plaintext);
    }

    #[test]
    fn tc2_invalid_ciphertext_length() {
        // Arrange
        let key = [1u8; 32];
        let mut ciphertext = vec![0u8; 15]; // 非16倍数长度

        // Act
        let result = symmetric_decryption_for_keyword_256bit(&key, &mut ciphertext);

        // Assert
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Decryption failed"));
    }

    #[test]
    fn tc3_corrupted_padding() {
        // Arrange
        let key = [1u8; 32];
        let mut ciphertext = vec![0u8; 16]; // 全零数据会导致填充解析失败

        // Act
        let result = symmetric_decryption_for_keyword_256bit(&key, &mut ciphertext);

        // Assert
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Decryption failed"));
    }

    #[test]
    fn tc4_invalid_utf8_data() {
        // Arrange
        let key = [1u8; 32];
        // 构造解密后得到0xFF的测试数据
        let invalid_utf8 = vec![0xFFu8; 16];
        let encryptor = Aes256EcbEnc::new_from_slice(&key).unwrap();
        let mut binding = invalid_utf8.clone();
        let ciphertext = encryptor.encrypt_padded_vec_mut::<Pkcs7>(&mut binding);

        // Act
        let result = symmetric_decryption_for_keyword_256bit(&key, &ciphertext);

        // Assert
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("UTF-8 conversion failed"));
    }
}
