import pytest
from collections import defaultdict
from Crypto.Random import get_random_bytes
from my import EncryptedSearchEngine  # 根据实际路径调整导入


class TestCountWordAppearance:
    @pytest.fixture(autouse=True)
    def setup_engine(self):
        """pytest夹具：初始化被测对象和数据结构"""
        # 生成符合AES-128要求的有效密钥
        valid_key = get_random_bytes(16)
        # 初始化引擎实例（使用空数据集路径）
        self.engine = EncryptedSearchEngine(
            file_key=valid_key,
            index_key=valid_key,
            dataset_path="/dev/null",
            threshold=10,
        )
        yield  # 测试结束后清理资源（如有需要）

    # 参数化测试用例（核心测试逻辑）
    @pytest.mark.parametrize(
        "test_id, docid, text, expected",
        [
            (1, 1, "hello world hello", {"hello": 2, "world": 1}),
            (2, 2, "Hello World", {"hello": 1, "world": 1}),
            (3, 3, "test!test?test...", {"test": 3}),
            (4, 4, "", {}),
            (5, 5, "a-b 123", {"a-b": 1, "123": 1}),
            (6, 6, "重复 重复 重复", {"重复": 3}),
            (7, 7, "a-b-c 123", {"a-b-c": 1, "123": 1}),
            (8, 8, "a-b-c-D 123", {"a-b-c-d": 1, "123": 1}),
        ],
    )
    def test_word_count_scenarios(self, test_id, docid, text, expected):
        """测试用例集合（参数化驱动）"""
        # 执行被测方法
        self.engine._EncryptedSearchEngine__count_word_appearance_per_doc(docid, text)

        # 获取实际结果
        actual = self.engine._EncryptedSearchEngine__word_appearance_time_per_doc[docid]

        # 断言验证
        assert actual == expected, f"测试用例TC{test_id:02d}验证失败"
