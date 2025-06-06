import argparse
import json
import os
import pickle
import sys
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import re
from collections import defaultdict
from colored import Fore, Style
import requests
import base64
import LSSS
from Crypto.Util.number import getPrime
import encrypt_keyword
from save_shares import save_dealer_sgx, save_index_key_shares
from collections import Counter
import enc_rust


def serialize_shares(shares):
    serialized = []
    for x, share in shares:
        serialized.append(
            {"x": x, "share": base64.b64encode(share).decode("utf-8")}  # 转换为字符串
        )
    return serialized


# 生成加密密钥
def generate_key(key_length=128):
    if key_length <= 0 or key_length % 8 != 0:
        raise ValueError(
            "Key length must be a positive integer multiple of 8 (e.g. 128, 256)"
        )
    return get_random_bytes(key_length // 8)  # AES-128


# 加密文档内容
def encrypt_doc(data, key):
    return enc_rust.aes_gcm_encrypt(key, data)


# 解密文档内容
def decrypt_doc(encrypted_data, key):
    return enc_rust.aes_gcm_decrypt(key, encrypted_data)


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
        self.__word_pattern = re.compile(r"\b[\w-]+\b")

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
        words = self.__word_pattern.findall(text.lower())

        # 统计每个单词在当前文档中的出现次数
        # words_appearance_time_per_doc结构为: Dict[docid][word] = count
        word_counts = Counter(words)
        self.__word_appearance_time_per_doc[docid].update(word_counts)

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
            word_enc = encrypt_keyword.symmetric_encryption_for_keyword(
                self.__index_key, word
            )
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
                word_enc = encrypt_keyword.symmetric_encryption_for_keyword(
                    self.__index_key, word
                )
                # 对词频进行加密
                count_enc = encrypt_keyword.symmetric_encryption_for_keyword(
                    self.__index_key, str(count)
                )
                # 对文档ID进行加密
                doc_id_enc = encrypt_keyword.symmetric_encryption_for_keyword(
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
        token = encrypt_keyword.symmetric_encryption_for_keyword(
            self.__index_key, keyword.lower()
        )
        tf_enc_and_doc_id_enc_structs = self.__inverted_index.get(token, [])
        return tf_enc_and_doc_id_enc_structs

    def decrypt_document(self, doc_id):
        return decrypt_doc(self.__encrypted_docs[doc_id], self.__file_key)

    def dump_index(self, file_path):
        with open(file_path, "wb") as f:
            pickle.dump(self.__inverted_index, f)


# 使用示例
if __name__ == "__main__":
    # 配置命令行参数解析
    parser = argparse.ArgumentParser(description="Encrypted Search Engine")
    parser.add_argument(
        "--dataset", type=str, required=True, help="Path to dataset JSON file"
    )
    parser.add_argument(
        "--keyword", type=str, required=True, help="Search keyword to look up"
    )
    args = parser.parse_args()
    # 判断文件是否存在
    if not os.path.exists(args.dataset):
        print(
            f"{Fore.red}Error: Dataset file {args.dataset} does not exist.{Style.reset}"
        )
        sys.exit(1)

    # 创建加密引擎
    file_key = generate_key()
    index_key = generate_key()
    engine = EncryptedSearchEngine(
        file_key=file_key,
        index_key=index_key,
        dataset_path=args.dataset,
        threshold=0,
    )
    engine.process_whole_document_set()

    # 使用LSSS库拆分index_key
    dealer, index_key_shares = LSSS.setup_secret_sharing(
        prime=getPrime(256),
        secrets=[int.from_bytes(index_key)],
        n_data_users=2,
    )

    # store all users and SGX's index_key_shares in a file
    save_index_key_shares(index_key_shares)
    save_dealer_sgx(dealer)

    # dump index to a file
    engine.dump_index("index.bin")

    sys.exit(0)

    # 执行搜索
    results = engine.search(args.keyword.lower())
    print(f"Found {Fore.red}{len(results)}{Style.reset} document(s):")
    # 发送HTTP请求
    # 将 results 和 index_key 作为 JSON 数据发送到服务器
    print(f"{Fore.red}Sending HTTP request to server...{Style.reset}")
    payload = {
        "encrypted_results": [
            (
                base64.b64encode(count_enc).decode("utf-8"),
                base64.b64encode(doc_id_enc).decode("utf-8"),
            )
            for count_enc, doc_id_enc in results  # results来自engine.search()
        ],
        "index_key": base64.b64encode(index_key).decode("utf-8"),
    }
    try:
        response = requests.post(
            url="http://localhost:8003/sort-encrypted-results",
            json=payload,
        )
        response.raise_for_status()  # 如果响应状态码不是2xx，则引发异常
        sorted_results = response.json()["sorted_results"]
        for tf_str, doc_id_str in sorted_results:
            tf = int(tf_str)
            doc_id = int(doc_id_str)
            print(
                f"Keyword appears {Fore.red}{tf}{Style.reset} times in document {Fore.green}{doc_id}{Style.reset}"
            )
            print(f"Content: \n{engine.decrypt_document(doc_id)}")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.red}Error: Failed to send HTTP request.{Style.reset}")
