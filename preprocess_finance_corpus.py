from defeatbeta_api.data.ticker import Ticker
from pandas import DataFrame


def get_news_data(ticker_symbol: str):
    ticker = Ticker(ticker_symbol)
    news = ticker.news()
    return news.get_news_list()


def process_news(news_df: DataFrame):
    title, content = news_df["title"], news_df["news"]
    zip_news = zip(title, content)
    corpus = []

    for title, content in zip_news:
        print(content)
        concatted = title + "\n\n"
        # 跳过最后一项

        for paragraphs in content[:-1]:
            concatted = concatted + paragraphs["paragraph"] + "\n"
        concatted += content[-1]["paragraph"]

        corpus.append(concatted)

    return corpus


if __name__ == "__main__":
    news = get_news_data("TSLA")
    corpus = process_news(news)
    print(corpus[0])
