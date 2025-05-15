import pickle
from pydantic import BaseModel, Field


class IndexKeyShares(BaseModel):
    shares: list[int] = Field(min_length=1)


def save_index_key_shares(index_key_shares: list[int]):
    """
    将LSSS生成的密钥分片序列化到二进制文件

    参数：
        index_key_shares (list): 多层嵌套的密钥分片结构，包含：
            [0--len(index_key_shares)-1] - 用户id为X的分片字典
            [最后一项] - SGX节点的分片字典

    生成文件：
        index_key_shares_user_x.bin - 用户X的(0,0)分片
        index_key_shares_sgx.bin   - SGX节点的分片
    """
    IndexKeyShares(shares=index_key_shares)
    for i in range(len(index_key_shares) - 1):
        with open("index_key_shares_user_%d.bin" % (i + 1), "wb") as f:
            pickle.dump(index_key_shares[i], f)

    with open("index_key_shares_sgx.bin", "wb") as f:
        pickle.dump(index_key_shares[-1], f)


def save_dealer_sgx(dealer):
    with open("dealer_sgx.bin", "wb") as f:
        pickle.dump(dealer, f)
