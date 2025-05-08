import secrets

# 使用multisecret库分割密钥
import sys

sys.path.append("../multi-secret-sharing/python")
import multisecret.MultiSecretRoyAdhikari

from Crypto.Util.number import getPrime

if __name__ == "__main__":

    """This example shows how to use high level secret splitting functionality"""

    prime = getPrime(256)

    # 随机生成一个128位密钥
    key = secrets.randbits(128)

    # multi secret sharing parameters
    secret_list = [key, 313, 501]
    n_participants = 11  # 10 data user and one SGX
    # 假设有10个用户和一个SGX，任意一个用户和SGX可以访问所有密钥
    # 用户编号1-10，SGX编号11
    # 访问结构：
    # 用户 OR SGX
    # (1 OR 2 OR 3 OR 4 OR 5 OR 6 OR 7 OR 8 OR 9 OR 10) AND (11)
    access_structures = [[], [], []]
    for i in range(n_participants - 1):
        access_structures[0].append([i + 1, n_participants])

    # 第2和第3个秘密的访问结构暂时任意
    access_structures[1] = [[1, 3, 11], [5, 11]]
    access_structures[2] = [[2, 4, 11], [6, 11], [8, 9, 10, 11]]

    # initialize Roy-Adhikari secret sharing algorithm
    dealer = multisecret.MultiSecretRoyAdhikari.Dealer(
        prime, n_participants, secret_list, access_structures
    )
    pseudo_shares = dealer.split_secrets()

    # Combine first secret for its first access group
    secret_num = 0
    group_num = 0
    combined = dealer.combine_secret(
        secret_num, group_num, pseudo_shares[secret_num][group_num]
    )

    assert combined == secret_list[secret_num]
    print("Combined secret: ", combined)
    print("Is secret correct: ", key == combined)


def setup_secret_sharing(
    prime, secrets, n_data_users=10, custom_access_structures=None
):
    """
    初始化多秘密共享方案

    参数：
    prime - 大质数
    secrets - 秘密值列表（至少包含一个秘密）
    n_data_users - 数据用户数量（默认10）
    custom_access_structures - 自定义访问结构（从第二个秘密开始）

    返回：
    dealer, pseudo_shares 元组
    """
    if secrets is None or len(secrets) == 0:
        raise ValueError("Secrets list cannot be empty")
    if custom_access_structures and len(custom_access_structures) != len(secrets) - 1:
        raise ValueError("Custom access structures must match the number of secrets")

    n_participants = n_data_users + 1  # 数据用户 + SGX
    sgx_id = n_participants  # SGX固定为最后一个参与者

    # 初始化访问结构
    access_structures = []

    # 第一个秘密的访问结构：(任意用户) AND SGX
    first_secret_access_structure = []
    for user_id in range(1, n_data_users + 1):
        first_secret_access_structure.append([user_id, sgx_id])
    access_structures.append(first_secret_access_structure)

    # 处理后续秘密的访问结构
    if custom_access_structures:
        for structure in custom_access_structures:
            access_structures.append(structure)

    # 创建分发者并分割秘密
    dealer = multisecret.MultiSecretRoyAdhikari.Dealer(
        p=prime,
        n_participants=n_participants,
        s_secrets=secrets,
        access_structures=access_structures,
    )
    pseudo_shares = dealer.split_secrets()

    return dealer, pseudo_shares
