import base64
import pickle
from colored import Fore, Style
import requests

DEFAULT_URL = "http://127.0.0.1:8001/search"
if __name__ == "__main__":
    with open("index_key_shares_user_1.bin", "rb") as f:
        index_key_shares: dict[tuple[int, int], bytes] = pickle.load(f)

    index_key_shares_base64 = base64.b64encode(index_key_shares.get((0, 0))).decode("utf-8")
    query_keyword = "computing"
    payload = {
        "pseudo_shares_base64": index_key_shares_base64,
        "secret_num": 0,
        "group_num": 0,
        "query_keyword": query_keyword,
    }
    #  发送HTTP请求
    response = requests.post(DEFAULT_URL, json=payload)

    sorted_results = response.json()["sorted_results"]
    for tf_str, doc_id_str in sorted_results:
        tf = int(tf_str)
        doc_id = int(doc_id_str)
        print(
            f"Keyword appears {Fore.red}{tf}{Style.reset} times in document {Fore.green}{doc_id}{Style.reset}"
        )
