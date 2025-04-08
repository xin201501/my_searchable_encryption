import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
import re
from collections import defaultdict


# 生成加密密钥
def generate_key(key_length=128):
    return get_random_bytes(key_length)  # AES-128


# 加密文档内容
def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode("utf-8"))
    return cipher.nonce + tag + ciphertext


# 解密文档内容
def decrypt_data(encrypted_data, key):
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")


# 构建加密索引
class EncryptedSearchEngine:
    def __init__(self, file_key, index_key, file_path):
        self.file_key = file_key
        self.index_key = index_key
        self.inverted_index = defaultdict(list)
        self.encrypted_docs = {}
        self.words_appearance_time = defaultdict(int)  # 记录每个关键词出现的次数
        self.file_path = file_path

    def process_whole_document_set(self):
        # 加载示例数据（假设为维基百科JSON格式）
        with open(self.file_path) as f:
            documents = json.load(f)

        # 遍历每个文档，对每个文档进行加密和索引构建
        for idx, doc in enumerate(documents):
            self.process_document(idx, doc["title"] + " " + doc["content"])

    def process_document(self, doc_id, text):
        # 加密文档内容
        encrypted = encrypt_data(text, self.file_key)
        self.encrypted_docs[doc_id] = encrypted

        # 构建倒排索引
        # 提取文档中所有的单词并计算单词出现的次数，单词间由标点符号分隔

        # for word in words:
        #     # 对关键词进行HMAC处理
        #     hmac = hashlib.pbkdf2_hmac('sha256', word.encode(), self.key, 100000)
        #     self.index[hmac].append(doc_id)

    def search(self, keyword):
        # 加密查询关键词
        hmac = hashlib.pbkdf2_hmac(
            "sha256", keyword.lower().encode(), self.index_key, 100000
        )
        doc_ids = self.inverted_index.get(hmac, [])
        return [self.decrypt_doc(doc_id) for doc_id in doc_ids]

    def decrypt_doc(self, doc_id):
        return decrypt_data(self.encrypted_docs[doc_id], self.key)


# 使用示例
if __name__ == "__main__":

    file_key = generate_key()
    index_key = generate_key()
    engine = EncryptedSearchEngine(
        file_key=file_key, index_key=index_key, file_path="sample.json"
    )
    engine.process_whole_document_set()
    # 执行搜索
    results = engine.search("science")
    print(f"Found {len(results)} documents:")
    for doc in results[:3]:
        print(doc[:200] + "...")
