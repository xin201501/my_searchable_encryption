from my import EncryptedSearchEngine, generate_key
from preprocess_finance_corpus import get_news_data, process_news
import argparse
import argcomplete
from colored import Fore, Style
import requests
import base64
import LSSS
from Crypto.Util.number import getPrime
from save_shares import save_dealer_sgx, save_index_key_shares


class FinanceDataSetSearchEngine(EncryptedSearchEngine):
    def __init__(self, file_key, index_key, dataset_path, threshold=10):
        super().__init__(file_key, index_key, dataset_path, threshold)

    def load_documents(self):
        news_df = get_news_data(self.dataset_path)
        corpus = process_news(news_df)
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
    parser.add_argument(
        "--keyword", type=str, required=True, help="Search keyword to look up"
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # 创建加密引擎
    file_key = generate_key()
    index_key = generate_key()
    engine = FinanceDataSetSearchEngine(
        file_key=file_key,
        index_key=index_key,
        dataset_path=args.company_name,
        threshold=args.threshold,
    )
    engine.process_whole_document_set()

    # 使用LSSS库拆分index_key
    dealer, index_key_shares = LSSS.setup_secret_sharing(
        prime=getPrime(256),
        secrets=[int.from_bytes(index_key)],
        n_data_users=args.user_count,
    )

    # store all users and SGX's index_key_shares in a file
    save_index_key_shares(index_key_shares)
    save_dealer_sgx(dealer)

    # dump index to a file
    engine.dump_index("index.bin")

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
