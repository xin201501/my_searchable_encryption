import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import re
from collections import defaultdict
from colored import Fore, Style


# 生成加密密钥
def generate_key(key_length=128):
    if key_length <= 0 or key_length % 8 != 0:
        raise ValueError(
            "Key length must be a positive integer multiple of 8 (e.g. 128, 256)"
        )
    return get_random_bytes(key_length // 8)  # AES-128


# 加密文档内容
def encrypt_doc(data, key):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode("utf-8"))
    return cipher.nonce + tag + ciphertext


# 解密文档内容
def decrypt_doc(encrypted_data, key):
    if len(encrypted_data) < 32:
        raise ValueError("Invalid encrypted data")
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")


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


# 构建加密索引
class EncryptedSearchEngine:
    def __init__(self, file_key, index_key, dataset_path, threshold=10):
        self.__file_key = file_key
        self.__index_key = index_key
        self.__inverted_index = defaultdict(list)
        self.__encrypted_docs = {}
        self.__words_appearance_time = defaultdict(int)  # 记录每个关键词出现的次数
        self.__word_appearance_time_per_doc = defaultdict(
            lambda: defaultdict(int)
        )  # 记录每个关键词出现在每个文档中的次数
        self.__dataset_path = dataset_path
        self.__threshold = threshold

    def __load_documents(self):
        documents = []
        with open(self.__dataset_path, "r") as f:
            try:
                # 尝试解析为JSON数组
                return json.load(f)
            except json.JSONDecodeError:
                # 回退到逐行解析模式
                f.seek(0)
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        documents.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num}: {e}")
        return documents

    def process_whole_document_set(self):
        # 加载示例数据（假设为维基百科JSON格式）
        documents = self.__load_documents()  # 使用上述加载方法

        # 遍历每个文档，对每个文档进行加密
        for idx, doc in enumerate(documents):
            doc_content = doc["title"] + " " + doc["text"]
            self.__count_word_appearance_per_doc(idx, doc_content)
            self.__encrypt_document(idx, doc_content)

        self.__count_keyword_appearance()
        self.__build_inverted_index()

    def __count_word_appearance_per_doc(self, docid, text):
        """统计指定文档中单词出现次数并更新索引

        Args:
            docid (int): 文档唯一标识符，用于关联单词统计结果
            text (str): 需要处理的文档文本内容

        Returns:
            None: 结果直接更新类成员变量words_appearance_time_per_doc
        """
        # 使用正则表达式提取全部单词并转换为小写
        words = re.findall(r"\b[\w-]+\b", text.lower())

        # 统计每个单词在当前文档中的出现次数
        # words_appearance_time_per_doc结构为: Dict[docid][word] = count
        for word in words:
            self.__word_appearance_time_per_doc[docid][word] += 1

    def __count_keyword_appearance(self):
        """
        统计所有文档中每个关键词的总出现次数

        遍历类属性word_appearance_time_per_doc中记录的每个文档词频数据
        将各个单词在所有文档中的出现次数累加存储到words_appearance_time字典中。
        该操作直接修改类实例的words_appearance_time属性
        无返回值。

        Args:
            无显式参数，通过类实例属性进行操作：
            self.word_appearance_time_per_doc (dict): 文档级词频记录，结构为 {docid: {word: count}}
            self.words_appearance_time (dict): 用于存储统计结果的字典，结构为 {word: total_count}

        Returns:
            None: 直接修改类实例的words_appearance_time属性
        """
        # 遍历每个文档的词频统计记录
        for docid, word_counts in self.__word_appearance_time_per_doc.items():
            # 累加当前文档的词频到全局统计字典
            for word, count in word_counts.items():
                self.__words_appearance_time[word] += count

    def __choose_out_keyword(self):
        # 返回出现次数大于threshold的词
        return [
            word
            for word, count in self.__words_appearance_time.items()
            if count > self.__threshold
        ]

    def __init_inverted_index(self):
        # 初始化倒排索引的关键字值
        for word in self.__choose_out_keyword():
            # 对关键词进行确定性加密处理
            word_enc = symmetric_encryption_for_keyword(self.__index_key, word)
            self.__inverted_index[word_enc] = []

    def __build_inverted_index(self):
        """构建倒排索引

        遍历word_appearance_time_per_doc，统计每个关键字在哪些文档中出现以及出现的次数，
        并将结果存储在inverted_index中。inverted_index的结构为{加密的关键字: [(加密的词频, 加密的doc_id), ...]}。
        """
        for doc_id, word_counts in self.__word_appearance_time_per_doc.items():
            for word, count in word_counts.items():
                if self.__words_appearance_time[word] <= self.__threshold:
                    continue
                # 对关键词进行确定性加密处理
                word_enc = symmetric_encryption_for_keyword(self.__index_key, word)
                # 对词频进行加密
                count_enc = symmetric_encryption_for_keyword(
                    self.__index_key, str(count)
                )
                # 对文档ID进行加密
                doc_id_enc = symmetric_encryption_for_keyword(
                    self.__index_key, str(doc_id)
                )
                # 将加密后的词频和文档ID对添加到倒排索引中
                self.__inverted_index[word_enc].append((count_enc, doc_id_enc))

    def __encrypt_document(self, doc_id, text: str):
        # 加密文档内容
        encrypted = encrypt_doc(text, self.__file_key)
        self.__encrypted_docs[doc_id] = encrypted

    def search(self, keyword: str):  # 返回词频——文档对
        # 加密查询关键词
        token = symmetric_encryption_for_keyword(self.__index_key, keyword.lower())
        tf_enc_and_doc_id_enc_structs = self.__inverted_index.get(token, [])
        return tf_enc_and_doc_id_enc_structs

    def decrypt_document(self, doc_id):
        return decrypt_doc(self.__encrypted_docs[doc_id], self.__file_key)


# 使用示例
if __name__ == "__main__":

    file_key = generate_key()
    index_key = generate_key()
    engine = EncryptedSearchEngine(
        file_key=file_key,
        index_key=index_key,
        dataset_path="dataset/test.json",
        threshold=2,
    )
    engine.process_whole_document_set()
    # 执行搜索
    results = engine.search("computing")
    print(f"Found {Fore.red}{len(results)}{Style.reset} document(s):")
    for tf_enc, doc_id_str_enc in results:
        tf_str = symmetric_decryption_for_keyword(index_key, tf_enc)
        doc_id_str = symmetric_decryption_for_keyword(index_key, doc_id_str_enc)
        tf = int(tf_str)
        doc_id = int(doc_id_str)
        print(
            f"Keyword appears {Fore.red}{tf}{Style.reset} time(s) in document {Fore.green}{doc_id}{Style.reset}"
        )
        print(f"Content: \n{engine.decrypt_document(doc_id)}")
