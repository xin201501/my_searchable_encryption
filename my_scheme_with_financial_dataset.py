from my import EncryptedIndexBuilder, Searcher, generate_key
from preprocess_finance_corpus import get_news_data, process_news
import argparse
import argcomplete
from colored import Fore, Style
import requests
import base64
import LSSS
from Crypto.Util.number import getPrime
from save_shares import save_dealer_sgx, save_key_shares
import encrypt_keyword


class FinanceDataSetIndexBuilder(EncryptedIndexBuilder):
    def __init__(self, file_key, index_key, dataset_path, threshold=10):
        super().__init__(file_key, index_key, dataset_path, threshold)

    def load_documents(self, count: int | None = None):
        news_df = get_news_data(self.dataset_path)
        # print(f"Fetched {len(news_df)} news articles for {self.dataset_path}")
        corpus = process_news(news_df)
        if count:
            corpus = corpus[:count]
        return corpus


if __name__ == "__main__":
    # 配置命令行参数解析
    parser = argparse.ArgumentParser(description="Encrypted Search Engine")
    parser.add_argument("--company_name", type=str, required=True, help="company name")
    parser.add_argument(
        "--threshold",
        type=int,
        required=True,
        help="appearance threshold for a word to be a keyword",
    )
    parser.add_argument("--user_count", type=int, required=True, help="user count")
    parser.add_argument("--keyword", type=str, help="Search keyword to look up")
    parser.add_argument("--doc_count", type=int, help="doc count")
    parser.add_argument(
        "--local_search", type=bool, default=False, help="Perform local search or not"
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # 创建加密引擎
    file_key = generate_key()
    index_key = generate_key()
    index_builder = FinanceDataSetIndexBuilder(
        file_key=file_key,
        index_key=index_key,
        dataset_path=args.company_name,
        threshold=args.threshold,
    )
    index_builder.process_whole_document_set(load_count=args.doc_count)

    second_secret_access_structure = []
    for user_id in range(1, args.user_count):
        second_secret_access_structure.append([user_id, args.user_count + 1])

    # 使用LSSS库拆分index_key和file_key
    dealer, key_shares = LSSS.setup_secret_sharing(
        prime=getPrime(256),
        secrets=[int.from_bytes(index_key), int.from_bytes(file_key)],
        n_data_users=args.user_count,
        custom_access_structures=[second_secret_access_structure],
    )

    # store all users and SGX's index_key_shares in a file
    save_key_shares(key_shares)
    save_dealer_sgx(dealer)

    # dump keywords to a file
    index_builder.dump_keywords("keywords.txt")

    # dump index to a file
    index_builder.dump_index("index.bin")

    index_builder.dump_encrypted_docs("encrypted_docs_finance")

    if args.local_search is False:
        print(f"Indexing complete.")
        exit(0)

    token = encrypt_keyword.symmetric_encryption_for_keyword(
        index_key, args.keyword.lower()
    )

    search_engine = Searcher(
        index_path="index.bin",
        file_dir="encrypted_docs_finance",
        file_key=file_key,
    )
    # 执行搜索
    results = search_engine.search(token)
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
            print(f"Content: \n{search_engine.decrypt_document(doc_id)}")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.red}Error: Failed to send HTTP request.{Style.reset}")
