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
    n_participants = 3
    access_structures = [[[1, 3], [2, 3]], [[1, 2, 3]], [[1, 2, 3]]]

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
