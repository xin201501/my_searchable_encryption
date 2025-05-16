import pytest
from unittest.mock import call
from my import EncryptedSearchEngine  # 注意这里直接导入被mock的函数
import encrypt_keyword


@pytest.fixture
def search_engine(mocker):
    """测试固件：初始化加密搜索引擎实例"""
    engine = EncryptedSearchEngine(
        file_key="test_key", index_key="test_key", dataset_path="/dev/null", threshold=0
    )
    mocker.patch(
        "encrypt_keyword.symmetric_encryption_for_keyword"
    )  # 正确mock模块级函数
    encrypt_keyword.symmetric_encryption_for_keyword.side_effect = (
        lambda _, x: f"enc_{x}"
    )
    return engine


class TestBuildInvertedIndex:
    def test_empty_documents(self, search_engine):
        """场景1: 空文档集合时索引保持为空"""
        # When
        search_engine._EncryptedSearchEngine__choose_out_keyword()
        search_engine._EncryptedSearchEngine__build_inverted_index()

        # Then
        assert not search_engine._EncryptedSearchEngine__inverted_index
        encrypt_keyword.symmetric_encryption_for_keyword.assert_not_called()  # 直接使用被mock的函数

    def test_single_document_single_word(self, search_engine):
        """场景2: 单文档单关键词生成正确索引结构"""
        # Given
        search_engine._EncryptedSearchEngine__word_appearance_time_per_doc = {
            1: {"apple": 3}
        }
        search_engine._EncryptedSearchEngine__words_appearance_time = {"apple": 3}
        encrypt_keyword.symmetric_encryption_for_keyword.side_effect = (
            lambda _, x: f"enc_{x}"
        )  # 直接配置mock

        # When
        search_engine._EncryptedSearchEngine__build_inverted_index()

        # Then
        expected_calls = [
            call("test_key", "apple"),
            call("test_key", "3"),
            call("test_key", "1"),
        ]
        encrypt_keyword.symmetric_encryption_for_keyword.assert_has_calls(
            expected_calls, any_order=True
        )
        assert search_engine._EncryptedSearchEngine__inverted_index["enc_apple"] == [
            ("enc_3", "enc_1")
        ]

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            (
                {1: {"apple": 3}, 2: {"apple": 5}},
                [("enc_3", "enc_1"), ("enc_5", "enc_2")],
            ),
            ({1: {"a": 1}, 3: {"a": 2}}, [("enc_1", "enc_1"), ("enc_2", "enc_3")]),
        ],
        ids=["多文档相同词", "不同文档相同词"],
    )
    def test_multiple_docs_same_word(self, search_engine, test_input, expected):
        """场景3: 多文档共享关键词时聚合结果验证"""
        # Given
        search_engine._EncryptedSearchEngine__word_appearance_time_per_doc = test_input
        search_engine._EncryptedSearchEngine__count_keyword_appearance()
        # my.symmetric_encryption_for_keyword.side_effect = lambda _, x: f"enc_{x}"

        # When
        search_engine._EncryptedSearchEngine__build_inverted_index()

        # Then
        # 正确获取第一个字典的键
        first_inner_dict = next(iter(test_input.values()))  # 获取第一个文档的词频字典
        first_key = next(iter(first_inner_dict.keys()))  # 获取该字典的第一个键
        key = f"enc_{first_key}"
        assert sorted(
            search_engine._EncryptedSearchEngine__inverted_index[key]
        ) == sorted(expected)

    def test_parameter_conversion(self, search_engine):
        """场景4: 验证数字型参数转换为字符串"""
        # Given
        search_engine._EncryptedSearchEngine__word_appearance_time_per_doc = {
            1001: {"python": 10}
        }
        search_engine._EncryptedSearchEngine__words_appearance_time = {"python": 10}
        # my.symmetric_encryption_for_keyword.return_value = "encrypted"

        # When

        search_engine._EncryptedSearchEngine__build_inverted_index()

        # Then
        expected_params = ["python", "10", "1001"]
        assert expected_params == [
            args[0][1]
            for args in encrypt_keyword.symmetric_encryption_for_keyword.call_args_list
        ]

    def test_single_doc_with_words_less_than_threshold(self, search_engine):
        """场景5: 单文档关键词数量低于阈值时索引保持为空"""
        # Given
        search_engine._EncryptedSearchEngine__word_appearance_time_per_doc = {
            1: {"apple": 3}
        }
        search_engine._EncryptedSearchEngine__words_appearance_time = {"apple": 3}
        search_engine._EncryptedSearchEngine__threshold = 4

        # When
        search_engine._EncryptedSearchEngine__build_inverted_index()

        # Then
        assert not search_engine._EncryptedSearchEngine__inverted_index
