import base64
import pytest
import json
import requests
import pickle
from unittest.mock import MagicMock

import sys

# 如果模块不在当前目录，请将模块路径添加到 sys.path 中
if "../multi-secret-sharing/python" not in sys.path:
    sys.path.append("../multi-secret-sharing/python")

from recover_key_http_request import combine_secret_request  # 替换实际模块路径

url = "http://localhost:8004/combine-secret/"


@pytest.fixture
def mock_requests_post(mocker):
    """模拟 requests.post 的 fixture"""
    return mocker.patch("recover_key_http_request.requests.post")


# 配置可序列化的 mock dealer
class MockDealer:
    def __init__(self):
        self.p = 2**256 - 2**32 - 2**4 + 2**12 + 2**9 + 1
        self.n_participants = 10
        self.s_secrets = [1, 2, 6]
        self.access_structures = [[[5, 7], [6]], [[1]], [[2, 3], [2, 5, 8]]]

    def to_dict(self):
        """将对象转换为可序列化字典"""
        return {
            "p": self.p,
            "n_participants": self.n_participants,
            "s_secrets": self.s_secrets,
            "access_structures": self.access_structures,
        }


def test_successful_request(mock_requests_post):
    """测试正常响应流程 (TC1)"""
    # 配置模拟响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"secret": 1}
    mock_requests_post.return_value = mock_response

    # 执行测试
    test_dealer = MockDealer()  # 替换实际 dealer 类型
    test_dealer_binary = pickle.dumps(test_dealer)
    test_dealer_base64 = base64.b64encode(test_dealer_binary).decode("utf-8")
    test_shares = [[1, 2], [3, 4]]
    test_secret_num = 0
    test_group_num = 0
    combine_secret_request(
        test_dealer_base64, test_shares, test_secret_num, test_group_num
    )

    # 验证请求构造
    expected_payload = {
        "dealer": test_dealer_base64,  # 调用序列化方法
        "pseudo_shares": test_shares,
        "secret_num": 0,
        "group_num": 0,
    }

    mock_requests_post.assert_called_once_with(
        url,  # 替换实际 URL
        data=json.dumps(expected_payload),
        headers={"Content-Type": "application/json"},
    )


def test_http_error(mock_requests_post):
    """测试 HTTP 错误处理 (TC2)"""
    # 配置错误响应
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid parameters"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "400 Client Error"
    )
    mock_requests_post.return_value = mock_response

    # 初始化测试数据
    test_dealer = MockDealer()
    test_dealer_binary = pickle.dumps(test_dealer)
    test_dealer_base64 = base64.b64encode(test_dealer_binary).decode("utf-8")
    test_shares = [[1, 2], [3, 4]]  # 使用有效 shares 以触发请求
    test_secret_num = 0
    test_group_num = 0

    # 验证异常是否被正确抛出
    with pytest.raises(Exception) as e:
        combine_secret_request(
            test_dealer_base64, test_shares, test_secret_num, test_group_num
        )
        assert "HTTP Error:" in str(e.value)
        assert "400 Client Error" in str(e.value)

    # 可选：验证请求是否按预期构造
    expected_payload = {
        "dealer": test_dealer_base64,
        "pseudo_shares": test_shares,
        "secret_num": test_secret_num,
        "group_num": test_group_num,
    }
    mock_requests_post.assert_called_once_with(
        url,
        data=json.dumps(expected_payload),
        headers={"Content-Type": "application/json"},
    )


def test_request_exception(mock_requests_post):
    """测试网络异常处理 (TC3)"""
    # 配置模拟异常
    mock_requests_post.side_effect = requests.exceptions.ConnectionError(
        "Connection failed"
    )

    # 准备测试数据
    test_dealer = MockDealer()
    test_dealer_binary = pickle.dumps(test_dealer)
    test_dealer_base64 = base64.b64encode(test_dealer_binary).decode("utf-8")
    test_shares = [[1, 2], [3, 4]]  # 使用非空 shares
    test_secret_num = 0
    test_group_num = 0

    # 执行函数并验证异常
    with pytest.raises(requests.exceptions.ConnectionError) as e:
        combine_secret_request(
            test_dealer_base64, test_shares, test_secret_num, test_group_num
        )
        assert "Connection failed" in str(e)

    # 可选：验证请求是否被正确调用
    expected_payload = {
        "dealer": test_dealer_base64,
        "pseudo_shares": test_shares,
        "secret_num": test_secret_num,
        "group_num": test_group_num,
    }
    mock_requests_post.assert_called_once_with(
        url,
        data=json.dumps(expected_payload),
        headers={"Content-Type": "application/json"},
    )
