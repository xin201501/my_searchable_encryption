from pydantic import ValidationError
import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from recover_key import combine_secret, CombineRequest  # 假设模型定义在models模块


@patch("recover_key.decode_dealer_base64")
@patch("LSSS.combine_secret_from_shares")
async def test_combine_secret_success(mock_combine, mock_decode):
    """TC01: 正常参数组合测试"""
    # 构造测试数据
    mock_request = CombineRequest(
        dealer_base64="base64_string",
        pseudo_shares=[2, 3],
        secret_num=0,
        group_num=0,
    )

    # 设置mock返回值
    mock_dealer = MagicMock()
    mock_decode.return_value = mock_dealer
    mock_combine.return_value = b"recovered_secret"

    # 执行测试
    result = await combine_secret(mock_request)

    # 验证结果
    assert result == {"secret": b"recovered_secret"}
    mock_decode.assert_called_once_with("base64_string")
    mock_combine.assert_called_once_with(
        dealer=mock_dealer,
        pseudo_shares=[2, 3],
        secret_num=0,
        group_num=0,
    )


@patch("recover_key.decode_dealer_base64")
async def test_combine_secret_decode_error(mock_decode):
    """TC02: decode_dealer_base64异常测试"""
    # 构造异常情况
    mock_request = CombineRequest(
        dealer_base64="invalid_base64",
        pseudo_shares=[2, 3],
        secret_num=0,
        group_num=0,
    )

    # 设置抛出异常
    mock_decode.side_effect = Exception("Decode error")

    # 执行测试并验证异常
    with pytest.raises(HTTPException) as exc_info:
        await combine_secret(mock_request)

    assert exc_info.value.status_code == 400
    assert "Decode error" in str(exc_info.value.detail)


@patch("recover_key.decode_dealer_base64")
@patch("LSSS.combine_secret_from_shares")
async def test_combine_secret_lsss_error(mock_combine, mock_decode):
    """TC03: LSSS组合失败测试"""
    # 构造测试数据
    mock_request = CombineRequest(
        dealer_base64="base64_string",
        pseudo_shares=[1, 3],
        secret_num=0,
        group_num=0,
    )

    # 设置mock对象
    mock_dealer = MagicMock()
    mock_decode.return_value = mock_dealer
    mock_combine.side_effect = Exception("LSSS error")

    # 执行测试并验证异常
    with pytest.raises(HTTPException) as exc_info:
        await combine_secret(mock_request)

    assert exc_info.value.status_code == 400
    assert "LSSS error" in str(exc_info.value.detail)


async def test_combine_secret_invalid_secret_num():
    """TC04: secret_num为负数测试"""
    # 构造非法参数
    with pytest.raises(ValidationError) as exc_info:
        mock_request = CombineRequest(
            dealer_base64="base64_string",
            pseudo_shares=[2, 3],
            secret_num=-1,  # 无效索引
            group_num=0,
        )

    assert "Input should be greater than or equal to 0" in str(exc_info.value)


async def test_combine_secret_invalid_group_num():
    """TC05: group_num为负数测试"""
    # 构造非法参数
    # 构造非法参数
    with pytest.raises(ValidationError) as exc_info:
        mock_request = CombineRequest(
            dealer_base64="base64_string",
            pseudo_shares=[2, 3],
            secret_num=0,
            group_num=-1,  # 无效索引
        )

    assert "Input should be greater than or equal to 0" in str(exc_info.value)
