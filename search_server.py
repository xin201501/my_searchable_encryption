import base64
import pickle
from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

DEFAULT_INDEX_PATH = "./index.bin"


class Token(BaseModel):
    token_base64: str = Field(min_length=1)


app = FastAPI()


@app.post("/search_server")
async def search_server(token_base64: Token):
    # 将token从base64解码
    token = base64.b64decode(token_base64.token_base64)
    # 读取index
    try:
        index: dict[bytes, list] = pickle.load(open(DEFAULT_INDEX_PATH, "rb"))
        # 得到结果，序列化后返回
        result = index.get(token)
        result_bytes = pickle.dumps(result)
        result_bytes_base64 = base64.b64encode(result_bytes)
        return {"results": result_bytes_base64}
    # 捕获文件打开错误
    except FileNotFoundError:
        return {"results": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)