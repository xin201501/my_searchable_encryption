import pytest
from unittest.mock import MagicMock
from LSSS import combine_secret_from_shares


class TestCombineSecretFromShares:
    @pytest.fixture
    def mock_dealer(self):
        """为所有测试用例提供干净的 mock dealer"""
        return MagicMock()

    # 正常场景参数化测试
    @pytest.mark.parametrize(
        "secret_num, group_num, expected_call",
        [(0, 0, (0, 0, ["share_data"])), (1, 2, (1, 2, ["share3"]))],
    )
    def test_normal_combination(
        self, mock_dealer, secret_num, group_num, expected_call
    ):
        """验证不同合法索引组合的正确调用"""
        # 配置伪份额结构
        pseudo_shares = [[["share_data"]], [["share1"], ["share2"], ["share3"]]]

        mock_dealer.combine_secret.return_value = 100
        result = combine_secret_from_shares(
            mock_dealer, pseudo_shares, secret_num, group_num
        )

        mock_dealer.combine_secret.assert_called_once_with(*expected_call)
        assert result == 100

    # 异常场景参数化测试
    @pytest.mark.parametrize(
        "secret_num, group_num, expected_error",
        [
            (2, 0, IndexError),  # 超出secret范围
            (0, 3, IndexError),  # 超出group范围
            (0, 0, ValueError),  # dealer方法异常
        ],
    )
    def test_error_conditions(self, mock_dealer, secret_num, group_num, expected_error):
        """验证不同异常场景"""
        pseudo_shares = [[["s0g0"], ["s0g1"], ["s0g2"]], [["s1g0"]]]

        if expected_error == ValueError:
            mock_dealer.combine_secret.side_effect = ValueError("Invalid shares")
        else:
            mock_dealer.combine_secret.return_value = 100  # 正常返回

        with pytest.raises(expected_error) as exc_info:
            combine_secret_from_shares(
                mock_dealer, pseudo_shares, secret_num, group_num
            )

        if expected_error == ValueError:
            assert "Invalid shares" in str(exc_info.value)
            mock_dealer.combine_secret.assert_called_once()
        else:
            mock_dealer.combine_secret.assert_not_called()
