import base64
import sys
import requests
import json

if "../multi-secret-sharing/python" not in sys.path:
    sys.path.append("../multi-secret-sharing/python")
import multisecret.MultiSecretRoyAdhikari

url = "http://localhost:8004/combine-secret/"


def combine_secret_request(
    dealer,
    pseudo_shares: list[int],
    secret_num: int,
    group_num: int,
):
    # dealer_str = base64.b64encode(dealer.to_bytes()).decode("utf-8")
    # 构造请求体
    payload = {
        "dealer": dealer,
        "pseudo_shares": pseudo_shares,  # 替换实际伪份额数据
        "secret_num": secret_num,  # 要恢复的秘密索引
        "group_num": group_num,  # 访问结构组索引
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()
    # print("Recovered secret:", response.json()["secret"])
    return response.json()["secret"]
