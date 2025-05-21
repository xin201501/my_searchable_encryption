# 此文件用于恢复加密索引的密钥
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic import Field
import pickle
import LSSS

import sys

if "../multi-secret-sharing/python" not in sys.path:
    sys.path.append("../multi-secret-sharing/python")
if "/root/multi-secret-sharing/python" not in sys.path:
    sys.path.append("/root/multi-secret-sharing/python")


def decode_dealer_base64(base64str):
    dealer_binary = base64.b64decode(base64str)
    dealer_obj = pickle.loads(dealer_binary)
    return dealer_obj


class CombineRequest(BaseModel):
    # 伪份额列表（需根据实际结构定义更详细的模型）
    # 默认恢复第一个秘密
    # 默认使用第一个访问结构组
    pseudo_shares: list[int]
    secret_num: int = Field(strict=True, ge=0)
    group_num: int = Field(strict=True, ge=0)


app = FastAPI()


@app.post("/combine-secret/")
async def combine_secret(request: CombineRequest):
    """
    组合秘密接口

    参数：
    - pseudo_shares: 伪份额的嵌套列表结构（示例：[[[share1], [share2]], ...]）
    - secret_num: 要恢复的秘密索引（从0开始）
    - group_num: 访问结构组索引（从0开始）
    """

    try:
        # 注意：实际使用时需要从持久化存储获取dealer
        f = open("dealer_sgx.bin", "rb")
        dealer = pickle.load(f)
        result = LSSS.combine_secret_from_shares(
            dealer=dealer,
            pseudo_shares=request.pseudo_shares,
            secret_num=request.secret_num,
            group_num=request.group_num,
        )
        return {"secret": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
