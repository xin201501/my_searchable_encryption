import pytest
from collections import defaultdict
from my import EncryptedSearchEngine


class TestEncryptedSearchEngine:
    """测试加密搜索引擎的关键词统计功能"""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        """初始化测试环境夹具"""
        # 创建被测类实例
        self.engine = EncryptedSearchEngine(
            file_key="file_key", index_key="index_key", dataset_path="/dev/null"
        )
        # 反射设置初始状态（pytest支持直接访问私有属性）
        self.engine._EncryptedSearchEngine__word_appearance_time_per_doc = {}
        self.engine._EncryptedSearchEngine__words_appearance_time = defaultdict(int)

    def test_empty_documents(self):
        """场景1: 空文档集合验证"""
        self.engine._EncryptedSearchEngine__count_keyword_appearance()
        assert self.engine._EncryptedSearchEngine__words_appearance_time == defaultdict(
            int
        )

    def test_single_document(self):
        """场景2: 单个文档词频统计"""
        # 设置测试数据
        self.engine._EncryptedSearchEngine__word_appearance_time_per_doc = {
            "doc1": {"python": 3, "java": 2}
        }
        self.engine._EncryptedSearchEngine__count_keyword_appearance()
        # 验证统计结果
        assert dict(self.engine._EncryptedSearchEngine__words_appearance_time) == {
            "python": 3,
            "java": 2,
        }

    @pytest.mark.parametrize(
        "input_data,expected",
        [
            ({"doc1": {"a": 2}, "doc2": {"a": 1}}, {"a": 3}),
            ({"doc1": {"a": 0}, "doc2": {"b": 0}}, {"a": 0, "b": 0}),
            ({"doc1": {"a": 2}, "doc2": {"b": 3}}, {"a": 2, "b": 3}),
        ],
    )
    def test_multiple_scenarios(self, input_data, expected):
        """参数化测试多场景验证"""
        self.engine._EncryptedSearchEngine__word_appearance_time_per_doc = input_data
        self.engine._EncryptedSearchEngine__count_keyword_appearance()
        assert (
            dict(self.engine._EncryptedSearchEngine__words_appearance_time) == expected
        )

    def test_large_dataset(self):
        """场景5: 大数据量验证（1000文档）"""
        # 构造测试数据
        test_data = {f"doc{i}": {"word": i} for i in range(1000)}
        self.engine._EncryptedSearchEngine__word_appearance_time_per_doc = test_data

        self.engine._EncryptedSearchEngine__count_keyword_appearance()
        # 验证累计结果
        assert self.engine._EncryptedSearchEngine__words_appearance_time["word"] == sum(
            range(1000)
        )
