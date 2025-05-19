import base64
from fastapi import FastAPI
from pydantic import BaseModel, Field
import requests
import LSSS
import pickle

from encrypt_keyword import symmetric_encryption_for_keyword
from sort_enc_result import sort_enc_result


class QueryRequest(BaseModel):
    # 伪份额列表（需根据实际结构定义更详细的模型）
    # 默认恢复第一个秘密
    # 默认使用第一个访问结构组
    pseudo_shares_base64: str = Field(min_length=1)
    secret_num: int = Field(strict=True, ge=0)
    group_num: int = Field(strict=True, ge=0)
    query_keyword: str


def combine_secret(pseudo_shares: list[int], secret_num: int, group_num: int):
    """组合秘密分片生成完整密钥（示例实现）

    注意：实际使用时需要从持久化存储获取dealer"""
    f = open("dealer_sgx.bin", "rb")
    dealer = pickle.load(f)
    result = LSSS.combine_secret_from_shares(
        dealer=dealer,
        pseudo_shares=pseudo_shares,
        secret_num=secret_num,
        group_num=group_num,
    )
    return result


def generate_token(index_key, query_keyword):
    """生成令牌"""
    query_keyword_enc = symmetric_encryption_for_keyword(index_key, query_keyword)
    return query_keyword_enc


def search_encrypted_index_request(token: bytes) -> str:
    """服务器端搜索"""
    payload = {"token_base64": base64.b64encode(token).decode("utf-8")}
    try:
        response = requests.post(
            url="http://localhost:8004/search_server",
            json=payload,
        )
        response.raise_for_status()  # 如果响应状态码不是2xx，则引发异常
        tf_enc_and_doc_id_enc_structs = response.json()["results"]
        return tf_enc_and_doc_id_enc_structs
    except requests.exceptions.RequestException:
        raise Exception(f"Error: Failed to send HTTP request to Cloud.")


app = FastAPI()


@app.post("/search")
async def handle_search_request(request: QueryRequest):
    """请求处理主函数"""
    try:
        pseudo_shares_user = base64.b64decode(request.pseudo_shares_base64)
        with open("index_key_shares_sgx.bin", "rb") as f:
            pseudo_shares_sgx = pickle.load(f)

        pseudo_shares = [
            pseudo_shares_user,
            pseudo_shares_sgx.get((request.secret_num, request.group_num)),
        ]

        # 1. 组合密钥
        index_key: bytes = combine_secret(
            pseudo_shares, request.secret_num, request.group_num
        ).to_bytes(16)

        # 2. 生成令牌
        token = generate_token(index_key, request.query_keyword)

        # 3. 服务器端搜索（示例调用）
        search_results_base64 = search_encrypted_index_request(token)
        search_results = pickle.loads(base64.b64decode(search_results_base64))

        # 5. 排序后返回
        return {
            "sorted_results": sort_enc_result(search_results, index_key),
        }

    except Exception as e:
        # 添加具体的异常处理逻辑
        raise RuntimeError(f"Search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")
