import pytest
from Crypto.Random import get_random_bytes

from my import EncryptedIndexBuilder


@pytest.fixture
def engine():
    """提供预配置的EncryptedIndexBuilder实例"""
    # 生成符合AES-128要求的有效密钥
    valid_key = get_random_bytes(16)
    # 初始化引擎实例（使用空数据集路径）
    engine = EncryptedIndexBuilder(
        file_key=valid_key, index_key=valid_key, dataset_path="/dev/null", threshold=10
    )
    # 注入初始测试数据到私有属性
    engine.words_appearance_time = {  # type: ignore
        "ai": 15,
        "blockchain": 9,
        "quantum": 20,
        "cybersecurity": 11,
    }
    return engine


def test_threshold_boundary(engine):
    """验证精确边界条件（threshold=10）"""
    engine.threshold = 10
    result = engine._EncryptedIndexBuilder__choose_out_keyword()
    # 验证应包含的项
    assert "ai" in result
    assert "quantum" in result
    assert "cybersecurity" in result
    # 验证排除项
    assert "blockchain" not in result
    # 验证结果数量
    assert len(result) == 3


def test_mixed_frequency(engine):
    """测试动态更新字典后的混合场景"""
    # 更新测试数据
    engine.words_appearance_time.update({"iot": 12, "vr": 5})
    # 将ai的count更新为10
    engine.words_appearance_time.update({"ai": 10})
    engine.threshold = 12
    result = engine._EncryptedIndexBuilder__choose_out_keyword()
    # 验证排序无关的内容匹配，ai 值已更新为10，小于threshold，应该被排除
    assert set(result) == {"quantum"}


@pytest.mark.parametrize(
    "threshold, expected",
    [
        (0, ["ai", "blockchain", "quantum", "cybersecurity"]),  # 所有count>0的项
        (15, ["quantum"]),  # 仅quantum(20) >15
        (20, []),  # 无满足条件的项
    ],
)
def test_various_thresholds(engine, threshold, expected):
    """参数化测试不同阈值场景"""
    engine.threshold = threshold
    assert sorted(engine._EncryptedIndexBuilder__choose_out_keyword()) == sorted(
        expected
    )


def test_zero_count_edge_case(engine):
    """测试包含count=0的特殊情况"""
    # 添加count=0的测试数据
    engine.words_appearance_time["nft"] = 0
    engine.threshold = 0
    result = engine._EncryptedIndexBuilder__choose_out_keyword()
    # 验证包含正常count>0的项
    assert "ai" in result
    assert "quantum" in result
    assert "cybersecurity" in result
    # 验证排除count=0的项
    assert "nft" not in result
