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
