from defeatbeta_api.data.ticker import Ticker
from pandas import DataFrame
from concurrent.futures import ProcessPoolExecutor


def get_news_data(ticker_symbol: str):
    ticker = Ticker(ticker_symbol)
    news = ticker.news()
    return news.get_news_list()


# 将process_item移出为独立函数以避免多进程序列化问题
def process_item(title, content):
    """处理单个新闻项的独立函数（支持多进程序列化）"""
    concatted = ""
    # 跳过最后一项
    for paragraphs in content[:-1]:
        concatted = concatted + paragraphs["paragraph"] + "\n"
    concatted += content[-1]["paragraph"]
    return {"title": title, "text": concatted}


def process_news(news_df: DataFrame):
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
    news = get_news_data("TSLA")
    # 选择report_date 早于 2025-08-23的数据
    news = news[news["report_date"] < "2025-08-23"]
    corpus = process_news(news)
    print(corpus[0])
