import pydantic
import pytest
from unittest.mock import mock_open, call
from save_shares import save_index_key_shares


@pytest.fixture
def valid_input():
    """标准有效输入数据"""
    return [{(0, 0): b"1"}, {(0, 1): b"2"}, {(1, 0): b"3"}]


def test_normal_case(mocker, valid_input):
    """测试正常多用户场景"""
    # Mock 文件操作
    mock_file = mocker.patch("builtins.open", mock_open())
    mock_pickle = mocker.patch("pickle.dump")

    save_index_key_shares(valid_input)

    # 验证文件创建数量
    assert mock_file.call_count == 3

    # 验证文件名格式
    expected_files = [
        call("index_key_shares_user_1.bin", "wb"),
        call("index_key_shares_user_2.bin", "wb"),
        call("index_key_shares_sgx.bin", "wb"),
    ]
    mock_file.assert_has_calls(expected_files, any_order=True)

    # 验证序列化内容
    expected_pickle = [call(d, mock_file()) for d in valid_input]
    mock_pickle.assert_has_calls(expected_pickle)


def test_sgx_only_case(mocker):
    """测试仅SGX场景"""
    mocker.patch("builtins.open", mock_open())
    mock_pickle = mocker.patch("pickle.dump")

    input_data = [{(1, 0): b"3"}]
    save_index_key_shares(input_data)

    # 验证用户文件未生成
    assert not any("user_1" in str(c) for c in mock_open().mock_calls)

    # 验证SGX文件
    mock_pickle.assert_called_once_with(
        input_data[-1], open("index_key_shares_sgx.bin", "wb")
    )


def test_empty_list_case():
    """测试空列表异常场景"""
    with pytest.raises(pydantic.ValidationError):
        save_index_key_shares([])


@pytest.mark.parametrize(
    "invalid_input",
    [
        [{(0, 0): 1}],  # 列表不是bytes
        [b"1"],  # 无secret number和group number
    ],
)
def test_invalid_data_type(mocker, invalid_input):
    """参数化测试非字典类型元素"""
    mocker.patch("builtins.open", mock_open())

    with pytest.raises(pydantic.ValidationError):
        save_index_key_shares(invalid_input)
