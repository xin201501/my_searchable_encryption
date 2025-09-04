from pandas import DataFrame


def get_news_data_by_company_name(ticker_symbol: str):
    from defeatbeta_api.data.ticker import Ticker

    ticker = Ticker(ticker_symbol)
    news = ticker.news()
    return news.get_news_list()


def get_all_news_data(count: int | None):
    from defeatbeta_api.client.duckdb_client import DuckDBClient
    from defeatbeta_api.client.hugging_face_client import HuggingFaceClient
    from defeatbeta_api.utils.const import stock_news

    duckdb_client = DuckDBClient()
    huggingface_client = HuggingFaceClient()
    url = huggingface_client.get_url_path(stock_news)
    if count is None:
        sql = f"SELECT * FROM '{url}'"
    else:
        sql = f"SELECT * FROM '{url}' LIMIT {count}"
    result = duckdb_client.query(sql)
    return result


# 将process_item移出为独立函数以避免多进程序列化问题
def process_item(title, content):
    """处理单个新闻项的独立函数（支持多进程序列化）"""
    concatted = "\n".join((item["paragraph"] for item in content))
    return {"title": title, "text": concatted}


def process_news(news_df: DataFrame):
    from concurrent.futures import ProcessPoolExecutor

    title, content = news_df["title"], news_df["news"]
    zip_news = zip(title, content)

    corpus = []

    with ProcessPoolExecutor() as executor:  # 使用进程池代替线程池
        futures = []
        for title, content in zip_news:
            futures.append(executor.submit(process_item, title, content))

        for future in futures:
            corpus.append(future.result())  # 收集处理结果

    return corpus


if __name__ == "__main__":
    news = get_news_data_by_company_name("TSLA")
    # 选择report_date 早于 2025-08-23的数据
    news = news[news["report_date"] < "2025-08-23"]
    corpus = process_news(news)
    print(corpus[0])
