import argparse
import base64
import pickle
from colored import Fore, Style
import requests
import re

DEFAULT_SEARCH_URL = "http://127.0.0.1:8001/search"
DEFAULT_GET_FILE_URL = "http://127.0.0.1:8001/get_file"
if __name__ == "__main__":
    with open("index_key_shares_user_1.bin", "rb") as f:
        key_shares: dict[tuple[int, int], bytes] = pickle.load(f)

    index_key_shares_base64 = base64.b64encode(key_shares.get((0, 0))).decode("utf-8")
    file_key_shares_base64 = base64.b64encode(key_shares.get((1, 0))).decode("utf-8")

    parser = argparse.ArgumentParser(description="Data User CLI")
    parser.add_argument(
        "--keyword", type=str, required=True, help="Search keyword to look up"
    )
    args = parser.parse_args()

    payload = {
        "pseudo_shares_base64": index_key_shares_base64,
        "secret_num": 0,
        "group_num": 0,
        "query_keyword": args.keyword,
    }
    #  发送HTTP请求
    response = requests.post(DEFAULT_SEARCH_URL, json=payload)

    sorted_results = response.json()["sorted_results"]
    for tf_str, doc_id_str in sorted_results:
        tf = int(tf_str)
        doc_id = int(doc_id_str)
        print(
            f"Keyword appears {Fore.red}{tf}{Style.reset} times in document {Fore.green}{doc_id}{Style.reset}"
        )
        # 获取文件
        get_file_payload = {
            "file_id": doc_id,
            "file_key_share": file_key_shares_base64,
            "secret_num": 1,
            "group_num": 0,
        }
        get_file_response = requests.post(DEFAULT_GET_FILE_URL, json=get_file_payload)
        file_content: str = get_file_response.json()["file_data"]
        # 高亮显示
        hightlighted_content = re.sub(
            f"\\b{args.keyword}\\b",
            f"{Fore.red}{args.keyword}{Style.reset}",
            file_content,
            flags=re.IGNORECASE,
        )
        print(f"{Fore.green}File content: \n{Style.reset}", hightlighted_content)
