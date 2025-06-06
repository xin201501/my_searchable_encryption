import base64
import encrypt_keyword
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


def sort_enc_result(enc_result_list, index_key):
    # 先解密enc_result_list
    plain_result_list = []
    for enc_result in enc_result_list:
        plain_tf_str = encrypt_keyword.symmetric_decryption_for_keyword(
            index_key, enc_result[0]
        )
        plain_doc_id_str = encrypt_keyword.symmetric_decryption_for_keyword(
            index_key, enc_result[1]
        )
        plain_tf = int(plain_tf_str)
        plain_doc_id = int(plain_doc_id_str)
        plain_result = (plain_tf, plain_doc_id)
        plain_result_list.append(plain_result)
        # 对plain_result_list按照tf进行排序
    plain_result_list.sort(key=lambda x: x[0], reverse=True)
    return plain_result_list


app = FastAPI()


class SortRequest(BaseModel):
    encrypted_results: list[tuple[str, str]]  # (加密tf, 加密docid)元组列表
    index_key: str  # 解密用的密钥


@app.post("/sort-encrypted-results")
async def sort_encrypted_results(request: SortRequest):
    try:
        decoded_results = [
            (base64.b64decode(count_b64), base64.b64decode(doc_id_b64))
            for count_b64, doc_id_b64 in request.encrypted_results
        ]
        decoded_index_key = base64.b64decode(request.index_key)
        # 直接使用已有的排序函数
        sorted_results = sort_enc_result(
            enc_result_list=decoded_results, index_key=decoded_index_key
        )
        return {"sorted_results": sorted_results}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Decryption or sorting failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
