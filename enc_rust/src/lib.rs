use pyo3::prelude::*;
use mimalloc::MiMalloc;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;
/// 使用AES-128 ECB模式加密明文字符串
///
/// 参数：
/// - `key`: 16字节的AES加密密钥
/// - `plaintext`: 待加密的明文字符串
///
/// 返回值：
/// - 成功时返回包含加密数据的字节向量，错误时返回PyResult的Err变体
#[pyfunction]
fn aes_ecb_encrypt(key: [u8; 16], plaintext: &str) -> PyResult<Vec<u8>> {
    // 使用AES加密库的ECB模式加密实现
    use aes::cipher::{block_padding::Pkcs7, BlockEncryptMut, KeyInit};

    // 定义AES-128 ECB加密器类型别名
    type Aes128EcbEnc = ecb::Encryptor<aes::Aes128>;

    // 创建加密器实例并执行加密操作：
    // 1. 使用PKCS#7填充方案
    // 2. 生成加密后的字节向量
    let ct = Aes128EcbEnc::new(&key.into()).encrypt_padded_vec_mut::<Pkcs7>(plaintext.as_bytes());

    Ok(ct)
}

/// 使用AES-128 ECB模式解密密文字符串
///
/// 参数：
/// - `key`: 16字节的AES加密密钥
/// - `ciphertext`: 待解密的密文字符串
///
/// 返回值：
/// - 成功时返回包含解密数据的字节向量，错误时返回PyResult的Err变体
#[pyfunction]
fn aes_ecb_decrypt(key: [u8; 16], ciphertext: &[u8]) -> PyResult<String> {
    // 使用AES加密库的ECB模式解密实现
    use aes::cipher::{block_padding::Pkcs7, BlockDecryptMut, KeyInit};
    // 定义AES-128 ECB解密器类型别名
    type Aes128EcbDec = ecb::Decryptor<aes::Aes128>;

    // 创建解密器实例并执行解密操作
    let decrypt_vec = Aes128EcbDec::new(&key.into())
        .decrypt_padded_vec_mut::<Pkcs7>(ciphertext)
        .map_err(|_| PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid ciphertext"))?;
    Ok(String::from_utf8(decrypt_vec)?)
}

#[pyfunction]
fn aes_gcm_encrypt(key: [u8; 16], plaintext: &str) -> PyResult<Vec<u8>> {
    use aes_gcm::{
        aead::{Aead, AeadCore, KeyInit, OsRng},
        Aes128Gcm, Key,
    };

    // Alternatively, the key can be transformed directly from a byte slice
    // (panicks on length mismatch):
    let key = Key::<Aes128Gcm>::from_slice(&key);

    let cipher = Aes128Gcm::new(&key);
    let nonce = Aes128Gcm::generate_nonce(&mut OsRng); // 96-bits; unique per message
    let ciphertext = cipher
        .encrypt(&nonce, plaintext.as_bytes())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{}", e)))?;
    let mut result = nonce.to_vec();
    result.extend_from_slice(&ciphertext);
    Ok(result)
}

#[pyfunction]
fn aes_gcm_decrypt(key: [u8; 16], ciphertext: &[u8]) -> PyResult<String> {
    use aes_gcm::{
        aead::{Aead, KeyInit},
        Aes128Gcm, Key,
    };

    // Alternatively, the key can be transformed directly from a byte slice
    // (panicks on length mismatch):
    let key = Key::<Aes128Gcm>::from_slice(&key);
    let cipher = Aes128Gcm::new(&key);
    let nonce = &ciphertext[..12];
    let nonce = nonce.into();
    let ciphertext = &ciphertext[12..];
    let decrypted = cipher
        .decrypt(nonce, ciphertext)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{}", e)))?;
    Ok(String::from_utf8(decrypted)?)
}

/// A Python module implemented in Rust.
#[pymodule]
fn enc_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(aes_ecb_encrypt, m)?)?;
    m.add_function(wrap_pyfunction!(aes_ecb_decrypt, m)?)?;
    m.add_function(wrap_pyfunction!(aes_gcm_encrypt, m)?)?;
    m.add_function(wrap_pyfunction!(aes_gcm_decrypt, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_aes_ecb_encrypt() {
        let key = [0x03; 16];
        let plaintext = "Hello, World!";
        let ciphertext = aes_ecb_encrypt(key, plaintext).unwrap();
        let decrypted_text = aes_ecb_decrypt(key, &ciphertext).unwrap();
        assert_eq!(plaintext, decrypted_text);
    }

    #[test]
    fn test_aes_gcm_encrypt() {
        let key = [0x03; 16];
        let plaintext = "Hello, World!";
        let ciphertext = aes_gcm_encrypt(key, plaintext).unwrap();
        let decrypted_text = aes_gcm_decrypt(key, &ciphertext).unwrap();
        assert_eq!(plaintext, decrypted_text);
    }
}
