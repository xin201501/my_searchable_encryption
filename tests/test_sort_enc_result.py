import base64
import pytest
from fastapi import HTTPException
from unittest.mock import patch
from sort_enc_result import sort_encrypted_results, SortRequest
import sort_enc_result
from pydantic import ValidationError


# Mock解密函数（假设密钥为"test_key"时解密逻辑）
@pytest.fixture
def mock_decryption(mocker):
    return mocker.patch(
        "my.symmetric_decryption_for_keyword",
        side_effect=lambda key, val: {
            "enc_tf_A": "5",
            "enc_doc1": "1001",
            "enc_tf_B": "3",
            "enc_doc2": "1002",
            "enc_tf_C": "8",
            "enc_doc3": "1003",
            "enc_tf": "10041",
            "enc_doc": "1004",
        }.get(
            val, "0"
        ),  # 默认返回0避免ValueError
    )


# 正常功能测试
def test_sort_encrypted_results(mock_decryption):
    encrypted_data = [
        ("enc_tf_A", "enc_doc1"),
        ("enc_tf_B", "enc_doc2"),
        ("enc_tf_C", "enc_doc3"),
    ]
    result = sort_enc_result.sort_enc_result(encrypted_data, "test_key")

    assert result == [(8, 1003), (5, 1001), (3, 1002)], "应该按tf降序排列"
    assert mock_decryption.call_count == 6  # 3个元素*2个字段


# 边界条件测试
def test_empty_list(mock_decryption):
    assert sort_enc_result.sort_enc_result([], "key") == []
    assert mock_decryption.call_count == 0


def test_single_element(mock_decryption):
    encrypted = [("enc_tf", "enc_doc")]
    assert sort_enc_result.sort_enc_result(encrypted, "key") == [(10041, 1004)]


# 异常处理测试
def test_invalid_decryption():
    encrypted = [("bad_tf", "valid_doc")]
    with pytest.raises(ValueError):
        sort_enc_result.sort_enc_result(encrypted, "invalid_key")


# 参数化测试多种情况
@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            [("enc_tf_A", "enc_doc1"), ("enc_tf_C", "enc_doc3")],
            [(8, 1003), (5, 1001)],
        ),  # 根据新mock数据调整期望值
        (
            [
                ("enc_tf_B", "enc_doc3"),
                ("enc_tf_A", "enc_doc1"),
                ("enc_tf_C", "enc_doc2"),
            ],
            [(8, 1002), (5, 1001), (3, 1003)],
        ),
    ],
)
def test_parametrized_cases(input_data, expected, mock_decryption):
    assert sort_enc_result.sort_enc_result(input_data, "test_key") == expected


# 测试类封装所有测试用例
class TestSortEncryptedResults:
    @pytest.fixture
    def mock_data(self):
        item1_base64 = base64.b64encode(b"item1").decode("utf-8")
        item2_base64 = base64.b64encode(b"item2").decode("utf-8")
        index_key_base64 = base64.b64encode(b"test_key").decode("utf-8")
        return {
            "encrypted_results": [
                (item1_base64, item2_base64),
            ],
            "index_key": index_key_base64,
        }

    @pytest.mark.asyncio
    @patch("sort_enc_result.sort_enc_result", spec=True)
    async def test_normal_case(self, mock_sort, mock_data):
        """
        测试正常排序流程
        场景：合法请求参数，排序函数返回有效结果
        """
        # Arrange
        mock_sort.return_value = ["sorted_result"]
        item1_base64, item2_base64 = mock_data["encrypted_results"][0]
        index_key_base64 = mock_data["index_key"]
        valid_request = SortRequest(
            encrypted_results=[(item1_base64, item2_base64)], index_key=index_key_base64
        )

        # Act
        response = await sort_encrypted_results(valid_request)

        # Assert
        assert response == {"sorted_results": ["sorted_result"]}
        mock_sort.assert_called_once_with(
            enc_result_list=[(b"item1", b"item2")], index_key=b"test_key"
        )

    @pytest.mark.asyncio
    async def test_invalid_request_structure(self, mock_data):
        """
        测试请求体结构异常
        场景：缺少必填字段index_key
        """
        # 使用非法请求结构（模拟Pydantic验证失败）
        with pytest.raises(ValidationError):
            item1_base64, item2_base64 = mock_data["encrypted_results"][0]
            invalid_request = SortRequest(
                encrypted_results=[(item1_base64, item2_base64)], index_key=None
            )
            await sort_encrypted_results(invalid_request)

    @pytest.mark.asyncio
    @patch("sort_enc_result.sort_enc_result", spec=True)
    async def test_sort_function_failure(self, mock_sort, mock_data):
        """
        测试排序函数内部异常
        场景：sort_enc_result抛出ValueError
        """
        # Arrange
        # 返回被mock的函数的list参数
        mock_sort.side_effect = ValueError("Invalid key format")
        item1_base64, item2_base64 = mock_data["encrypted_results"][0]
        valid_request = SortRequest(
            encrypted_results=[(item1_base64, item2_base64)], index_key="invalid_key"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await sort_encrypted_results(valid_request)

        assert exc_info.value.status_code == 400
        assert "Decryption or sorting failed" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("sort_enc_result.sort_enc_result", spec=True)
    async def test_edge_case_empty_list(self, mock_sort):
        """
        测试边界条件：空加密结果列表
        场景：encrypted_results为空列表
        """
        mock_sort.side_effect = lambda enc_result_list, index_key: enc_result_list
        # 根据业务需求调整断言条件
        request = SortRequest(
            encrypted_results=[],
            index_key=base64.b64encode(b"test_key").decode("utf-8"),
        )
        response = await sort_encrypted_results(request)
        assert response == {"sorted_results": []}
        mock_sort.assert_called_once_with(enc_result_list=[], index_key=b"test_key")
