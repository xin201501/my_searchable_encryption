import pytest
import my
from sort_enc_result import sort_enc_result


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
    result = sort_enc_result(encrypted_data, "test_key")

    assert result == [(8, 1003), (5, 1001), (3, 1002)], "应该按tf降序排列"
    assert mock_decryption.call_count == 6  # 3个元素*2个字段


# 边界条件测试
def test_empty_list(mock_decryption):
    assert sort_enc_result([], "key") == []
    assert mock_decryption.call_count == 0


def test_single_element(mock_decryption):
    encrypted = [("enc_tf", "enc_doc")]
    assert sort_enc_result(encrypted, "key") == [(10041, 1004)]


# 异常处理测试
def test_invalid_decryption():
    encrypted = [("bad_tf", "valid_doc")]
    with pytest.raises(ValueError):
        sort_enc_result(encrypted, "invalid_key")


# 参数化测试多种情况
@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            [("enc_tf_A", "enc_doc1"), ("enc_tf_C", "enc_doc3")],
            [(8, 1003), (5, 1001)],
        ),  # 根据新mock数据调整期望值
    ],
)
def test_parametrized_cases(input_data, expected, mock_decryption):
    assert sort_enc_result(input_data, "test_key") == expected
