import base64
from contextlib import asynccontextmanager
import pickle
from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

DEFAULT_INDEX_PATH = "./index.bin"


class Token(BaseModel):
    token_base64: str = Field(min_length=1)


inverted_index = {}


@asynccontextmanager
async def load_index(app: FastAPI):
    try:
        index: dict[bytes, list] = pickle.load(open(DEFAULT_INDEX_PATH, "rb"))
        inverted_index.update(index)
    except:
        pass
    
    yield

    inverted_index.clear()


app = FastAPI(lifespan=load_index)


@app.post("/search_server")
async def search_server(token_base64: Token):
    # 将token从base64解码
    token = base64.b64decode(token_base64.token_base64)
    # 读取index
    try:
        # 得到结果，序列化后返回
        result = inverted_index.get(token)
        result_bytes = pickle.dumps(result)
        result_bytes_base64 = base64.b64encode(result_bytes)
        return {"results": result_bytes_base64}
    # 捕获文件打开错误
    except FileNotFoundError:
        return {"results": []}


@app.post("get_file")
async def get_file(file_id: int):
    try:
        with open(f"encrypted_docs_finance/doc_{file_id}", "rb") as f:
            file_data = f.read()
        file_data_base64 = base64.b64encode(file_data).decode("utf-8")
        return {"file_data_base64": file_data_base64}
    except FileNotFoundError:
        return {"file_data_base64": None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
