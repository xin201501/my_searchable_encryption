# 新增测试文件
import pandas as pd
from preprocess_finance_corpus import process_news  # 需要将your_module替换为实际模块名

def test_news_processing():
    # 测试数据
    mock_news_data = [
        {
        'title': 'Test News',
        'news': [
            {'paragraph': 'First paragraph'},
            {'paragraph': 'Second paragraph'}
        ]
        },
        {
            'title': 'Another Test News',
            'news': [
                {'paragraph': 'Another first paragraph'},
                {'paragraph': 'Another second paragraph'},
                {'paragraph': 'Another third paragraph'}
            ]
        }
    ]
    
    # 转化为DataFrame
    mock_news_df = pd.DataFrame(mock_news_data)
    
    # 执行测试
    result = process_news(mock_news_df)
    
    # 验证结果
    assert isinstance(result, list)
    assert len(result) == 2
    #验证最后输出
    assert result[0] == 'Test News\n\nFirst paragraph\nSecond paragraph'
    assert result[1] == 'Another Test News\n\nAnother first paragraph\nAnother second paragraph\nAnother third paragraph'

def test_empty_news():
    # 测试空数据情况
    empty_data = {'title': '', 'news': []}
    # 转化为DataFrame
    empty_data_df = pd.DataFrame(empty_data)
    assert len(empty_data_df) == 0
    result = process_news(empty_data_df)
    assert result == []