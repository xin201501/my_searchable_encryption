import pytest
from unittest.mock import Mock, patch
from LSSS import setup_secret_sharing


def test_empty_secrets_raises_error():
    """测试空secrets列表触发异常"""
    with pytest.raises(ValueError, match="Secrets list cannot be empty"):
        setup_secret_sharing(prime=11, secrets=[])


def test_invalid_access_structure_length():
    """测试自定义访问结构数量与secrets不匹配"""
    secrets = [1, 2, 3]
    invalid_structures = [
        [["1:2"]],
        [["3:4"]],
    ]  # 需要2个结构但提供2个（实际需要3-1=2？不，原函数中的条件是len(custom) == len(secrets)-1，此处3个secrets需要2个结构）
    # 如果输入的结构数量是2，那么是符合的，所以这个测试可能需要调整。例如，当secrets长度为3，而custom结构长度为1，则会触发错误。
    # 修改例子：
    invalid_structures = [[["1:2"]]]  # 长度1，而secrets长度3需要2个结构
    with pytest.raises(ValueError, match="Custom access structures must match"):
        setup_secret_sharing(
            prime=11, secrets=secrets, custom_access_structures=invalid_structures
        )


@patch("multisecret.MultiSecretRoyAdhikari.Dealer")
def test_single_secret_default_structure(mock_dealer):
    """测试单秘密默认访问结构生成"""
    # Mock配置
    mock_instance = Mock()
    mock_instance.split_secrets.return_value = "mock_shares"
    mock_dealer.return_value = mock_instance

    # 执行测试
    prime = 97
    secrets = [123]
    dealer, shares = setup_secret_sharing(prime, secrets, n_data_users=3)

    # 验证结构生成
    expected_access = [[[1, 4], [2, 4], [3, 4]]]  # 4=3(data users)+1(SGX)
    mock_dealer.assert_called_once_with(
        p=prime,
        n_participants=4,
        s_secrets=secrets,
        access_structures=expected_access,
    )
    # assert shares == "mock_shares"


@patch("multisecret.MultiSecretRoyAdhikari.Dealer")
def test_custom_access_structures(mock_dealer):
    """测试自定义访问结构拼接"""
    # Mock配置
    mock_instance = Mock()
    mock_instance.split_secrets.return_value = "custom_mock"
    mock_dealer.return_value = mock_instance

    # 测试数据
    prime = 101
    secrets = [10, 20]
    custom_structures = [[[1, 2], [3, 4]]]

    # 执行调用
    setup_secret_sharing(
        prime, secrets, n_data_users=5, custom_access_structures=custom_structures
    )

    # 验证结构合并
    expected_access = [
        [[1, 6], [2, 6], [3, 6], [4, 6], [5, 6]],  # 默认结构
        *custom_structures,  # 自定义结构
    ]
    mock_dealer.assert_called_once_with(
        p=101,
        n_participants=6,  # 5+1
        s_secrets=[10, 20],
        access_structures=expected_access,
    )


@patch("multisecret.MultiSecretRoyAdhikari.Dealer")
def test_default_n_data_users(mock_dealer):
    from unittest import mock

    """测试默认数据用户数量"""
    setup_secret_sharing(prime=11, secrets=[99])
    mock_dealer.assert_called_once_with(
        p=11,
        n_participants=11,  # 默认10+1
        s_secrets=[99],
        access_structures=[
            [
                [1, 11],
                [2, 11],
                [3, 11],
                [4, 11],
                [5, 11],
                [6, 11],
                [7, 11],
                [8, 11],
                [9, 11],
                [10, 11],
            ]
        ],
    )
