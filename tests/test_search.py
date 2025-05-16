import json
import pytest
from encrypt_keyword import symmetric_decryption_for_keyword
from my import EncryptedSearchEngine

# 固定测试密钥（32字节）
TEST_FILE_KEY = b"1234567891234567"  # 替换实际生成的32字节密钥
TEST_INDEX_KEY = b"1234567891234567"  # 替换实际生成的32字节密钥


@pytest.fixture(scope="module")
def test_data():
    """测试数据集"""
    return [
        {
            "title": "Cloud Computing",
            "text": "Cloud computing is the delivery of computing services.",
        },
        {
            "title": "Distributed Systems",
            "text": "Distributed systems use multiple computing nodes.",
        },
        {"title": "Cybersecurity", "text": "Security in computing systems is crucial."},
    ]


@pytest.fixture
def engine(tmp_path, test_data):
    """创建并初始化搜索引擎实例"""
    # 创建临时测试文件
    test_file = tmp_path / "test_dataset.json"
    with open(test_file, "w") as f:
        json.dump(test_data, f)

    # 初始化引擎
    engine = EncryptedSearchEngine(
        file_key=TEST_FILE_KEY,
        index_key=TEST_INDEX_KEY,
        dataset_path=str(test_file),
        threshold=1,
    )
    engine.process_whole_document_set()
    return engine


def test_search_existing_keyword(engine):
    """测试搜索存在的关键词（多结果）"""
    results = engine.search("computing")
    assert len(results) == 3
    assert isinstance(results[0], tuple)
    assert isinstance(results[0][0], bytes)  # 加密词频
    assert isinstance(results[0][1], bytes)  # 加密文档ID
    # 解密文档ID和词频
    result_id_strs = []
    for _, docid_enc in results:
        doc_id = symmetric_decryption_for_keyword(TEST_INDEX_KEY, docid_enc)
        result_id_strs.append(doc_id)
    result_ids_int = list(map(int, result_id_strs))
    assert sorted(result_ids_int) == [0, 1, 2]


def test_search_single_result(tmp_path, test_data):
    """测试搜索唯一匹配的关键词"""
    # 修改测试数据为单个文档
    test_file = tmp_path / "test_dataset.json"
    with open(test_file, "w") as f:
        json.dump([test_data[0]], f)
    engine = EncryptedSearchEngine(
        file_key=TEST_FILE_KEY,
        index_key=TEST_INDEX_KEY,
        dataset_path=str(test_file),
        threshold=1,
    )
    engine.process_whole_document_set()

    results = engine.search("cloud")
    assert len(results) == 1
    # 解密文档ID和词频
    doc_id = symmetric_decryption_for_keyword(TEST_INDEX_KEY, results[0][1])
    assert int(doc_id) == 0


def test_search_non_existing_keyword(engine):
    """测试搜索不存在的关键词"""
    results = engine.search("nonexistent")
    assert len(results) == 0


@pytest.mark.parametrize("keyword", ["cloud", "Cloud", "CLOUD", "cLOuD"])
def test_case_insensitive_search(engine, keyword):
    """参数化测试大小写不敏感"""
    results = engine.search(keyword)
    assert len(results) == 1


def test_empty_keyword_search(engine):
    """测试空关键词搜索"""
    results = engine.search("")
    assert len(results) == 0
